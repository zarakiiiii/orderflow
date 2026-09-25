from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    product_id: int
    quantity: int

    model_config = {
        "from_attributes": True,
    }


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: list[CartItemResponse]

    model_config = {
        "from_attributes": True,
    }