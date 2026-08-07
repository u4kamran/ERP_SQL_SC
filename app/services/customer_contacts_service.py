"""Customer marketing contact directory — CUST_SMS + saved social/email links."""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.customer_contacts_repository import CustomerContactsRepository
from app.schemas.customer_contacts import (
    ContactLookupResponse,
    CustomerContactListResponse,
    CustomerContactRow,
    CustomerContactStats,
    CustomerMarketingLinks,
    CustomerMarketingLinksUpdate,
)
from app.services.customer_marketing_store import contact_key_for_sms, get_links, load_all, save_links
from app.services.email_discovery_service import discover_profiles_by_email, is_valid_email
from app.services.platform_cards_service import build_platform_cards
from app.services.social_discovery_service import build_social_discovery_links, normalize_lookup_phone
from app.utils.gl_format import dash_gl
from app.utils.phone_extract import extract_pk_mobiles, format_pk_phone_display, pk_phone_for_input

_EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_SOCIAL_KEYS = ("facebook", "instagram", "whatsapp", "tiktok", "youtube", "website")


class CustomerContactsService:
    def __init__(self, db: Session):
        self.repo = CustomerContactsRepository(db)
        self._gl_phone_index: dict[str, dict] | None = None

    def list_contacts(
        self,
        *,
        q: str = "",
        page: int = 1,
        page_size: int = 50,
        only_with_phone: bool = False,
        only_with_email: bool = False,
        only_with_social: bool = False,
        only_missing: bool = False,
    ) -> CustomerContactListResponse:
        page = max(1, page)
        page_size = min(max(1, page_size), 200)

        marketing = load_all()
        all_rows = self._build_all_rows(q=q, marketing=marketing)
        filtered = self._apply_filters(
            all_rows,
            q=q,
            only_with_phone=only_with_phone,
            only_with_email=only_with_email,
            only_with_social=only_with_social,
            only_missing=only_missing,
        )

        total = len(filtered)
        start = (page - 1) * page_size
        page_items = filtered[start : start + page_size]

        return CustomerContactListResponse(
            items=page_items,
            total=total,
            page=page,
            page_size=page_size,
            with_phone=sum(1 for r in all_rows if r.has_phone),
            with_email=sum(1 for r in all_rows if r.has_email),
            with_social=sum(1 for r in all_rows if r.has_social),
        )

    def get_contact(self, cust_sms_id: int) -> CustomerContactRow:
        row = self.repo.fetch_cust_sms_by_id(cust_sms_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in CUST_SMS.")
        marketing = load_all()
        built = self._build_row(row, marketing)
        if not built:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
        return built

    def lookup_contact(self, *, phone: str = "", email: str = "") -> ContactLookupResponse:
        phone = (phone or "").strip()
        email = (email or "").strip().lower()

        if not phone and not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter a mobile number or email to search.",
            )
        if phone and email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search by mobile OR email, not both at once.",
            )

        marketing = load_all()
        gl_index = self._get_gl_phone_index()
        contacts: list[CustomerContactRow] = []

        if phone:
            normalized, display, phone_raw = normalize_lookup_phone(phone)
            if not phone_raw and len(re.sub(r"\D", "", phone)) < 10:
                return ContactLookupResponse(
                    found=False,
                    lookup_type="phone",
                    query=phone,
                    message="Invalid mobile number. Use Pakistan format e.g. 0300 1234567.",
                    social_links=build_social_discovery_links(),
                )

            core = normalized[-10:] if normalized else re.sub(r"\D", "", phone)[-10:]
            sms_rows = self.repo.fetch_cust_sms_by_phone(core)
            for row in sms_rows:
                built = self._build_row(row, marketing, gl_index=gl_index)
                if built and self._phone_matches(built, core):
                    contacts.append(built)

            # De-duplicate by cust_sms_id
            seen: set[int] = set()
            unique: list[CustomerContactRow] = []
            for c in contacts:
                if c.cust_sms_id in seen:
                    continue
                seen.add(c.cust_sms_id)
                unique.append(c)
            contacts = unique

            primary = contacts[0] if contacts else None
            social_links = build_social_discovery_links(
                name=primary.name if primary else "",
                phone_display=primary.phone_display if primary else display,
                phone_raw=primary.phone_raw if primary else phone_raw,
                email=primary.email_display if primary else "",
            )
            discovered: list = []
            if primary and primary.email_display:
                discovered = discover_profiles_by_email(primary.email_display)
            return ContactLookupResponse(
                found=bool(contacts),
                lookup_type="phone",
                query=phone,
                match_count=len(contacts),
                contacts=contacts,
                social_links=social_links,
                discovered_profiles=discovered,
                platform_cards=build_platform_cards(primary, discovered, social_links),
                message=(
                    f"Found {len(contacts)} customer(s) in CUST_SMS for this mobile."
                    if contacts
                    else "No customer found in CUST_SMS for this mobile. Use social discovery links below."
                ),
            )

        # Email lookup
        if not is_valid_email(email):
            return ContactLookupResponse(
                found=False,
                lookup_type="email",
                query=email,
                message="Invalid email format. Example: customer@gmail.com",
                help_note="Enter a valid email address to search social media.",
                social_links=[],
                discovered_profiles=[],
            )

        email_rows = self._find_by_email(email, marketing, gl_index)
        discovered = discover_profiles_by_email(email)
        primary = email_rows[0] if email_rows else None
        social_links = build_social_discovery_links(
            name=primary.name if primary else "",
            phone_display=primary.phone_display if primary else "",
            phone_raw=primary.phone_raw if primary else "",
            email=email,
        )

        if email_rows:
            msg = f"Found {len(email_rows)} customer(s) in system with this email."
        elif discovered:
            msg = f"Email not in CUST_SMS, but found {len(discovered)} possible public profile(s). Verify and save below."
        else:
            msg = "Email not saved in system yet. Use the search links below to find social accounts, then save them."

        return ContactLookupResponse(
            found=bool(email_rows) or bool(discovered),
            lookup_type="email",
            query=email,
            match_count=len(email_rows),
            contacts=email_rows,
            social_links=social_links,
            discovered_profiles=discovered,
            platform_cards=build_platform_cards(primary, discovered, social_links),
            message=msg,
            help_note=(
                "CUST_SMS stores mobile numbers only. Email and social links are saved when you add them. "
                "Facebook/Instagram do not allow automatic search — use the links below to find profiles publicly."
            ),
        )

    def stats(self) -> CustomerContactStats:
        marketing = load_all()
        rows = self._build_all_rows(q="", marketing=marketing)
        return CustomerContactStats(
            total_accounts=len(rows),
            with_phone=sum(1 for r in rows if r.has_phone),
            with_email=sum(1 for r in rows if r.has_email),
            with_social=sum(1 for r in rows if r.has_social),
            missing_all=sum(1 for r in rows if not r.has_phone and not r.has_email and not r.has_social),
            gl_linked=sum(1 for r in rows if r.gl_linked),
        )

    def update_marketing_links(
        self, cust_sms_id: int, data: CustomerMarketingLinksUpdate
    ) -> CustomerContactRow:
        row = self.repo.fetch_cust_sms_by_id(cust_sms_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in CUST_SMS.")

        key = contact_key_for_sms(cust_sms_id)
        saved = save_links(key, CustomerMarketingLinks(**data.model_dump()))
        marketing = load_all()
        built = self._build_row(row, marketing, override_links=saved)
        if not built:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
        return built

    def export_csv(
        self,
        *,
        q: str = "",
        only_with_phone: bool = False,
        only_with_email: bool = False,
        only_with_social: bool = False,
    ) -> str:
        marketing = load_all()
        rows = self._build_all_rows(q=q, marketing=marketing)
        filtered = self._apply_filters(
            rows,
            q=q,
            only_with_phone=only_with_phone,
            only_with_email=only_with_email,
            only_with_social=only_with_social,
            only_missing=False,
        )

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "SMS_ID",
                "AC_ID",
                "Customer Name",
                "Phone",
                "Alt Phone",
                "Address",
                "Added",
                "Email",
                "Facebook",
                "Instagram",
                "WhatsApp",
                "TikTok",
                "YouTube",
                "Website",
                "Notes",
                "GL Balance",
            ]
        )
        for item in filtered:
            writer.writerow(
                [
                    item.cust_sms_id,
                    item.ac_id_display,
                    item.name,
                    item.phone_display,
                    item.phone_alt_display,
                    item.address,
                    item.added_at,
                    item.email_display,
                    item.facebook,
                    item.instagram,
                    item.whatsapp,
                    item.tiktok,
                    item.youtube,
                    item.website,
                    item.notes,
                    item.current_balance if item.current_balance is not None else "",
                ]
            )
        return buffer.getvalue()

    def _build_all_rows(self, *, q: str, marketing: dict[str, CustomerMarketingLinks]) -> list[CustomerContactRow]:
        sms_rows = self.repo.fetch_cust_sms_rows(q=q)
        gl_index = self._get_gl_phone_index()
        built: list[CustomerContactRow] = []
        for row in sms_rows:
            item = self._build_row(row, marketing, gl_index=gl_index)
            if item:
                built.append(item)
        return built

    def _get_gl_phone_index(self) -> dict[str, dict]:
        if self._gl_phone_index is not None:
            return self._gl_phone_index

        index: dict[str, dict] = {}
        for row in self.repo.fetch_gl_phone_index_rows():
            phones = extract_pk_mobiles(
                row.get("created_by"),
                row.get("cust_phone"),
                row.get("cust_contact"),
                row.get("vend_phone"),
                row.get("vend_contact"),
            )
            payload = {
                "ac_id": int(row["ac_id"]),
                "name": str(row.get("name") or "").strip(),
                "cbal": float(row["cbal"]) if row.get("cbal") is not None else None,
            }
            for phone in phones:
                index.setdefault(phone, payload)
        self._gl_phone_index = index
        return index

    def _build_row(
        self,
        row: dict,
        marketing: dict[str, CustomerMarketingLinks],
        *,
        gl_index: dict[str, dict] | None = None,
        override_links: CustomerMarketingLinks | None = None,
    ) -> CustomerContactRow | None:
        cust_sms_id = int(row["CUST_ID"])
        key = contact_key_for_sms(cust_sms_id)
        links = override_links or marketing.get(key, CustomerMarketingLinks())

        phones = extract_pk_mobiles(row.get("mobile_no"), row.get("mobile_no_tmp"))
        alt_phones = extract_pk_mobiles(row.get("mobile_no_tmp"))
        normalized = phones[0] if phones else ""
        alt_normalized = ""
        for candidate in alt_phones:
            if candidate != normalized:
                alt_normalized = candidate
                break

        phone_display = format_pk_phone_display(normalized) if normalized else ""
        phone_raw = pk_phone_for_input(normalized) if normalized else ""
        phone_alt_display = format_pk_phone_display(alt_normalized) if alt_normalized else ""

        gl_index = gl_index or self._get_gl_phone_index()
        gl_match = gl_index.get(normalized) or gl_index.get(alt_normalized)
        ac_id = int(gl_match["ac_id"]) if gl_match else None
        ac_id_display = dash_gl(ac_id) if ac_id else ""
        current_balance = gl_match.get("cbal") if gl_match else None

        name = str(row.get("cust_name") or "").strip() or "Unknown"
        address = str(row.get("cust_address") or "").strip()
        added_at = ""
        if row.get("ADDED_DATETIME"):
            dt = row["ADDED_DATETIME"]
            if isinstance(dt, datetime):
                added_at = dt.strftime("%Y-%m-%d %H:%M")

        marketing_email = (links.email or "").strip()
        email_display = marketing_email

        facebook = links.facebook.strip()
        instagram = links.instagram.strip()
        whatsapp = links.whatsapp.strip() or (f"https://wa.me/92{phone_raw}" if phone_raw else "")
        tiktok = links.tiktok.strip()
        youtube = links.youtube.strip()
        website = links.website.strip()
        notes = links.notes.strip()

        has_social = any(
            self._is_url_or_handle(getattr(links, field))
            for field in _SOCIAL_KEYS
            if field != "whatsapp"
        ) or bool(phone_raw)

        return CustomerContactRow(
            contact_key=key,
            cust_sms_id=cust_sms_id,
            ac_id=ac_id,
            ac_id_display=ac_id_display,
            name=name,
            party_type="customer",
            phone_display=phone_display,
            phone_raw=phone_raw,
            phone_alt_display=phone_alt_display,
            contact_person=name,
            address=address,
            added_at=added_at,
            erp_email="",
            marketing_email=marketing_email,
            email_display=email_display,
            facebook=facebook,
            instagram=instagram,
            whatsapp=whatsapp,
            tiktok=tiktok,
            youtube=youtube,
            website=website,
            notes=notes,
            current_balance=current_balance,
            has_phone=bool(phone_raw),
            has_email=bool(email_display),
            has_social=has_social,
            gl_linked=ac_id is not None,
        )

    def _apply_filters(
        self,
        rows: list[CustomerContactRow],
        *,
        q: str,
        only_with_phone: bool,
        only_with_email: bool,
        only_with_social: bool,
        only_missing: bool,
    ) -> list[CustomerContactRow]:
        q = (q or "").strip().lower()
        result: list[CustomerContactRow] = []
        for row in rows:
            if q and not self._matches_query(row, q):
                continue
            if only_with_phone and not row.has_phone:
                continue
            if only_with_email and not row.has_email:
                continue
            if only_with_social and not row.has_social:
                continue
            if only_missing and (row.has_phone or row.has_email or row.has_social):
                continue
            result.append(row)
        return result

    def _find_by_email(
        self,
        email: str,
        marketing: dict[str, CustomerMarketingLinks],
        gl_index: dict[str, dict],
    ) -> list[CustomerContactRow]:
        email = email.strip().lower()
        if not email or "@" not in email:
            return []

        matched_ids: set[int] = set()
        for key, links in marketing.items():
            if not key.startswith("sms:"):
                continue
            saved = (links.email or "").strip().lower()
            if saved == email or (saved and email in saved):
                try:
                    matched_ids.add(int(key.split(":", 1)[1]))
                except ValueError:
                    continue

        results: list[CustomerContactRow] = []
        for cust_id in matched_ids:
            row = self.repo.fetch_cust_sms_by_id(cust_id)
            if row:
                built = self._build_row(row, marketing, gl_index=gl_index)
                if built:
                    results.append(built)

        if results:
            return results

        # Fallback: scan all contacts for partial email match in saved data
        for row in self.repo.fetch_cust_sms_rows(q=email):
            built = self._build_row(row, marketing, gl_index=gl_index)
            if built and email in (built.email_display or "").lower():
                results.append(built)
        return results

    @staticmethod
    def _phone_matches(row: CustomerContactRow, core: str) -> bool:
        digits = re.sub(r"\D", "", core or "")
        if len(digits) > 10:
            digits = digits[-10:]
        for field in (row.phone_display, row.phone_alt_display, row.phone_raw):
            if digits and digits in re.sub(r"\D", "", field or ""):
                return True
        return False

    def _matches_query(self, row: CustomerContactRow, q: str) -> bool:
        q_digits = re.sub(r"\D", "", q)
        if q_digits and len(q_digits) >= 7:
            row_digits = re.sub(r"\D", "", " ".join([row.phone_display, row.phone_alt_display, row.phone_raw]))
            if q_digits in row_digits or q_digits[-10:] in row_digits:
                return True

        if "@" in q:
            if q in (row.email_display or "").lower():
                return True

        haystack = " ".join(
            [
                str(row.cust_sms_id),
                str(row.ac_id or ""),
                row.ac_id_display,
                row.name,
                row.phone_display,
                row.phone_alt_display,
                row.address,
                row.email_display,
                row.facebook,
                row.instagram,
                row.whatsapp,
                row.website,
                row.notes,
            ]
        ).lower()
        return q in haystack

    @staticmethod
    def _is_url_or_handle(value: str) -> bool:
        return len((value or "").strip()) >= 3
