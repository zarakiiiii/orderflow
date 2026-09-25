from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.cart import Cart, CartItem
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderResponse


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def checkout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find the user's cart
    cart = db.scalar(
        select(Cart).where(
            Cart.user_id == current_user.id
        )
    )

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    # Get all cart items
    cart_items = db.scalars(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    try:
        total_amount = Decimal("0")
        order_items_data = []

        for cart_item in cart_items:
            product = db.get(Product, cart_item.product_id)

            if product is None or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {cart_item.product_id} is unavailable",
                )

            inventory = db.scalar(
                select(Inventory)
                .where(
                Inventory.product_id == cart_item.product_id
                )
                .with_for_update()
            )

            if inventory is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Inventory not found for product {cart_item.product_id}",
                )

            if inventory.quantity < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Insufficient stock for product "
                        f"{cart_item.product_id}"
                    ),
                )

            item_total = (
                product.price * cart_item.quantity
            )

            total_amount += item_total

            order_items_data.append(
                {
                    "product_id": product.id,
                    "quantity": cart_item.quantity,
                    "unit_price": product.price,
                    "inventory": inventory,
                }
            )

        # Create the order
        order = Order(
            user_id=current_user.id,
            status="confirmed",
            total_amount=total_amount,
        )

        db.add(order)
        db.flush()

        # Create order items and deduct inventory
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
            )

            db.add(order_item)

            item_data["inventory"].quantity -= item_data["quantity"]

        # Remove everything from the cart
        for cart_item in cart_items:
            db.delete(cart_item)

        db.commit()

        # Load the order items before returning
        order_items = db.scalars(
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
            .order_by(OrderItem.id)
        ).all()

        return {
            "id": order.id,
            "status": order.status,
            "total_amount": order.total_amount,
            "items": order_items,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Checkout failed",
        )