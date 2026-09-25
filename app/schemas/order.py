from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    status: str
    total_amount: Decimal
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)