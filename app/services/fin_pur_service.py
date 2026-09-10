"""Purchase Receipt business logic — mirrors VB6 Fin_PurM / Fin_PurD / Fin_PurDed."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.fin_pur_repository import FinPurRepository, _vget
from app.schemas.fin_pur import (
    FinPurConfigOut,
    FinPurDeleteResponse,
    FinPurDocumentOut,
    FinPurHeaderCharges,
    FinPurItemOut,
    FinPurLineIn,
    FinPurLineOut,
    FinPurLookupRow,
    FinPurSaveRequest,
    FinPurSaveResponse,
    FinPurSupplierOut,
    FinPurTotalsOut,
)


def _money(value) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _as_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


class FinPurService:
    DOC_TYPE_ID = 2
    # GLModule2 for Shafique Departmental Store
    STAX_TYPE_MODE = 1
    MV_MODE = 1
    M_BOOK_TYPE = 2
    M_FISCAL = 0
    MAX_ENTRIES = 500

    def __init__(
        self,
        db: Session,
        *,
        username: str,
        legacy_uid: Optional[int] = None,
        is_admin: bool = False,
        is_sa: bool = False,
    ):
        self.db = db
        self.repo = FinPurRepository(db)
        self.username = username
        self.legacy_uid = legacy_uid or settings.voucher_legacy_uid
        self.is_admin = is_admin
        self.is_sa = is_sa

    # ----- config / lookups -----

    def get_config(self) -> FinPurConfigOut:
        setup = self.repo.get_gsetup()
        doc = self.repo.get_doc_type(self.DOC_TYPE_ID) or {}
        gl_setup = self.repo.get_doc_gl_setup(self.DOC_TYPE_ID) or {}
        book_id = int(_vget(doc, "doc_book_id", default=102) or 102)
        book = self.repo.get_book(book_id)
        book_ok = True
        book_message = ""
        if not book:
            book_ok = False
            book_message = "Book not found or for Use of Other Modules, please enter another ..."
        else:
            ed = int(_vget(book, "ed_status", default=0) or 0)
            if ed == 1:
                book_ok = False
                book_message = "Book is temporarily stoped ..."
            elif not self.is_admin and not self.repo.user_has_book(self.legacy_uid, book_id):
                book_ok = False
                book_message = "Permission to Book is denied, Consult Administrator ... "

        fiscal_start = _as_date(_vget(setup, "fiscal_start"))
        fiscal_end = _as_date(_vget(setup, "Fiscal_end", "fiscal_end"))

        return FinPurConfigOut(
            doc_type_id=self.DOC_TYPE_ID,
            doc_abbr=str(_vget(doc, "doc_abbr", default="PUR") or "PUR"),
            book_id=book_id,
            fiscal=self.M_FISCAL,
            max_entries=self.MAX_ENTRIES,
            stax_type_mode=self.STAX_TYPE_MODE,
            fiscal_start=fiscal_start,
            fiscal_end=fiscal_end,
            company_name=settings.company_name,
            book_ok=book_ok,
            book_message=book_message,
            reg_stax_rate=_money(_vget(gl_setup, "reg_page")),
            unreg_stax_rate=_money(_vget(gl_setup, "unreg_page")),
            legacy_uid=self.legacy_uid,
            is_sa=self.is_sa,
        )

    def get_supplier(self, supplier_id: int) -> FinPurSupplierOut:
        if not supplier_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Supplier ID.")
        rs = self.repo.get_supplier(supplier_id)
        if not rs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier ID not found... ",
            )
        title = str(_vget(rs, "Vendor_Title", "vendor_title", default="") or "")
        if not title:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Supplier ID.")

        tag_1 = int(_vget(rs, "tag_1", "TAG_1", default=0) or 0)
        cfg = self.get_config()
        # Fin_PurM.TxtID_Validate: tag_1=0 Registered, tag_1=1 Un-Registered, else Other
        if tag_1 == 0:
            registration = "Registered"
            rate = cfg.reg_stax_rate if cfg.stax_type_mode == 1 else 0.0
        elif tag_1 == 1:
            registration = "Un-Registered"
            rate = cfg.unreg_stax_rate if cfg.stax_type_mode == 1 else 0.0
        else:
            registration = "Other"
            rate = 0.0

        city_id = int(_vget(rs, "city_id", "CITY_ID", default=0) or 0)
        city_title = ""
        if city_id:
            city = self.repo.get_city(city_id)
            if city:
                city_title = str(_vget(city, "City_Title", "city_title", default="not found") or "not found")
            else:
                city_title = "ID not found..."

        return FinPurSupplierOut(
            supplier_id=supplier_id,
            vendor_title=title,
            address=str(_vget(rs, "Address", "address", default="") or ""),
            stax_id=str(_vget(rs, "stax_id", "STAX_ID", default="") or ""),
            city_id=city_id,
            city_title=city_title,
            registration=registration,
            tag_1=tag_1,
            sales_tax_rate=rate,
        )

    def get_item(
        self,
        *,
        item_id: Optional[float] = None,
        manual_id: Optional[float] = None,
        barcode: Optional[str] = None,
        barcode_ws: Optional[str] = None,
    ) -> FinPurItemOut:
        view = self.repo.get_item_view(
            item_id=item_id, manual_id=manual_id, barcode=barcode, barcode_ws=barcode_ws
        )
        if not view and item_id is not None:
            view = self.repo.get_item(item_id)
        if not view:
            if barcode or barcode_ws:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode ID not found.")
            if manual_id is not None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual ID not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item ID not found, please re-enter ...\n\n Or Main Or Sub Account ID is selected. ",
            )

        iid = float(_vget(view, "item_id", "ITEM_ID"))
        item = self.repo.get_item(iid) or view
        ed = int(_vget(item, "ed_status", default=0) or 0)
        if ed == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item ID is Disabled, Consultant Administrator .... ",
            )

        manual = _vget(item, "manualid", "manual_id")
        title = str(_vget(item, "Item_Title", "item_title", default="") or "")
        if manual is not None:
            title = f"{title} --- {manual}"

        uom_id = int(_vget(item, "uom_id", default=0) or 0)
        uom_abbr = ""
        if uom_id:
            uom = self.repo.get_uom(uom_id)
            uom_abbr = str(_vget(uom, "uom_abbr", default="UOM ID not found ...... ") or "UOM ID not found ...... ")

        co_id = _vget(item, "co_id")
        co_title = ""
        if co_id is not None and int(co_id or 0) != 0:
            co = self.repo.get_company(int(co_id))
            if co:
                co_title = str(_vget(co, "co_TITLE", "co_title", default="") or "")
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company ID not found... ",
                )

        return FinPurItemOut(
            item_id=iid,
            manual_id=float(manual) if manual is not None else None,
            item_title=title,
            barcodeid=str(_vget(item, "barcodeid", default="") or "") or None,
            barcodeid_ws=str(_vget(item, "barcodeid_ws", default="") or "") or None,
            co_id=int(co_id) if co_id is not None else None,
            co_title=co_title,
            uom_id=uom_id or None,
            uom_abbr=uom_abbr,
            sales_rate=_money(_vget(item, "sales_Rate", "sales_rate")),
            stock_qty=_money(_vget(item, "Cqty", "cqty")),
            mrp=_money(_vget(item, "disc_p1")),
            tp_rate=_money(_vget(item, "Cqty1", "cqty1")),
            stax_reg=_money(_vget(item, "STAX_REG", "stax_reg")),
            ed_status=ed,
        )

    def search_suppliers(self, q: str) -> List[FinPurLookupRow]:
        return [
            FinPurLookupRow(
                id=str(int(_vget(r, "vendor_id"))),
                title=str(_vget(r, "vendor_title", default="") or ""),
                extra=str(_vget(r, "stax_id", default="") or ""),
            )
            for r in self.repo.search_suppliers(q)
        ]

    def search_items(self, q: str) -> List[FinPurLookupRow]:
        return [
            FinPurLookupRow(
                id=str(_vget(r, "item_id")),
                title=str(_vget(r, "item_title", default="") or ""),
                extra=str(_vget(r, "manualid", default="") or ""),
            )
            for r in self.repo.search_items(q)
        ]

    # ----- load document -----

    def load_document(self, prod_id: int) -> FinPurDocumentOut:
        cfg = self.get_config()
        if not cfg.book_ok:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=cfg.book_message)

        header = self.repo.get_header(prod_id, fiscal=cfg.fiscal, doc_type_id=cfg.doc_type_id)
        if not header:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document/Voucher not found, please re-enter ...",
            )

        sys_status = int(_vget(header, "sys_status", default=0) or 0)
        if sys_status == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document/Voucher is posted, please re-enter ...",
            )

        serial_no = int(_vget(header, "serial_no", "SERIAL_NO"))
        supplier_id = int(_vget(header, "supplier_id", "SUPPLIER_ID", default=0) or 0)
        supplier_title = ""
        city_title = ""
        registration = "Registered" if int(_vget(header, "stax_type", default=0) or 0) == 0 else "UN-Registered"

        try:
            supplier = self.get_supplier(supplier_id)
            supplier_title = supplier.vendor_title
            city_title = supplier.city_title
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier ID Not Found ..... ",
            )

        charges = FinPurHeaderCharges(
            discount=_money(_vget(header, "discount_amt")),
            claim=_money(_vget(header, "claim_amt")),
            other_ded=_money(_vget(header, "other_ded_amt")),
            loading=_money(_vget(header, "loading_amt")),
            carriage=_money(_vget(header, "carriage_amt")),
            other_charges=_money(_vget(header, "other_charges_amt")),
        )

        # VB6 load adjusts HDiscount vs line discount then zeros LblDiscount — keep raw H* from DB;
        # client recalculates display totals.
        lines_out: List[FinPurLineOut] = []
        for row in self.repo.get_lines(serial_no):
            item_id = float(_vget(row, "item_id", "ITEM_ID", default=0) or 0)
            item_title = "Item ID not found ...."
            item = self.repo.get_item(item_id) if item_id else None
            if item:
                item_title = f"{_vget(item, 'item_title', default='')} --- {_vget(item, 'manualid', default='')}"

            exp = _as_date(_vget(row, "exp_date", "EXP_DATE"))
            lines_out.append(
                FinPurLineOut(
                    serial_order=int(_vget(row, "serial_order", "SERIAL_ORDER", default=0) or 0),
                    item_id=item_id,
                    item_title=item_title,
                    qty=_money(_vget(row, "qty")),
                    rate=_money(_vget(row, "rate")),
                    pur_amt=_money(_vget(row, "PUR_amt", "pur_amt")),
                    stax_rate=_money(_vget(row, "stax_rate", "STAX_RATE")),
                    stax_amt=_money(_vget(row, "stax_amt", "STAX_AMT")),
                    disc_per=_money(_vget(row, "disc_Per", "DISC_PER")),
                    disc_amt=_money(_vget(row, "disc_amt", "DISC_AMT")),
                    disc_per_oi=_money(_vget(row, "disc_Per_oi", "DISC_PER_OI")),
                    disc_amt_oi=_money(_vget(row, "disc_amt_oi", "DISC_AMT_OI")),
                    total_amt=_money(_vget(row, "total_amt", "TOTAL_AMT")),
                    remarks=str(_vget(row, "remarks", default="") or ""),
                    exp_date=exp,
                )
            )

        totals = self._compute_totals(lines_out, charges)
        doc_date = _as_date(_vget(header, "doc_date", "DOC_DATE")) or date.today()

        return FinPurDocumentOut(
            prod_id=prod_id,
            serial_no=serial_no,
            fiscal=int(_vget(header, "fiscal", default=0) or 0),
            doc_type_id=int(_vget(header, "Doc_Type_ID", "doc_type_id", default=2) or 2),
            doc_date=doc_date,
            supplier_id=supplier_id,
            supplier_title=supplier_title,
            registration=registration,
            remarks=str(_vget(header, "remarks", default="") or ""),
            payment_type=int(_vget(header, "payment_type", default=0) or 0),
            stax_type=int(_vget(header, "stax_type", default=0) or 0),
            gp_id=str(_vget(header, "gp_id", default="") or ""),
            gp_time=str(_vget(header, "gp_time", default="") or ""),
            vendor_title=str(_vget(header, "Vendor_Title", "vendor_title", default="") or ""),
            address=str(_vget(header, "Address", "address", default="") or ""),
            stax_id=str(_vget(header, "stax_id", default="") or ""),
            city_id=int(_vget(header, "city_id", default=0) or 0),
            city_title=city_title,
            sys_status=sys_status,
            doc_abbr=cfg.doc_abbr,
            charges=charges,
            totals=totals,
            lines=lines_out,
        )

    def _compute_totals(self, lines: List[FinPurLineOut], charges: FinPurHeaderCharges) -> FinPurTotalsOut:
        n_qty = n_amount = n_stax = n_disc = n_off = 0.0
        for line in lines:
            n_qty += line.qty
            n_amount += line.pur_amt
            n_stax += line.stax_amt
            n_disc += line.disc_amt
            n_off += line.disc_amt_oi
        n_tamount = n_amount - n_disc + n_stax
        m_discount = charges.discount + charges.claim + charges.other_ded
        m_charges = charges.loading + charges.carriage + charges.other_charges
        net = n_tamount - n_off - m_discount + m_charges
        return FinPurTotalsOut(
            qty=round(n_qty, 2),
            amount=round(n_amount, 2),
            sales_tax=round(n_stax, 2),
            discount=round(n_disc, 2),
            stax_excl_amt=round(n_amount - n_disc, 2),
            off_inv_disc=round(n_off, 2),
            included=round(n_tamount, 2),
            net_amount=round(net, 2),
            header_discount=round(m_discount, 2),
            header_charges=round(m_charges, 2),
            diff=round(m_charges - m_discount, 2),
        )

    # ----- save -----

    def save_document(self, payload: FinPurSaveRequest) -> FinPurSaveResponse:
        cfg = self.get_config()
        if not cfg.book_ok:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=cfg.book_message)

        if not payload.lines:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No transaction to slave ")

        if cfg.fiscal_start and cfg.fiscal_end:
            if payload.doc_date < cfg.fiscal_start or payload.doc_date > cfg.fiscal_end:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Document/Voucher Date out of range ...  \n\n"
                        f"Select between  {cfg.fiscal_start}  and  {cfg.fiscal_end}  "
                    ),
                )

        # Ensure supplier exists
        self.get_supplier(payload.supplier_id)

        remarks = payload.remarks if payload.remarks else "Nil"
        gl_setup = self.repo.get_doc_gl_setup(self.DOC_TYPE_ID) or {}
        book_id = cfg.book_id

        existing = None
        if payload.prod_id and payload.prod_id > 0:
            existing = self.repo.get_header(payload.prod_id, fiscal=cfg.fiscal, doc_type_id=cfg.doc_type_id)

        c_found = existing is not None
        serial_code = int(_vget(existing, "serial_no", default=0) or 0) if existing else 0

        try:
            if c_found:
                # Reverse prior inventory + GL balances, delete old detail
                self.repo.reverse_inventory_for_serial(serial_code)
                self.repo.reverse_gl_balances_for_serial(serial_code)
                self.repo.delete_detail(serial_code)

            if c_found:
                new_voucher_no = int(payload.prod_id)
            else:
                new_voucher_no = self.repo.next_prod_id(cfg.fiscal)
                serial_code = self.repo.allocate_serial_no(self.legacy_uid)

            line_disc_total = sum(_money(l.disc_amt) for l in payload.lines)
            h = payload.charges
            discount_amt = _money(h.discount) + line_disc_total

            self.repo.upsert_header(
                is_new=not c_found,
                serial_no=serial_code,
                prod_id=new_voucher_no,
                fiscal=cfg.fiscal,
                doc_type_id=cfg.doc_type_id,
                doc_date=payload.doc_date,
                supplier_id=payload.supplier_id,
                remarks=remarks,
                payment_type=payload.payment_type,
                stax_type=payload.stax_type,
                gp_id=payload.gp_id,
                gp_time=payload.gp_time,
                vendor_title=payload.vendor_title,
                address=payload.address,
                stax_id=payload.stax_id,
                city_id=payload.city_id,
                discount_amt=discount_amt,
                claim_amt=_money(h.claim),
                other_ded_amt=_money(h.other_ded),
                loading_amt=_money(h.loading),
                carriage_amt=_money(h.carriage),
                other_charges_amt=_money(h.other_charges),
            )

            # VB6 T_Amount accumulation (preserve loop formula)
            t_amount = 0.0
            it_discount = 0.0
            it_discount_oi = 0.0
            l_tsale = 0.0
            l_tsales_tax = 0.0
            m_sales_local_amt = 0.0
            m_sales_import_amt = 0.0

            m_discount = _money(h.discount) + _money(h.claim) + _money(h.other_ded)
            m_charges = _money(h.loading) + _money(h.carriage) + _money(h.other_charges)
            l_discount = line_disc_total
            lbl_off_inv = sum(_money(l.disc_amt_oi) for l in payload.lines)

            credit_sales_import_id = int(_vget(gl_setup, "sp_ac_id", default=0) or 0)
            credit_sales_local_id = int(_vget(gl_setup, "sp_ac_id_local", default=0) or 0)
            sales_tax_id = int(_vget(gl_setup, "stax_id", default=0) or 0)
            discount_id = int(_vget(gl_setup, "discount_id", default=0) or 0)
            claim_id = int(_vget(gl_setup, "claim_id", default=0) or 0)
            other_ded_id = int(_vget(gl_setup, "otherded_id", default=0) or 0)
            carriage_id = int(_vget(gl_setup, "carriage_id", default=0) or 0)
            loading_id = int(_vget(gl_setup, "loading_id", default=0) or 0)
            other_charges_id = int(_vget(gl_setup, "othercharges_id", default=0) or 0)

            self.repo.delete_fin_ldgr_by_serial(serial_code)
            self.repo.delete_gl_lines(serial_code)

            # VB6 writes gl0002 before detail/GL lines (Amount from prior T_Amount; we set after loop too)
            self.repo.upsert_gl_header(
                is_new=not c_found,
                serial_no=serial_code,
                voucher_id=new_voucher_no,
                book_id=book_id,
                v_mode=self.MV_MODE,
                fiscal=cfg.fiscal,
                book_type=self.M_BOOK_TYPE,
                voucher_date=payload.doc_date,
                amount=0,
                tnot=len(payload.lines),
                username=self.username,
            )

            supplier_title = ""
            try:
                supplier_title = self.get_supplier(payload.supplier_id).vendor_title
            except HTTPException:
                supplier_title = payload.vendor_title

            for n_cnt, line in enumerate(payload.lines, start=1):
                self._validate_line(line)
                tmp_qty = _money(line.qty)
                tmp_rate = _money(line.rate)
                tmp_sale_amt = _money(line.pur_amt) if line.pur_amt else round(tmp_rate * tmp_qty, 2)
                tmp_stax_rate = _money(line.stax_rate)
                tmp_stax_amt = _money(line.stax_amt)
                tmp_disc_rate = _money(line.disc_per)
                tmp_disc_amt = _money(line.disc_amt)
                tmp_doi_rate = _money(line.disc_per_oi)
                tmp_doi_amt = _money(line.disc_amt_oi)
                tmp_total = _money(line.total_amt)
                if not tmp_total:
                    tmp_total = round(((tmp_sale_amt + tmp_stax_amt) - tmp_disc_amt) - tmp_doi_amt, 2)

                l_tsale += tmp_sale_amt
                l_tsales_tax += tmp_stax_amt
                it_discount += tmp_disc_amt
                it_discount_oi += tmp_doi_amt
                # Preserve VB6 cumulative formula
                t_amount = (((t_amount + tmp_sale_amt) - it_discount) - it_discount_oi)

                exp_date = line.exp_date or payload.doc_date
                self.repo.insert_detail_line(
                    {
                        "prod_id": float(new_voucher_no),
                        "serial_order": n_cnt,
                        "serial_no": serial_code,
                        "doc_date": payload.doc_date,
                        "item_id": line.item_id,
                        "qty": tmp_qty,
                        "rate": tmp_rate,
                        "pur_amt": tmp_sale_amt,
                        "stax_rate": int(tmp_stax_rate),
                        "stax_amt": tmp_stax_amt,
                        "disc_per": tmp_disc_rate,
                        "disc_amt": tmp_disc_amt,
                        "disc_per_oi": tmp_doi_rate,
                        "disc_amt_oi": tmp_doi_amt,
                        "total_amt": tmp_total,
                        "remarks": (line.remarks or "")[:10],
                        "exp_date": exp_date if line.item_id else None,
                    }
                )

                self.repo.ensure_supp_item(payload.supplier_id, line.item_id)

                item = self.repo.get_item(line.item_id)
                gl_integ = 0
                if item:
                    if self.STAX_TYPE_MODE == 0:
                        gl_integ = int(_vget(item, "gl_pur_id", default=0) or 0)
                    else:
                        gl_integ = credit_sales_local_id
                    m_sales_local_amt += tmp_sale_amt
                    stock_amt = (((tmp_sale_amt + tmp_stax_amt) - tmp_disc_amt) - tmp_doi_amt)
                    cost_rate = stock_amt / tmp_qty if tmp_qty else 0.0
                    self.repo.update_item_on_purchase(
                        item_id=line.item_id,
                        qty=tmp_qty,
                        stock_amt=stock_amt,
                        cost_rate=cost_rate,
                    )

                self.repo.insert_fin_ldgr(
                    {
                        "item_id": line.item_id,
                        "doc_id": new_voucher_no,
                        "doc_date": payload.doc_date,
                        "fiscal": cfg.fiscal,
                        "doc_type_id": cfg.doc_type_id,
                        "serial_no": serial_code,
                        "qtydr": tmp_qty,
                        "rate": tmp_rate,
                        "amtdr": tmp_sale_amt,
                        "desc": f"{payload.gp_id}: {supplier_title}"[:40],
                    }
                )

                if self.STAX_TYPE_MODE == 0 and tmp_sale_amt != 0 and gl_integ:
                    self.repo.insert_gl_line(
                        {
                            "voucher_id": new_voucher_no,
                            "book_id": book_id,
                            "vdate": payload.doc_date,
                            "serial_no": serial_code,
                            "serial_order": n_cnt,
                            "ac_id": gl_integ,
                            "adcn": payload.gp_id,
                            "narration": " " + (line.item_title or ""),
                            "debit": tmp_sale_amt,
                            "credit": 0,
                        }
                    )

            # Refresh gl0002 Amount with VB6 T_Amount
            self.repo.upsert_gl_header(
                is_new=False,
                serial_no=serial_code,
                voucher_id=new_voucher_no,
                book_id=book_id,
                v_mode=self.MV_MODE,
                fiscal=cfg.fiscal,
                book_type=self.M_BOOK_TYPE,
                voucher_date=payload.doc_date,
                amount=t_amount,
                tnot=len(payload.lines),
                username=self.username,
            )

            # Summed GL when cSTaxType = 1
            if self.STAX_TYPE_MODE == 1:
                if m_sales_import_amt > 0 and credit_sales_import_id:
                    self.repo.insert_gl_line(
                        {
                            "voucher_id": new_voucher_no,
                            "book_id": book_id,
                            "vdate": payload.doc_date,
                            "serial_no": serial_code,
                            "serial_order": 1,
                            "ac_id": credit_sales_import_id,
                            "adcn": payload.gp_id,
                            "narration": supplier_title,
                            "debit": m_sales_import_amt,
                            "credit": 0,
                        }
                    )
                if m_sales_local_amt > 0 and credit_sales_local_id:
                    self.repo.insert_gl_line(
                        {
                            "voucher_id": new_voucher_no,
                            "book_id": book_id,
                            "vdate": payload.doc_date,
                            "serial_no": serial_code,
                            "serial_order": 2,
                            "ac_id": credit_sales_local_id,
                            "adcn": payload.gp_id,
                            "narration": supplier_title,
                            "debit": m_sales_local_amt,
                            "credit": 0,
                        }
                    )
                if l_tsales_tax > 0 and sales_tax_id:
                    self.repo.insert_gl_line(
                        {
                            "voucher_id": new_voucher_no,
                            "book_id": book_id,
                            "vdate": payload.doc_date,
                            "serial_no": serial_code,
                            "serial_order": 3,
                            "ac_id": sales_tax_id,
                            "adcn": payload.gp_id,
                            "narration": supplier_title,
                            "debit": l_tsales_tax,
                            "credit": 0,
                        }
                    )

            # VB6: HLoading → mCarriageId ; HCarriage → mLoadingID (Fin_PurDed double-swap)
            if _money(h.loading) > 0 and carriage_id:
                self.repo.insert_gl_line(
                    {
                        "voucher_id": new_voucher_no,
                        "book_id": book_id,
                        "vdate": payload.doc_date,
                        "serial_no": serial_code,
                        "serial_order": 4,
                        "ac_id": carriage_id,
                        "adcn": payload.gp_id,
                        "narration": supplier_title,
                        "debit": _money(h.loading),
                        "credit": 0,
                    }
                )
            if _money(h.carriage) > 0 and loading_id:
                self.repo.insert_gl_line(
                    {
                        "voucher_id": new_voucher_no,
                        "book_id": book_id,
                        "vdate": payload.doc_date,
                        "serial_no": serial_code,
                        "serial_order": 5,
                        "ac_id": loading_id,
                        "adcn": payload.gp_id,
                        "narration": supplier_title,
                        "debit": _money(h.carriage),
                        "credit": 0,
                    }
                )
            if _money(h.other_charges) > 0 and other_charges_id:
                self.repo.insert_gl_line(
                    {
                        "voucher_id": new_voucher_no,
                        "book_id": book_id,
                        "vdate": payload.doc_date,
                        "serial_no": serial_code,
                        "serial_order": 6,
                        "ac_id": other_charges_id,
                        "adcn": payload.gp_id,
                        "narration": supplier_title,
                        "debit": _money(h.other_charges),
                        "credit": 0,
                    }
                )

            l_net_invoice = l_tsale - (l_discount + lbl_off_inv) + l_tsales_tax + m_charges
            if l_net_invoice != 0:
                self.repo.insert_gl_line(
                    {
                        "voucher_id": new_voucher_no,
                        "book_id": book_id,
                        "vdate": payload.doc_date,
                        "serial_no": serial_code,
                        "serial_order": 7,
                        "ac_id": payload.supplier_id,
                        "adcn": payload.gp_id,
                        "narration": f"GRN No. {new_voucher_no}",
                        "debit": 0,
                        "credit": l_net_invoice,
                    }
                )

            if (m_discount + l_discount) > 0:
                if (_money(h.discount) + l_discount) > 0 and discount_id:
                    self.repo.insert_gl_line(
                        {
                            "voucher_id": new_voucher_no,
                            "book_id": book_id,
                            "vdate": payload.doc_date,
                            "serial_no": serial_code,
                            "serial_order": 8,
                            "ac_id": discount_id,
                            "adcn": payload.gp_id,
                            "narration": f"{supplier_title} On Invoice.",
                            "debit": 0,
                            "credit": _money(h.discount) + l_discount,
                        }
                    )
                if lbl_off_inv > 0 and discount_id:
                    self.repo.insert_gl_line(
                        {
                            "voucher_id": new_voucher_no,
                            "book_id": book_id,
                            "vdate": payload.doc_date,
                            "serial_no": serial_code,
                            "serial_order": 9,
                            "ac_id": discount_id,
                            "adcn": payload.gp_id,
                            "narration": f"{supplier_title} Off Invoice.",
                            "debit": 0,
                            "credit": lbl_off_inv,
                        }
                    )
                if _money(h.claim) > 0 and claim_id:
                    self.repo.insert_gl_line(
                        {
                            "voucher_id": new_voucher_no,
                            "book_id": book_id,
                            "vdate": payload.doc_date,
                            "serial_no": serial_code,
                            "serial_order": 10,
                            "ac_id": claim_id,
                            "adcn": payload.gp_id,
                            "narration": supplier_title,
                            "debit": 0,
                            "credit": _money(h.claim),
                        }
                    )
                if _money(h.other_ded) > 0 and other_ded_id:
                    self.repo.insert_gl_line(
                        {
                            "voucher_id": new_voucher_no,
                            "book_id": book_id,
                            "vdate": payload.doc_date,
                            "serial_no": serial_code,
                            "serial_order": 11,
                            "ac_id": other_ded_id,
                            "adcn": payload.gp_id,
                            "narration": supplier_title,
                            "debit": 0,
                            "credit": _money(h.other_ded),
                        }
                    )

            total_dr, total_cr = self.repo.apply_gl_balances_for_serial(serial_code)
            self.repo.delete_zero_item_lines()
            self.db.commit()

            imbalance_note = ""
            if round(total_dr, 2) != round(total_cr, 2):
                imbalance_note = f" total debit {total_dr}  total credit {total_cr}"

            if not c_found:
                msg = f"New Document/Voucher Added. No. {cfg.doc_abbr} {new_voucher_no}"
            else:
                msg = f"Document/Voucher Edited. No. {cfg.doc_abbr} {new_voucher_no}"
            if imbalance_note:
                msg = msg + imbalance_note

            needs_resave = self.repo.check_detail_data(new_voucher_no, book_id)
            if needs_resave:
                msg = msg + " Click the save button again."

            return FinPurSaveResponse(
                message=msg,
                prod_id=new_voucher_no,
                serial_no=serial_code,
                doc_display=f"{cfg.doc_abbr} {new_voucher_no}",
                needs_resave=needs_resave,
            )
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in Query contact with Administrator. ({exc})",
            ) from exc

    def _validate_line(self, line: FinPurLineIn) -> None:
        if not line.item_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid:  Please enter Quantity ...  ")
        if _money(line.qty) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid:  Please enter Quantity ...  ",
            )
        item = self.repo.get_item(line.item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item ID not found, please re-enter ...",
            )

    # ----- delete -----

    def delete_document(self, prod_id: int) -> FinPurDeleteResponse:
        cfg = self.get_config()
        header = self.repo.get_header(prod_id, fiscal=cfg.fiscal, doc_type_id=cfg.doc_type_id)
        if not header:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document/Voucher not found, please re-enter ...",
            )
        serial_code = int(_vget(header, "serial_no"))
        try:
            self.repo.reverse_inventory_for_serial(serial_code)
            self.repo.reverse_gl_balances_for_serial(serial_code)
            self.repo.delete_detail(serial_code)
            self.repo.delete_header(prod_id, serial_code)
            self.repo.delete_fin_ldgr(prod_id, serial_code, cfg.doc_type_id)
            self.repo.delete_gl_for_document(serial_code, cfg.book_id, prod_id)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc
        return FinPurDeleteResponse(
            message=f"Document ID: {prod_id}  has been deleted... ",
            prod_id=prod_id,
        )

    def assign_company(self, co_id: int, item_ids: List[float]) -> dict:
        if not self.is_sa and not self.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acess denied contact with administrator.")
        co = self.repo.get_company(co_id)
        if not co:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company ID not found... ")
        try:
            n = self.repo.assign_co_to_items(co_id, item_ids)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"message": f"{n} Items Added successfully.", "count": n}

    def update_item_from_detail(
        self,
        *,
        item_id: float,
        mrp: float,
        stax_rate: float,
        stax_amt: float,
        qty: float,
        amount: float,
        disc_amt: float,
        off_inv_disc_amt: float,
        rate: float,
        co_id: int,
    ) -> None:
        """Mirror Fin_PurD CmdSave item field update (before grid append)."""
        if qty == 0:
            return
        oamt1 = round(stax_amt / qty, 2)
        camt1 = round((amount - disc_amt - off_inv_disc_amt) / qty, 2)
        try:
            self.repo.update_item_from_line_entry(
                item_id=item_id,
                mrp=mrp,
                stax_reg=stax_rate,
                oamt1=oamt1,
                camt1=camt1,
                cqty1=rate,
                co_id=co_id,
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(exc)) from exc
