from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_role
from app.core.database import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse

import json
from app.core.redis import redis_client


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    existing_product = db.scalar(
        select(Product).where(Product.sku == product_data.sku)
    )

    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SKU already exists",
        )

    product = Product(
        name=product_data.name,
        description=product_data.description,
        sku=product_data.sku,
        price=product_data.price,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    redis_client.delete("products:list")

    return product


@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products(
    db: Session = Depends(get_db),
):
    cached_products = redis_client.get("products:list")

    if cached_products:
        return json.loads(cached_products)

    products = db.scalars(
        select(Product)
        .where(Product.is_active == True)
        .order_by(Product.id)
    ).all()

    products_data = [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "sku": product.sku,
            "price": str(product.price),
            "is_active": product.is_active,
        }
        for product in products
    ]

    redis_client.set(
        "products:list",
        json.dumps(products_data),
        ex=60,
    )

    return products_data


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product