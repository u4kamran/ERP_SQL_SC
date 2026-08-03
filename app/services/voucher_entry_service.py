"""Voucher entry business logic — mirrors VB6 VoucherM CmdSave/CmdDelete."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.voucher_entry_repository import VoucherEntryRepository, _vget
from app.schemas.voucher_entry import (
    VoucherAccountLookup,
    VoucherBookOut,
    VoucherConfigOut,
    VoucherDeleteResponse,
    VoucherHeaderOut,
    VoucherLineIn,
    VoucherLineOut,
    VoucherNarrationLookup,
    VoucherNextNumberOut,
    VoucherSaveRequest,
    VoucherSaveResponse,
)
from app.utils.gl_format import format_voucher_no, format_voucher_type


def _money(value) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _nil(text: str) -> str:
    cleaned = (text or "").strip()
    return cleaned if cleaned else "Nil"


class VoucherEntryService:
    def __init__(self, db: Session, *, username: str, legacy_uid: Optional[int] = None, is_admin: bool = False):
        self.db = db
        self.repo = VoucherEntryRepository(db)
        self.username = username
        self.legacy_uid = legacy_uid or settings.voucher_legacy_uid
        self.is_admin = is_admin

    def get_config(self) -> VoucherConfigOut:
        setup = self.repo.get_gsetup()
        max_entries = int(_vget(setup, "max_trans", default=2000) or 2000)
        fiscal_start = _vget(setup, "fiscal_start")
        fiscal_end = _vget(setup, "fiscal_end")
        if fiscal_start and not isinstance(fiscal_start, date):
            fiscal_start = date.fromisoformat(str(fiscal_start)[:10])
        if fiscal_end and not isinstance(fiscal_end, date):
            fiscal_end = date.fromisoformat(str(fiscal_end)[:10])
        return VoucherConfigOut(
            max_entries=max_entries,
            fiscal_start=fiscal_start,
            fiscal_end=fiscal_end,
            legacy_uid=self.legacy_uid,
        )

    def list_books(self) -> List[VoucherBookOut]:
        rows = self.repo.list_books(self.legacy_uid, admin_bypass=self.is_admin)
        results = []
        for row in rows:
            if int(_vget(row, "ed_status", default=0) or 0) == 1:
                continue
            ac_id = _vget(row, "ac_id")
            balance = None
            if ac_id:
                acct = self.repo.get_account(int(ac_id))
                if acct:
                    balance = _money(_vget(acct, "cbal"))
            results.append(
                VoucherBookOut(
                    book_id=int(_vget(row, "book_id")),
                    book_title=str(_vget(row, "book_title", default="")),
                    voucher_abbr=str(_vget(row, "voucher_abbr", default="")),
                    book_type=int(_vget(row, "book_type", default=2)),
                    ac_id=int(ac_id) if ac_id is not None else None,
                    v_numbering=int(_vget(row, "v_numbering", default=1)),
                    v_combination=int(_vget(row, "v_combination", default=1)),
                    bb_od=int(_vget(row, "bb_od")) if _vget(row, "bb_od") is not None else None,
                    title_jv=str(_vget(row, "title_JV", "title_jv", default="") or ""),
                    book_balance=balance,
                )
            )
        return results

    def get_book(self, book_id: int) -> VoucherBookOut:
        row = self.repo.get_book(book_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")
        if not self.is_admin and not self.repo.user_has_book(self.legacy_uid, book_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to book denied.")
        if int(_vget(row, "ed_status", default=0) or 0) == 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is temporarily stopped.")
        books = self.list_books()
        for book in books:
            if book.book_id == book_id:
                return book
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to book denied.")

    def search_accounts(self, q: str) -> List[VoucherAccountLookup]:
        rows = self.repo.search_accounts(q)
        return [
            VoucherAccountLookup(
                ac_id=int(_vget(r, "ac_id")),
                ac_title=str(_vget(r, "ac_title", default="")),
                cbal=_money(_vget(r, "cbal")),
            )
            for r in rows
        ]

    def get_account(self, ac_id: int) -> VoucherAccountLookup:
        row = self.repo.get_account(ac_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
        if int(_vget(row, "ac_level", default=0) or 0) != 4:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account must be level 4.")
        if int(_vget(row, "ed_status", default=0) or 0) == 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is disabled.")
        return VoucherAccountLookup(
            ac_id=int(_vget(row, "ac_id")),
            ac_title=str(_vget(row, "ac_title", default="")),
            cbal=_money(_vget(row, "cbal")),
        )

    def search_narrations(self, q: str, ac_id: Optional[int] = None) -> List[VoucherNarrationLookup]:
        results: List[VoucherNarrationLookup] = []
        for row in self.repo.search_narration_templates(q):
            nar_id = _vget(row, "nar_id")
            title = str(_vget(row, "nar_title", default=""))
            results.append(VoucherNarrationLookup(id=f"tpl-{nar_id}", narration=title, source="template"))
        if ac_id:
            for row in self.repo.search_narration_history(ac_id, q):
                title = str(_vget(row, "narration", default=""))
                results.append(
                    VoucherNarrationLookup(id=f"hist-{hash(title)}", narration=title, source="history")
                )
        return results[:50]

    def last_narration(self, ac_id: int) -> Optional[str]:
        return self.repo.last_narration_for_account(ac_id)

    def next_number(self, book_id: int, v_mode: int, fiscal: int) -> VoucherNextNumberOut:
        book = self.get_book(book_id)
        fiscal_val = self._resolve_fiscal(book, fiscal)
        next_id = self.repo.next_voucher_id(book_id, v_mode, fiscal_val)
        display = format_voucher_no(next_id, fiscal_val if book.v_numbering == 2 else 0)
        if book.voucher_abbr:
            display = f"{format_voucher_type(book.voucher_abbr, v_mode)} {display}".strip()
        return VoucherNextNumberOut(voucher_id=next_id, voucher_display=display)

    def load_by_key(self, book_id: int, voucher_id: int, v_mode: int, fiscal: int) -> VoucherHeaderOut:
        book = self.get_book(book_id)
        fiscal_val = self._resolve_fiscal(book, fiscal)
        v_mode_val = self._resolve_v_mode(book, v_mode)
        header = self.repo.get_header_by_key(voucher_id, book_id, v_mode_val, fiscal_val)
        if not header and book.book_type != 2:
            for alt_mode in (2, 3):
                if alt_mode == v_mode_val:
                    continue
                header = self.repo.get_header_by_key(voucher_id, book_id, alt_mode, fiscal_val)
                if header:
                    break
        if not header:
            candidates = self.repo.list_headers_by_book_voucher(voucher_id, book_id)
            if candidates:
                fiscals = sorted({int(_vget(row, "fiscal", default=0) or 0) for row in candidates})
                modes = sorted({int(_vget(row, "v_mode", default=1) or 1) for row in candidates})
                mode_labels = {1: "JV", 2: "Payment", 3: "Receipt"}
                mode_text = ", ".join(mode_labels.get(m, str(m)) for m in modes)
                fiscal_text = ", ".join(str(f).zfill(2) for f in fiscals if f)
                detail = "Voucher not found for the selected month/mode."
                if book.v_numbering == 2 and fiscal_text:
                    detail += f" Try fiscal month {fiscal_text}."
                if book.book_type != 2 and len(modes) > 1:
                    detail += f" Available as {mode_text}."
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voucher not found.")
        return self._header_response(header, book)

    def load_by_serial(self, serial_no: float) -> VoucherHeaderOut:
        header = self.repo.get_header_by_serial(serial_no)
        if not header:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voucher not found.")
        book_id = int(_vget(header, "book_id"))
        book = self.get_book(book_id)
        return self._header_response(header, book)

    def repeat_last(self, book_id: int) -> List[VoucherLineOut]:
        self.get_book(book_id)
        lines = self.repo.get_last_voucher_lines(book_id)
        out = []
        for idx, row in enumerate(lines, start=1):
            ac_id = int(_vget(row, "ac_id"))
            acct = self.repo.get_account(ac_id)
            out.append(
                VoucherLineOut(
                    serial_order=idx,
                    ac_id=ac_id,
                    ac_title=str(_vget(acct or {}, "ac_title", default="")),
                    narration=str(_vget(row, "narration", default="")),
                    debit=_money(_vget(row, "debit")),
                    credit=_money(_vget(row, "credit")),
                    reference=str(_vget(row, "reference", default="") or ""),
                )
            )
        return out

    def save(self, payload: VoucherSaveRequest, *, editing: bool = False) -> VoucherSaveResponse:
        book = self.get_book(payload.book_id)
        config = self.get_config()
        fiscal_val = self._resolve_fiscal(book, payload.fiscal)
        v_mode = self._resolve_v_mode(book, payload.v_mode)

        lines = self._normalize_lines(payload.lines, v_mode)
        self._validate_save(payload, book, config, lines, v_mode, fiscal_val)

        total_debit = sum(_money(l.debit) for l in lines)
        total_credit = sum(_money(l.credit) for l in lines)
        remarks = _nil(payload.remarks)

        is_new = not editing
        serial_no = payload.serial_no
        voucher_id = payload.voucher_id

        try:
            if editing:
                if serial_no is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="serial_no required for edit.")
                header = self.repo.get_header_by_serial(float(serial_no))
                if not header:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voucher not found.")
                if int(_vget(header, "sys_status", default=0) or 0) == 1:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voucher is posted.")
                voucher_id = int(_vget(header, "voucher_id"))
                self._check_book_balance(book, header, lines, serial_no=float(serial_no))
                self.repo.reverse_balances_for_serial(float(serial_no))
                self.repo.delete_lines(float(serial_no))
            else:
                voucher_id = self.repo.next_voucher_id(payload.book_id, v_mode, fiscal_val)
                serial_no = self.repo.allocate_serial_no(self.legacy_uid)
                self._check_book_balance(book, None, lines, serial_no=None)

            self.repo.insert_header(
                serial_no=float(serial_no),
                voucher_id=int(voucher_id),
                book_id=payload.book_id,
                v_mode=v_mode,
                fiscal=fiscal_val,
                voucher_date=payload.voucher_date,
                remarks=remarks,
                amount=total_debit,
                book_type=book.book_type,
                line_count=len(lines),
                username=self.username,
                is_new=is_new,
            )

            for idx, line in enumerate(lines, start=1):
                narration = _nil(line.narration)
                self.repo.insert_line(
                    serial_no=float(serial_no),
                    voucher_id=int(voucher_id),
                    book_id=payload.book_id,
                    serial_order=idx,
                    voucher_date=payload.voucher_date,
                    ac_id=line.ac_id,
                    narration=narration,
                    debit=_money(line.debit),
                    credit=_money(line.credit),
                    reference=(line.reference or "").strip(),
                )
                self.repo.apply_balance(line.ac_id, _money(line.debit), _money(line.credit))

            self.db.commit()
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Voucher save failed: {exc}",
            ) from exc

        display_fiscal = fiscal_val if book.v_numbering == 2 else 0
        voucher_display = format_voucher_no(int(voucher_id), display_fiscal)
        if book.voucher_abbr:
            voucher_display = f"{format_voucher_type(book.voucher_abbr, v_mode)} {voucher_display}".strip()

        msg = "Voucher edited." if editing else "New voucher added."
        return VoucherSaveResponse(
            message=f"{msg} No. {voucher_display}",
            serial_no=float(serial_no),
            voucher_id=int(voucher_id),
            voucher_display=voucher_display,
        )

    def delete(self, serial_no: float) -> VoucherDeleteResponse:
        header = self.repo.get_header_by_serial(serial_no)
        if not header:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voucher not found.")
        if int(_vget(header, "sys_status", default=0) or 0) == 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voucher is posted.")
        book_id = int(_vget(header, "book_id"))
        self.get_book(book_id)
        voucher_id = int(_vget(header, "voucher_id"))

        try:
            self.repo.reverse_balances_for_serial(serial_no)
            self.repo.delete_lines(serial_no)
            self.repo.delete_header(serial_no)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Voucher delete failed: {exc}",
            ) from exc

        return VoucherDeleteResponse(message=f"Voucher deleted. No. {voucher_id}", voucher_id=voucher_id)

    def _header_response(self, header: dict, book: VoucherBookOut) -> VoucherHeaderOut:
        if int(_vget(header, "sys_status", default=0) or 0) == 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voucher is posted.")
        serial_no = float(_vget(header, "serial_no"))
        raw_lines = self.repo.get_lines(serial_no)
        lines = []
        for row in raw_lines:
            ac_id = int(_vget(row, "ac_id"))
            acct = self.repo.get_account(ac_id)
            lines.append(
                VoucherLineOut(
                    serial_order=int(_vget(row, "serial_order", default=0)),
                    ac_id=ac_id,
                    ac_title=str(_vget(acct or {}, "ac_title", default="")),
                    narration=str(_vget(row, "narration", default="")),
                    debit=_money(_vget(row, "debit")),
                    credit=_money(_vget(row, "credit")),
                    reference=str(_vget(row, "reference", default="") or ""),
                )
            )
        vdate = _vget(header, "voucher_date")
        if vdate and not isinstance(vdate, date):
            vdate = date.fromisoformat(str(vdate)[:10])
        return VoucherHeaderOut(
            serial_no=serial_no,
            voucher_id=int(_vget(header, "voucher_id")),
            book_id=int(_vget(header, "book_id")),
            v_mode=int(_vget(header, "v_mode")),
            fiscal=int(_vget(header, "fiscal", default=0) or 0),
            voucher_date=vdate,
            remarks=str(_vget(header, "remarks", default="") or ""),
            amount=_money(_vget(header, "Amount", "amount")),
            book_type=int(_vget(header, "book_type", default=book.book_type)),
            sys_status=int(_vget(header, "sys_status", default=0) or 0),
            voucher_abbr=book.voucher_abbr,
            book_title=book.book_title,
            lines=lines,
        )

    def _resolve_fiscal(self, book: VoucherBookOut, fiscal: int) -> int:
        if book.v_numbering == 1:
            return 0
        if fiscal < 1 or fiscal > 12:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Month/Fiscal must be 1-12.")
        return fiscal

    def _resolve_v_mode(self, book: VoucherBookOut, v_mode: int) -> int:
        if book.book_type == 2:
            return 1
        if v_mode not in (2, 3):
            return 2 if book.v_combination == 2 else v_mode
        return v_mode

    def _normalize_lines(self, lines: List[VoucherLineIn], v_mode: int) -> List[VoucherLineIn]:
        normalized = []
        for line in lines:
            debit = _money(line.debit)
            credit = _money(line.credit)
            if v_mode == 2:
                credit = 0.0
            elif v_mode == 3:
                debit = 0.0
            if debit == 0 and credit == 0:
                continue
            self.get_account(line.ac_id)
            normalized.append(
                VoucherLineIn(
                    ac_id=line.ac_id,
                    narration=line.narration,
                    debit=debit,
                    credit=credit,
                    reference=line.reference,
                )
            )
        return normalized

    def _validate_save(
        self,
        payload: VoucherSaveRequest,
        book: VoucherBookOut,
        config: VoucherConfigOut,
        lines: List[VoucherLineIn],
        v_mode: int,
        fiscal_val: int,
    ) -> None:
        if not lines:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one transaction line required.")
        if len(lines) > config.max_entries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {config.max_entries} lines allowed.",
            )

        total_debit = sum(_money(l.debit) for l in lines)
        total_credit = sum(_money(l.credit) for l in lines)
        if total_debit != total_credit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Voucher is not balanced. Debit - Credit = {total_debit - total_credit:.2f}",
            )
        if total_debit == 0 and total_credit == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zero amount voucher not allowed.")

        if config.fiscal_start and payload.voucher_date < config.fiscal_start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voucher date out of fiscal range.")
        if config.fiscal_end and payload.voucher_date > config.fiscal_end:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voucher date out of fiscal range.")

        if book.v_numbering == 2 and payload.voucher_date.month != fiscal_val:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected Month/Fiscal does not match voucher date.",
            )

        for line in lines:
            if _money(line.debit) < 0 or _money(line.credit) < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Negative amounts not allowed.")
            if _money(line.debit) > 0 and _money(line.credit) > 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Line cannot have both debit and credit.")

    def _check_book_balance(
        self,
        book: VoucherBookOut,
        existing_header: Optional[dict],
        lines: List[VoucherLineIn],
        *,
        serial_no: Optional[float],
    ) -> None:
        if book.book_type not in (0, 1) or not book.ac_id:
            return
        acct = self.repo.get_account(book.ac_id)
        if not acct:
            return
        opening = _money(_vget(acct, "cbal"))

        old_effect = 0.0
        if serial_no is not None:
            for row in self.repo.get_lines(serial_no):
                if int(_vget(row, "ac_id")) == book.ac_id:
                    old_effect += _money(_vget(row, "debit")) - _money(_vget(row, "credit"))

        current_effect = 0.0
        for line in lines:
            if line.ac_id == book.ac_id:
                current_effect += _money(line.debit) - _money(line.credit)

        projected = opening - old_effect + current_effect
        if projected < 0:
            if book.book_type == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cash balance would be negative: {projected:.2f}",
                )
            if book.book_type == 0 and not book.bb_od:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Bank balance would be negative: {projected:.2f}",
                )
