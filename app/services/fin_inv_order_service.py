"""Purchase Order business logic — mirrors VB6 Fin_InvM_Order."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.fin_inv_order_repository import FinInvOrderRepository, _vget
from app.schemas.fin_inv_order import (
    FinInvOrderAddSupplierItemResponse,
    FinInvOrderConfigOut,
    FinInvOrderDeleteResponse,
    FinInvOrderDocumentOut,
    FinInvOrderHeaderCharges,
    FinInvOrderHistoryRow,
    FinInvOrderItemOut,
    FinInvOrderLineIn,
    FinInvOrderLineOut,
    FinInvOrderLookupRow,
    FinInvOrderPoHistoryRow,
    FinInvOrderPrintHeader,
    FinInvOrderPrintLine,
    FinInvOrderPrintOut,
    FinInvOrderPrintRow,
    FinInvOrderSaveRequest,
    FinInvOrderSaveResponse,
    FinInvOrderSupplierItemOut,
    FinInvOrderSupplierOut,
    FinInvOrderTotalsOut,
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


# VB6 LstInvStore_shortOrder / PO100.pdf layout defaults
PO_PRINT_COMPANY_ADDRESS = "193-A, QAMAR PARK SHAD BAGH LAHORE."
PO_PRINT_COMPANY_PHONE = "Ph No.+92-42-37603151-2"
PO_PRINT_COMPANY_NTN = "3973706-3"
PO_PRINT_COMPANY_STRN = "0300397370614"
PO_PRINT_NOTE = (
    "Goods will be received as per the purchase order and only "
    "18% GST Invoices will be accepted. If the company is exampted "
    "from WHT, Provide the examption certificate."
)


def _format_po_print_date(doc_date, doc_date_t) -> str:
    """VB6 report uses document date at 12:00 AM (see PO100.pdf)."""
    if doc_date:
        if isinstance(doc_date, datetime):
            d = doc_date.date()
        else:
            d = doc_date
        return f"{d.month}/{d.day}/{d.year} 12:00 AM"
    if doc_date_t and isinstance(doc_date_t, datetime):
        dt = doc_date_t
        hour = dt.hour % 12 or 12
        ampm = "AM" if dt.hour < 12 else "PM"
        return f"{dt.month}/{dt.day}/{dt.year} {hour}:{dt.minute:02d} {ampm}"
    return ""


class FinInvOrderService:
    DOC_TYPE_ID = 33
    M_FISCAL = 0
    MAX_ENTRIES = 2000
    DEFAULT_BOOK_ID = 133

    def __init__(
        self,
        db: Session,
        *,
        username: str,
        legacy_uid: Optional[int] = None,
        is_admin: bool = False,
        web_module_authorized: bool = False,
    ):
        self.db = db
        self.repo = FinInvOrderRepository(db)
        self.username = username
        self.legacy_uid = legacy_uid or settings.voucher_legacy_uid
        self.is_admin = is_admin
        self.web_module_authorized = web_module_authorized

    def get_config(self) -> FinInvOrderConfigOut:
        setup = self.repo.get_gsetup()
        doc = self.repo.get_doc_type(self.DOC_TYPE_ID) or {}
        book_id = int(_vget(doc, "doc_book_id", default=self.DEFAULT_BOOK_ID) or self.DEFAULT_BOOK_ID)
        book = self.repo.get_book(book_id)
        book_ok = True
        book_message = ""
        if not book:
            book_ok = False
            book_message = "Book not found or for Use of Other Modules, please enter another ..."
        elif not self.is_admin and not self.repo.user_has_book(self.legacy_uid, book_id):
            # ContPL Gc0003 often has no rows for PO book 133 (live DB only uid 77).
            # Web access is already gated by inventory.fin_inv_order.* JWT permissions,
            # so treat module-authorized users as book-authorized (VB6 book ACL superseded).
            if self.web_module_authorized:
                book_ok = True
                book_message = ""
            else:
                book_ok = False
                book_message = "Permission to Book is denied, Consult Administrator ... "

        fiscal_start = _as_date(_vget(setup, "fiscal_start"))
        fiscal_end = _as_date(_vget(setup, "Fiscal_end", "fiscal_end"))

        return FinInvOrderConfigOut(
            doc_type_id=self.DOC_TYPE_ID,
            doc_abbr=str(_vget(doc, "doc_abbr", default="PO") or "PO"),
            book_id=book_id,
            fiscal=self.M_FISCAL,
            max_entries=self.MAX_ENTRIES,
            fiscal_start=fiscal_start,
            fiscal_end=fiscal_end,
            company_name=settings.company_name,
            book_ok=book_ok,
            book_message=book_message,
            legacy_uid=self.legacy_uid,
        )

    def get_supplier(self, supplier_id: int) -> FinInvOrderSupplierOut:
        if not supplier_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Supplier ID.")
        rs = self.repo.get_supplier(supplier_id)
        if not rs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier ID Not Found ..... ",
            )
        title = str(_vget(rs, "Vendor_Title", "vendor_title", default="") or "")
        if not title:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Supplier ID.")
        tag_1 = int(_vget(rs, "tag_1", "TAG_1", default=0) or 0)
        if tag_1 == 0:
            registration = "Registered"
        elif tag_1 == 1:
            registration = "Un-Registered"
        else:
            registration = "Other"

        city_id = int(_vget(rs, "city_id", "CITY_ID", default=0) or 0)
        city_title = ""
        if city_id:
            city = self.repo.get_city(city_id)
            if city:
                city_title = str(_vget(city, "City_Title", "city_title", default="not found") or "not found")
            else:
                city_title = "ID not found..."

        return FinInvOrderSupplierOut(
            supplier_id=supplier_id,
            vendor_title=title,
            contact_person=str(_vget(rs, "CONTACT_PERSON", "contact_person", default="") or "").strip(),
            address=str(_vget(rs, "Address", "address", default="") or ""),
            stax_id=str(_vget(rs, "stax_id", "STAX_ID", default="") or ""),
            city_id=city_id,
            city_title=city_title,
            registration=registration,
            tag_1=tag_1,
        )

    def get_supplier_items(self, supplier_id: int) -> List[FinInvOrderSupplierItemOut]:
        self.get_supplier(supplier_id)
        return [
            FinInvOrderSupplierItemOut(
                supplier_title=str(_vget(r, "ac_title", default="") or ""),
                manual_id=str(_vget(r, "manualid", default="") or ""),
                item_title=str(_vget(r, "ITEM_TITLE", "item_title", default="") or ""),
                tnot=_money(_vget(r, "TNOT", "tnot")),
                stock_qty=_money(_vget(r, "CQTY", "cqty")),
                cost_rate=_money(_vget(r, "COST_RATE", "cost_rate")),
                sales_rate=_money(_vget(r, "SALES_RATE", "sales_rate")),
                item_id=float(_vget(r, "item_id", "ITEM_ID")),
            )
            for r in self.repo.get_supplier_items(supplier_id)
        ]

    def get_item(
        self,
        *,
        supplier_id: Optional[int] = None,
        item_id: Optional[float] = None,
        manual_id: Optional[float] = None,
        barcode: Optional[str] = None,
        barcode_ws: Optional[str] = None,
    ) -> FinInvOrderItemOut:
        view = None
        ws = bool(barcode_ws)
        if item_id is not None:
            view = self.repo.get_item_view_t(item_id=item_id)
        elif manual_id is not None:
            view = self.repo.get_item_view_t(manual_id=manual_id)
        elif barcode is not None:
            view = self.repo.get_item_view_t(barcode=barcode)
            if not view:
                view = self.repo.get_item_view_ws(barcode)
                ws = True
        elif barcode_ws is not None:
            view = self.repo.get_item_view_ws(barcode_ws)
            ws = True

        if not view:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

        iid = float(_vget(view, "item_id", "ITEM_ID"))
        in_catalog = False
        if supplier_id:
            in_catalog = self.repo.check_supplier_item(supplier_id, iid)

        return FinInvOrderItemOut(
            item_id=iid,
            manual_id=float(_vget(view, "manualid", default=0) or 0) or None,
            item_title=str(_vget(view, "Item_Title", "item_title", default="") or ""),
            barcodeid=str(_vget(view, "barcodeid", default="") or "") or None,
            barcodeid_ws=str(_vget(view, "barcodeid_ws", default="") or "") or None,
            cost_rate=_money(_vget(view, "cost_Rate", "cost_rate")),
            sales_rate=_money(_vget(view, "sales_Rate", "sales_rate")),
            stock_qty=_money(_vget(view, "Cqty", "cqty")),
            visacard_rate=_money(_vget(view, "visacard_rate")),
            disc_p4=_money(_vget(view, "disc_p4")),
            in_supplier_catalog=in_catalog,
        )

    def search_suppliers(self, q: str) -> List[FinInvOrderLookupRow]:
        return [
            FinInvOrderLookupRow(
                id=str(int(_vget(r, "vendor_id"))),
                title=str(_vget(r, "vendor_title", default="") or ""),
                extra=str(_vget(r, "stax_id", default="") or ""),
            )
            for r in self.repo.search_suppliers(q)
        ]

    def search_items(self, q: str) -> List[FinInvOrderLookupRow]:
        return [
            FinInvOrderLookupRow(
                id=str(_vget(r, "item_id")),
                title=str(_vget(r, "item_title", default="") or ""),
                extra=str(_vget(r, "manualid", default="") or ""),
            )
            for r in self.repo.search_items(q)
        ]

    def item_history(self, item_id: float, limit: int = 5) -> dict:
        purchase = [
            FinInvOrderHistoryRow(
                doc_id=str(_vget(r, "PROD_ID", "prod_id", default="")),
                doc_date=_as_date(_vget(r, "doc_date")),
                party=str(_vget(r, "supplier_title", default="") or ""),
                qty=_money(_vget(r, "QTY", "qty")),
                rate=_money(_vget(r, "rate")),
                extra=str(_vget(r, "Exp_Date", "exp_date", default="") or ""),
            )
            for r in self.repo.purchase_history(item_id, limit)
        ]
        sales = [
            FinInvOrderHistoryRow(
                doc_id=str(_vget(r, "Inv_ID", "inv_id", default="")),
                doc_date=_as_date(_vget(r, "doc_date")),
                party=str(_vget(r, "customer_title", default="") or ""),
                qty=_money(_vget(r, "QTY", "qty")),
                rate=_money(_vget(r, "rate")),
            )
            for r in self.repo.sales_history(item_id, limit)
        ]
        return {"purchase": purchase, "sales": sales}

    def po_history(self, supplier_id: int, limit: int = 5) -> List[FinInvOrderPoHistoryRow]:
        self.get_supplier(supplier_id)
        return [
            FinInvOrderPoHistoryRow(
                inv_id=int(_vget(r, "INV_ID", "inv_id")),
                doc_date=_as_date(_vget(r, "DOC_DATE", "doc_date")),
                supplier_id=int(_vget(r, "CUST_ID", "cust_id", default=supplier_id) or supplier_id),
                supplier_title=str(_vget(r, "CUSTOMER_TITLE", "customer_title", default="") or ""),
                total_amt=_money(_vget(r, "TOTAL_AMT", "total_amt")),
            )
            for r in self.repo.po_history(supplier_id, limit)
        ]

    def get_print_data(self, inv_id: int) -> FinInvOrderPrintOut:
        rows = self.repo.get_print_rows(inv_id)
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Print data not found.")

        first = rows[0]
        total_qty = sum(_money(_vget(r, "qty", "QTY")) for r in rows)
        lines = [
            FinInvOrderPrintLine(
                serial_order=int(_vget(r, "serial_order", "SERIAL_ORDER", default=0) or 0),
                item_title=str(_vget(r, "item_title", "ITEM_TITLE", default="") or ""),
                qty=_money(_vget(r, "qty", "QTY")),
            )
            for r in rows
        ]
        header = FinInvOrderPrintHeader(
            inv_id=int(_vget(first, "inv_id", "INV_ID")),
            doc_date_display=_format_po_print_date(
                _vget(first, "doc_date", "DOC_DATE"),
                _vget(first, "doc_date_t", "DOC_DATE_T"),
            ),
            supplier_title=str(_vget(first, "customer_title", "CUSTOMER_TITLE", default="") or "").strip(),
            cust_order=str(_vget(first, "cust_order", "CUST_ORDER", default="") or "").strip(),
            full_name=str(_vget(first, "full_name", "FULL_NAME", default="") or "").strip(),
            total_qty=round(total_qty, 2),
            company_name=(settings.company_name or "Shafique Departmental Store.").rstrip(".") + ".",
            company_address=PO_PRINT_COMPANY_ADDRESS,
            company_phone=PO_PRINT_COMPANY_PHONE,
            company_ntn=PO_PRINT_COMPANY_NTN,
            company_strn=PO_PRINT_COMPANY_STRN,
            print_note=PO_PRINT_NOTE,
        )
        return FinInvOrderPrintOut(header=header, lines=lines)

    def add_supplier_item(self, supplier_id: int, manual_id: float) -> FinInvOrderAddSupplierItemResponse:
        self.get_supplier(supplier_id)
        if not manual_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select Item First.")
        item = self.repo.get_item_view_t(manual_id=manual_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual ID not found.")
        item_id = float(_vget(item, "item_id", "ITEM_ID"))
        if self.repo.supplier_has_item(supplier_id, manual_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item Already Exist")
        self.repo.add_supplier_item(supplier_id, item_id)
        return FinInvOrderAddSupplierItemResponse(message="Item added to supplier catalog.", item_id=item_id)

    def remove_supplier_item(self, supplier_id: int, item_id: float) -> dict:
        self.repo.remove_supplier_item(supplier_id, item_id)
        return {"message": "Item removed from supplier catalog."}

    def _compute_line(self, line: FinInvOrderLineIn) -> FinInvOrderLineIn:
        qty = _money(line.qty)
        rate = _money(line.rate)
        amount = _money(line.amount) if line.amount else round(qty * rate, 3)
        disc_per = _money(line.disc_per)
        disc_amt = _money(line.disc_amt) if line.disc_amt else round(amount * disc_per / 100, 3)
        net_amt = _money(line.net_amt) if line.net_amt else round(amount - disc_amt, 2)
        line.amount = amount
        line.disc_amt = disc_amt
        line.net_amt = net_amt
        return line

    def _compute_totals(self, lines: List[FinInvOrderLineOut], charges: FinInvOrderHeaderCharges) -> FinInvOrderTotalsOut:
        qty = amount = disc_amt = net_amt = 0.0
        for line in lines:
            qty += line.qty
            amount += line.amount
            disc_amt += line.disc_amt
            net_amt += line.net_amt
        header_discount = _money(charges.discount) + _money(charges.claim) + _money(charges.other_ded)
        header_charges = _money(charges.loading) + _money(charges.carriage) + _money(charges.other_charges)
        t_amount = round(net_amt, 2)
        net_invoice = round(t_amount - header_discount + header_charges, 2)
        return FinInvOrderTotalsOut(
            qty=round(qty, 3),
            amount=round(amount, 2),
            disc_amt=round(disc_amt, 2),
            net_amt=round(net_amt, 2),
            header_discount=round(header_discount, 2),
            header_charges=round(header_charges, 2),
            diff=round(header_charges - header_discount, 2),
            net_invoice=net_invoice,
        )

    def load_document(self, inv_id: int) -> FinInvOrderDocumentOut:
        cfg = self.get_config()
        if not cfg.book_ok:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=cfg.book_message)

        header = self.repo.get_header(inv_id, fiscal=cfg.fiscal, doc_type_id=cfg.doc_type_id)
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
        supplier_id = int(_vget(header, "cust_id", "CUST_ID", default=0) or 0)
        supplier = self.get_supplier(supplier_id)

        stax_type = int(_vget(header, "stax_type", default=0) or 0)
        if stax_type == 0:
            registration = "Registered"
        elif stax_type == 1:
            registration = "Un-Registered"
        else:
            registration = "Other"

        payment_type = int(_vget(header, "payment_type", default=1) or 1)
        if payment_type == 0:
            customer_title = supplier.vendor_title
            address = supplier.address
            stax_id = supplier.stax_id
            city_id = supplier.city_id
            city_title = supplier.city_title
        else:
            customer_title = str(_vget(header, "customer_title", "Customer_title", default="") or "")
            address = str(_vget(header, "Address", "address", default="") or "")
            stax_id = str(_vget(header, "stax_id", default="") or "")
            city_id = int(_vget(header, "city_id", default=0) or 0)
            city_title = supplier.city_title
            if city_id:
                city = self.repo.get_city(city_id)
                if city:
                    city_title = str(_vget(city, "City_Title", "city_title", default="not found") or "not found")
                else:
                    city_title = "ID not found..."

        charges = FinInvOrderHeaderCharges(
            discount=_money(_vget(header, "discount_amt")),
            claim=_money(_vget(header, "claim_amt")),
            other_ded=_money(_vget(header, "other_ded_amt")),
            loading=_money(_vget(header, "loading_amt")),
            carriage=_money(_vget(header, "carriage_amt")),
            other_charges=_money(_vget(header, "other_charges_amt")),
        )

        lines_out: List[FinInvOrderLineOut] = []
        for row in self.repo.get_lines(serial_no):
            item_id = float(_vget(row, "item_id", "ITEM_ID", default=0) or 0)
            item_title = "Item ID not found ...."
            manual_id = ""
            barcode_id = ""
            item = self.repo.get_item(item_id) if item_id else None
            view = self.repo.get_item_view_t(item_id=item_id) if item_id else None
            if item:
                item_title = str(_vget(item, "item_title", default="") or "")
            if view:
                manual_id = str(_vget(view, "manualid", default="") or "")
                barcode_id = str(_vget(view, "barcodeid", default="") or "")

            lines_out.append(
                FinInvOrderLineOut(
                    serial_order=int(_vget(row, "serial_order", "SERIAL_ORDER", default=0) or 0),
                    item_id=item_id,
                    barcode_id=barcode_id,
                    manual_id=manual_id,
                    item_title=item_title,
                    qty=_money(_vget(row, "qty")),
                    rate=_money(_vget(row, "rate")),
                    amount=_money(_vget(row, "sale_amt", "SALE_AMT")),
                    disc_per=_money(_vget(row, "stax_rate", "STAX_RATE")),
                    disc_amt=_money(_vget(row, "stax_amt", "STAX_AMT")),
                    net_amt=_money(_vget(row, "total_amt", "TOTAL_AMT")),
                )
            )

        totals = self._compute_totals(lines_out, charges)
        doc_date = _as_date(_vget(header, "doc_date", "DOC_DATE")) or date.today()

        return FinInvOrderDocumentOut(
            inv_id=inv_id,
            serial_no=serial_no,
            fiscal=int(_vget(header, "fiscal", default=0) or 0),
            doc_type_id=int(_vget(header, "doc_type_id", "Doc_Type_ID", default=33) or 33),
            doc_date=doc_date,
            supplier_id=supplier_id,
            supplier_title=supplier.vendor_title,
            registration=registration,
            cust_order=str(_vget(header, "cust_order", default="") or "").strip(),
            cust_order_date=str(_vget(header, "cust_order_date", default="") or "").strip(),
            payment_type=payment_type,
            stax_type=stax_type,
            gp_id=str(_vget(header, "gp_id", default="") or "").strip(),
            gp_time=str(_vget(header, "gp_time", default="") or "").strip(),
            customer_title=customer_title,
            address=address,
            stax_id=stax_id,
            city_id=city_id,
            city_title=city_title,
            remarks=str(_vget(header, "remarks", default="") or "").strip(),
            amount_rec=_money(_vget(header, "amount_rec", "AMOUNT_REC")),
            bal_amt=_money(_vget(header, "bal_amt", "BAL_AMT")),
            sys_status=sys_status,
            doc_abbr=cfg.doc_abbr,
            charges=charges,
            totals=totals,
            lines=lines_out,
        )

    def _validate_save(self, payload: FinInvOrderSaveRequest, cfg: FinInvOrderConfigOut) -> None:
        if not payload.lines:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select item first.")

        for line in payload.lines:
            if not line.item_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select item first.")
            computed = self._compute_line(line)
            if computed.qty == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zero quantity not allowed.")
            if computed.net_amt == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zero Net Amount not allowed.")
            if computed.rate == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Zero Rate not Allowed Contact with Administrator ...",
                )
            if not self.repo.check_supplier_item(payload.supplier_id, line.item_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Item not exist in Supplier Purchase Order Data.",
                )

        item_ids = [line.item_id for line in payload.lines]
        if len(item_ids) != len(set(item_ids)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item already exist.")

        if cfg.fiscal_start and cfg.fiscal_end:
            if payload.doc_date < cfg.fiscal_start or payload.doc_date > cfg.fiscal_end:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Document/Voucher Date out of range ...  \n\n"
                        f"Select between  {cfg.fiscal_start}  and  {cfg.fiscal_end}  "
                    ),
                )
        if payload.doc_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Document Date > System Date (Post Date not valid) ...  \n\n"
                    f"System Date:  {date.today()}  "
                ),
            )

        if payload.payment_type == 2:
            if not payload.customer_title.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Supplier Title:  (Cash Sales) Blank Supplier Title not allowed ...  ",
                )
            if not payload.address.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Supplier Address:  (Cash Sales) Blank Supplier Address not allowed ...  ",
                )
            if not payload.city_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid City ID:  (Cash Sales) Blank City ID not allowed ...  ",
                )
        else:
            self.get_supplier(payload.supplier_id)

    def save_document(self, payload: FinInvOrderSaveRequest) -> FinInvOrderSaveResponse:
        cfg = self.get_config()
        if not cfg.book_ok:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=cfg.book_message)

        payload.lines = [self._compute_line(line) for line in payload.lines]
        self._validate_save(payload, cfg)

        existing = None
        if payload.inv_id and payload.inv_id > 0:
            existing = self.repo.get_header(payload.inv_id, fiscal=cfg.fiscal, doc_type_id=cfg.doc_type_id)

        c_found = existing is not None
        serial_code = int(_vget(existing, "serial_no", "SERIAL_NO", default=0) or 0) if existing else 0

        if c_found:
            sys_status = int(_vget(existing, "sys_status", default=0) or 0)
            if sys_status == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Document/Voucher is posted, please re-enter ...",
                )

        line_outs = [
            FinInvOrderLineOut(
                serial_order=i,
                item_id=line.item_id,
                barcode_id=line.barcode_id,
                manual_id=line.manual_id,
                item_title=line.item_title,
                qty=line.qty,
                rate=line.rate,
                amount=line.amount,
                disc_per=line.disc_per,
                disc_amt=line.disc_amt,
                net_amt=line.net_amt,
            )
            for i, line in enumerate(payload.lines, start=1)
        ]
        totals = self._compute_totals(line_outs, payload.charges)

        stax_id = payload.stax_id.strip() or "Nil"
        if payload.payment_type == 0:
            supplier = self.get_supplier(payload.supplier_id)
            customer_title = supplier.vendor_title
            address = supplier.address
            stax_id = supplier.stax_id or stax_id
            city_id = supplier.city_id
            stax_type = 0 if supplier.registration == "Registered" else (1 if supplier.registration == "Un-Registered" else 2)
        else:
            customer_title = payload.customer_title
            address = payload.address
            city_id = payload.city_id
            stax_type = payload.stax_type

        try:
            if c_found and serial_code:
                self.repo.delete_detail(serial_code)

            if c_found:
                new_voucher_no = int(payload.inv_id)
                gl_voucher_id = int(_vget(existing, "gl_voucher_id", default=0) or 0)
                if payload.payment_type == 0:
                    gl_voucher_id = new_voucher_no
            else:
                new_voucher_no = self.repo.next_inv_id(self.legacy_uid)
                if new_voucher_no == 0:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zero Invoice ID is not Allowed ...")
                serial_code = self.repo.allocate_serial_no(self.legacy_uid)
                gl_voucher_id = new_voucher_no if payload.payment_type > 0 else 0

            self.repo.upsert_header(
                is_new=not c_found,
                serial_no=serial_code,
                inv_id=new_voucher_no,
                gl_voucher_id=gl_voucher_id,
                fiscal=cfg.fiscal,
                doc_type_id=cfg.doc_type_id,
                doc_date=payload.doc_date,
                supplier_id=payload.supplier_id,
                payment_type=payload.payment_type,
                stax_type=stax_type,
                gp_id=payload.gp_id,
                gp_time=payload.gp_time,
                cust_order=payload.cust_order,
                cust_order_date=payload.cust_order_date,
                sale_amt=totals.net_invoice,
                amount_rec=_money(payload.amount_rec),
                bal_amt=_money(payload.bal_amt),
                customer_title=customer_title,
                address=address,
                stax_id=stax_id,
                city_id=city_id,
                remarks=payload.remarks,
                discount_amt=_money(payload.charges.discount),
                claim_amt=_money(payload.charges.claim),
                other_ded_amt=_money(payload.charges.other_ded),
                loading_amt=_money(payload.charges.loading),
                carriage_amt=_money(payload.charges.carriage),
                other_charges_amt=_money(payload.charges.other_charges),
            )

            self.repo.delete_fin_ldgr_by_serial(serial_code)
            self.repo.delete_gl_lines(serial_code)

            for n_cnt, line in enumerate(payload.lines, start=1):
                self.repo.insert_detail_line(
                    {
                        "inv_id": new_voucher_no,
                        "serial_order": n_cnt,
                        "serial_no": serial_code,
                        "doc_date": payload.doc_date,
                        "item_id": line.item_id,
                        "qty": line.qty,
                        "rate": line.rate,
                        "sale_amt": line.amount,
                        "stax_rate": line.disc_per,
                        "stax_amt": line.disc_amt,
                        "total_amt": line.net_amt,
                    }
                )

            self.db.commit()
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        if c_found:
            if cfg.fiscal == 0:
                message = f"Document/PO Edited. No. {cfg.doc_abbr} {new_voucher_no}"
            else:
                message = f"Document/PO Edited. No. {cfg.doc_abbr} {cfg.fiscal}-{new_voucher_no}"
        else:
            if cfg.fiscal == 0:
                message = f"New Document/Purchase Order No. {new_voucher_no}"
            else:
                message = f"New Document/Purchase Order No. {cfg.doc_abbr} {cfg.fiscal}-{new_voucher_no}"

        return FinInvOrderSaveResponse(
            message=message,
            inv_id=new_voucher_no,
            serial_no=serial_code,
            doc_display=str(new_voucher_no),
        )

    def delete_document(self, inv_id: int) -> FinInvOrderDeleteResponse:
        cfg = self.get_config()
        header = self.repo.get_header(inv_id, fiscal=cfg.fiscal, doc_type_id=cfg.doc_type_id)
        if not header:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        serial_code = int(_vget(header, "serial_no", "SERIAL_NO"))
        try:
            self.repo.delete_detail(serial_code)
            self.repo.delete_header(inv_id, serial_code)
            self.repo.delete_fin_ldgr(inv_id, serial_code, cfg.doc_type_id)
            self.repo.delete_gl_lines(serial_code)
            self.repo.delete_gl_header(serial_code)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        return FinInvOrderDeleteResponse(
            message=f"Document ID: {inv_id}  has been deleted... ",
            inv_id=inv_id,
        )

    def next_id_preview(self) -> dict:
        return {"next_inv_id": self.repo.preview_next_inv_id()}
