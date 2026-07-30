"""General Ledger report business logic."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.gl_ledger_report_repository import GlLedgerReportRepository
from app.schemas.gl_ledger_report import (
    GlAccountLookup,
    GlLedgerAccountSection,
    GlLedgerReportData,
    GlLedgerReportRequest,
    GlLedgerTransactionRow,
    GlWhatsAppContactLookup,
)
from app.utils.phone_extract import extract_pk_mobiles, format_pk_phone_display, pk_phone_for_input
from app.utils.gl_format import dash_gl, format_voucher_no, format_voucher_type

MAX_AC_ID = 99999999


class GlLedgerReportService:
    def __init__(self, db: Session):
        self.repo = GlLedgerReportRepository(db)

    def search_whatsapp_contacts(self, q: str) -> list[GlWhatsAppContactLookup]:
        contacts: list[GlWhatsAppContactLookup] = []
        seen_keys: set[str] = set()

        for row in self.repo.search_whatsapp_contact_rows(q):
            name = str(row.get("name") or "").strip() or "Contact"
            ac_id = row.get("ac_id")
            source = str(row.get("source") or "")
            phones = extract_pk_mobiles(row.get("created_by") or row.get("phone"))
            entity_id = ac_id if ac_id is not None else row.get("cust_id")

            if phones:
                for index, normalized in enumerate(phones):
                    key = f"{normalized}:{name.lower()}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    contacts.append(
                        GlWhatsAppContactLookup(
                            contact_id=f"{source}:{entity_id}:{index}",
                            name=name,
                            phone_display=format_pk_phone_display(normalized),
                            phone_raw=pk_phone_for_input(normalized),
                            ac_id=int(ac_id) if ac_id is not None else None,
                            source=source,
                            has_mobile=True,
                        )
                    )
                    if len(contacts) >= 50:
                        return contacts
                continue

            no_phone_key = f"no-phone:{entity_id}:{name.lower()}"
            if no_phone_key in seen_keys:
                continue
            seen_keys.add(no_phone_key)
            created_by = str(row.get("created_by") or "").strip()
            hint = created_by if created_by and created_by not in {".", ""} else "CREATED_BY empty"
            contacts.append(
                GlWhatsAppContactLookup(
                    contact_id=f"{source}:{entity_id}:none",
                    name=name,
                    phone_display=hint,
                    phone_raw="",
                    ac_id=int(ac_id) if ac_id is not None else None,
                    source=source,
                    has_mobile=False,
                )
            )
            if len(contacts) >= 50:
                return contacts

        return contacts

    def lookup_whatsapp_contact(self, ac_id: int) -> GlWhatsAppContactLookup:
        contacts = self.search_whatsapp_contacts(str(ac_id))
        if not contacts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="not found",
            )
        for contact in contacts:
            if contact.has_mobile and contact.phone_raw:
                return contact
        return contacts[0]

    def search_accounts(self, q: str) -> list[GlAccountLookup]:
        return [
            GlAccountLookup(
                ac_id=int(r["ac_id"]),
                ac_title=str(r["ac_title"] or ""),
                ac_id_display=dash_gl(r["ac_id"]),
            )
            for r in self.repo.search_accounts(q)
        ]

    def lookup_account(self, ac_id: int) -> GlAccountLookup:
        row = self.repo.lookup_account(ac_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account ID not found.")
        return GlAccountLookup(
            ac_id=int(row["ac_id"]),
            ac_title=str(row["ac_title"] or ""),
            ac_id_display=dash_gl(row["ac_id"]),
        )

    def build_report(self, params: GlLedgerReportRequest) -> GlLedgerReportData:
        if params.date_to < params.date_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date range: From date must be on or before To date.",
            )

        start_ac_id = 1 if params.complete_report else params.start_ac_id
        end_ac_id = MAX_AC_ID if params.complete_report else params.end_ac_id

        accounts = self.repo.fetch_accounts(start_ac_id, end_ac_id, params.suppress_zero_bal)
        if not accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accounts found in the selected range.",
            )

        opening_map = self.repo.fetch_opening_totals(start_ac_id, end_ac_id, params.date_from)
        tx_rows = self.repo.fetch_transactions(
            start_ac_id, end_ac_id, params.date_from, params.date_to
        )
        tx_by_account: dict[int, list] = defaultdict(list)
        for row in tx_rows:
            tx_by_account[int(row["ac_id"])].append(row)

        sections: list[GlLedgerAccountSection] = []
        for account in accounts:
            ac_id = int(account["ac_id"])
            obal = float(account.get("obal") or 0)
            opening_parts = opening_map.get(ac_id, {"tdebit": 0.0, "tcredit": 0.0})
            opening_balance = obal + opening_parts["tdebit"] - opening_parts["tcredit"]

            if opening_balance >= 0:
                opening_debit = opening_balance
                opening_credit = 0.0
            else:
                opening_debit = 0.0
                opening_credit = abs(opening_balance)

            running = opening_balance
            account_debit = opening_debit
            account_credit = opening_credit
            transactions: list[GlLedgerTransactionRow] = []

            for row in tx_by_account.get(ac_id, []):
                debit = float(row.get("DEBIT") or 0)
                credit = float(row.get("CREDIT") or 0)
                running += debit - credit
                account_debit += debit
                account_credit += credit
                voucher_date = row.get("VOUCHER_DATE")
                if isinstance(voucher_date, datetime):
                    voucher_date = voucher_date.date()
                ref = row.get("EXTERNAL_ID")
                if ref in (None, ""):
                    ref = row.get("ADCN")
                if ref in (None, ""):
                    ref = row.get("REF_ID")
                transactions.append(
                    GlLedgerTransactionRow(
                        voucher_date=voucher_date,
                        voucher_no=format_voucher_no(row.get("VOUCHER_ID"), row.get("FISCAL")),
                        voucher_type=format_voucher_type(row.get("VOUCHER_ABBR"), row.get("v_mode")),
                        narration=str(row.get("NARRATION") or "").strip(),
                        book_id=int(row["book_id"]) if row.get("book_id") is not None else None,
                        reference=str(ref or "").strip(),
                        debit=debit,
                        credit=credit,
                        balance=running,
                    )
                )

            sections.append(
                GlLedgerAccountSection(
                    ac_id=ac_id,
                    ac_id_display=dash_gl(ac_id),
                    ac_title=str(account.get("ac_title") or ""),
                    opening_balance=opening_balance,
                    opening_debit=opening_debit,
                    opening_credit=opening_credit,
                    transactions=transactions,
                    total_debit=account_debit,
                    total_credit=account_credit,
                    transaction_count=len(transactions),
                )
            )

        date_range = (
            f"From: {params.date_from.strftime('%d/%m/%Y')} "
            f"To: {params.date_to.strftime('%d/%m/%Y')}"
        )
        criteria = f"From: {start_ac_id} To: {end_ac_id} {date_range}"

        return GlLedgerReportData(
            company_name=settings.company_name,
            report_title="Ledger Transaction Listing",
            criteria=criteria,
            date_range=date_range,
            printed_on=datetime.now().strftime("%d/%m/%Y"),
            accounts=sections,
            total_accounts=len(sections),
            page_wise=params.page_wise,
        )
