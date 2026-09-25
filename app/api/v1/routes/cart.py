from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import (
    CartItemCreate,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
)


router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)


def get_or_create_cart(
    user_id: int,
    db: Session,
) -> Cart:
    cart = db.scalar(
        select(Cart).where(Cart.user_id == user_id)
    )

    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.flush()

    return cart


@router.post(
    "/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_cart(
    item_data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Make sure the product exists and is active
    product = db.get(Product, item_data.product_id)

    if product is None or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    cart = get_or_create_cart(current_user.id, db)

    # Check whether this product is already in the cart
    cart_item = db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_data.product_id,
        )
    )

    if cart_item:
        # Add to the existing quantity
        cart_item.quantity += item_data.quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
        )
        db.add(cart_item)

    db.commit()
    db.refresh(cart_item)

    return cart_item


@router.get(
    "",
    response_model=CartResponse,
)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = get_or_create_cart(current_user.id, db)

    db.commit()
    db.refresh(cart)

    items = db.scalars(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
        .order_by(CartItem.id)
    ).all()

    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "items": items,
    }


@router.patch(
    "/items/{product_id}",
    response_model=CartItemResponse,
)
def update_cart_item(
    product_id: int,
    item_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = db.scalar(
        select(Cart).where(Cart.user_id == current_user.id)
    )

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    cart_item = db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id,
        )
    )

    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    cart_item.quantity = item_data.quantity

    db.commit()
    db.refresh(cart_item)

    return cart_item


@router.delete(
    "/items/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_cart_item(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = db.scalar(
        select(Cart).where(Cart.user_id == current_user.id)
    )

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    cart_item = db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id,
        )
    )

    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    db.delete(cart_item)
    db.commit()

    return None