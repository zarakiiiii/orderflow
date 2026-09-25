from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    sku: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    sku: str
    price: Decimal
    is_active: bool

    model_config = {
        "from_attributes": True,
    }