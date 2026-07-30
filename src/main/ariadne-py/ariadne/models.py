from pydantic import BaseModel, Field, model_validator


class BOMEntry(BaseModel):
    item_number: int
    quantity: int
    reference_designator: str
    part_value: str | None = None
    package: str | None = None
    manufacturer: str | None = None
    manufacturer_order_code: str | None = None
    supplier: str | None = None
    supplier_order_code: str | None = None
    notes: str | None = None
    mounting_type: str = "SMT"
    designator_code: str | None = None
    eec_category_id: int | None = None


class Device(BaseModel):
    brand: str = ""
    model_name: str = ""
    manufacturer: str = ""
    year_of_production: int | None = None
    notes: str | None = None


class Material(BaseModel):
    material_name: str
    casrn: str | None = None
    category: str = "element"


class ComponentMaterial(BaseModel):
    bom_entry_ref: str
    material: Material
    mass_mg: float = 0.0
    note: str | None = None
    source_mdf: str | None = None


class ImportResult(BaseModel):
    total_rows: int = 0
    imported_rows: int = 0
    failed_rows: int = 0
    success: bool = True
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def compute_success(self):
        self.success = self.failed_rows == 0
        return self
