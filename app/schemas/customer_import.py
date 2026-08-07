"""Schemas for reviewed OCR customer imports."""

from pydantic import BaseModel, Field, field_validator


class CustomerImportRecord(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    mobile: str = Field(..., min_length=10, max_length=30)
    original_address: str = Field("", max_length=500)
    english_address: str = Field("", max_length=500)

    @field_validator(
        "name",
        "mobile",
        "original_address",
        "english_address",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class CustomerImportFinalizeRequest(BaseModel):
    records: list[CustomerImportRecord] = Field(..., min_length=1, max_length=200)


class CustomerImportFinalizeResponse(BaseModel):
    received: int
    created: int
    skipped_existing: int
    created_ids: list[int] = Field(default_factory=list)
    existing_mobiles: list[str] = Field(default_factory=list)
    message: str


class CustomerImportExtractedRecord(BaseModel):
    source_row: int | None = None
    name: str = ""
    mobile: str = ""
    original_address: str = ""
    english_address: str = ""
    rider_name: str = ""
    notes: str = ""


class CustomerImportExtractResponse(BaseModel):
    records: list[CustomerImportExtractedRecord] = Field(default_factory=list)
    model: str
    warnings: list[str] = Field(default_factory=list)
