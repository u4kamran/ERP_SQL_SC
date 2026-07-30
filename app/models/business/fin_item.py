"""FIN_ITEM ORM model — legacy dbo.FIN_ITEM (59 columns)."""

from sqlalchemy import Float, Integer, SmallInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DECIMAL


class BusinessBase(DeclarativeBase):
    pass


# SQL Server money maps to DECIMAL(19,4)
Money = DECIMAL(19, 4)


class FinItem(BusinessBase):
    """Inventory / finance item master (VB6 legacy table)."""

    __tablename__ = "FIN_ITEM"
    __table_args__ = {"schema": "dbo"}

    ITEM_ID: Mapped[float] = mapped_column(Float, primary_key=True)
    ITEM_TITLE: Mapped[str | None] = mapped_column(String(100))
    ITEM_SHORT: Mapped[str | None] = mapped_column(String(20))
    AC_LEVEL: Mapped[int | None] = mapped_column(SmallInteger)
    ED_STATUS: Mapped[int | None] = mapped_column(SmallInteger)
    ITEM_OEM: Mapped[str | None] = mapped_column(String(20))
    manualid: Mapped[int] = mapped_column(Integer, nullable=False)
    barcodeid: Mapped[str | None] = mapped_column(String(50))
    UOM_ID: Mapped[int | None] = mapped_column(SmallInteger)
    COUNTRY_ID: Mapped[int | None] = mapped_column(SmallInteger)
    TNOT: Mapped[int | None] = mapped_column(SmallInteger)
    OQTY: Mapped[float | None] = mapped_column(Money)
    OAMT: Mapped[float | None] = mapped_column(Money)
    CQTY: Mapped[float | None] = mapped_column(Money)
    CAMT: Mapped[float | None] = mapped_column(Money)
    avg_cost: Mapped[float | None] = mapped_column(Money)
    Mr_Cost: Mapped[float | None] = mapped_column(Money)
    ITEM_NATURE: Mapped[int | None] = mapped_column(SmallInteger)
    MIN_LEVEL: Mapped[float | None] = mapped_column(Float)
    MAX_LEVEL: Mapped[float | None] = mapped_column(Float)
    RO_QTY: Mapped[float | None] = mapped_column(Float)
    CRITICAL_LEVEL: Mapped[float | None] = mapped_column(Float)
    VISACARD_RATE: Mapped[float | None] = mapped_column(Money)
    SALES_RATE: Mapped[float | None] = mapped_column(Money)
    COST_RATE: Mapped[float | None] = mapped_column(Money)
    DISC_P1: Mapped[float | None] = mapped_column(Money)
    DISC_P2: Mapped[float | None] = mapped_column(Money)
    DISC_P3: Mapped[float | None] = mapped_column(Money)
    DISC_P4: Mapped[float | None] = mapped_column(Money)
    GL_SALES_ID: Mapped[int | None] = mapped_column(Integer)
    GL_PUR_ID: Mapped[int | None] = mapped_column(Integer)
    GL_CONS_ID: Mapped[int | None] = mapped_column(Integer)
    GL_DISC_ID: Mapped[int | None] = mapped_column(Integer)
    GL_STAX_ID: Mapped[int | None] = mapped_column(Integer)
    STAX_REG: Mapped[float | None] = mapped_column(Money)
    STAX_UNREG: Mapped[float | None] = mapped_column(Money)
    REMARKS: Mapped[str | None] = mapped_column(String(50))
    cprocess_id: Mapped[int | None] = mapped_column(Integer)
    qtycdebit: Mapped[float | None] = mapped_column(Money)
    qtyccredit: Mapped[float | None] = mapped_column(Money)
    amtcdebit: Mapped[float | None] = mapped_column(Money)
    amtccredit: Mapped[float | None] = mapped_column(Money)
    QTYTCBAL: Mapped[float | None] = mapped_column(Money)
    amttcbal: Mapped[float | None] = mapped_column(Money)
    qtynetbal: Mapped[float | None] = mapped_column(Money)
    amtnetbal: Mapped[float | None] = mapped_column(Money)
    qtynetclosing: Mapped[float | None] = mapped_column(Money)
    amtnetclosing: Mapped[float | None] = mapped_column(Money)
    co_id: Mapped[int | None] = mapped_column(SmallInteger)
    OQTY1: Mapped[float | None] = mapped_column(Money)
    OAMT1: Mapped[float | None] = mapped_column(Money)
    CQTY1: Mapped[float | None] = mapped_column(Money)
    CAMT1: Mapped[float | None] = mapped_column(Money)
    TNOT1: Mapped[int | None] = mapped_column(SmallInteger)
    MIN_LEVEL1: Mapped[float | None] = mapped_column(Float)
    MAX_LEVEL1: Mapped[float | None] = mapped_column(Float)
    RO_QTY1: Mapped[float | None] = mapped_column(Float)
    CRITICAL_LEVEL1: Mapped[float | None] = mapped_column(Float)
    BARCODEID_WS: Mapped[str | None] = mapped_column(String(50))
