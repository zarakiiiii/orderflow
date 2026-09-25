from pydantic import BaseModel, Field


class InventoryCreate(BaseModel):
    quantity: int = Field(ge=0)


class InventoryUpdate(BaseModel):
    quantity: int = Field(ge=0)


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    quantity: int

    model_config = {
        "from_attributes": True,
    }