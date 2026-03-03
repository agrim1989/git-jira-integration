"""Pydantic models for marketplace API. KAN-81."""
from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    """Request to register a user."""

    email: str
    name: str


class UserResponse(BaseModel):
    """User profile response."""

    user_id: str
    email: str
    name: str
    created_at: datetime


class ProductResponse(BaseModel):
    """Product in catalog."""

    product_id: str
    title: str
    description: str
    price: float
    category_id: str
    category_name: str


class CartItemResponse(BaseModel):
    """Cart item with product details."""

    product_id: str
    title: str
    quantity: int
    price: float
    subtotal: float


class CartAdd(BaseModel):
    """Add or update cart item."""

    product_id: str
    quantity: int = 1


class OrderItemResponse(BaseModel):
    """Order line item."""

    product_id: str
    title: str
    quantity: int
    price: float
    subtotal: float


class OrderResponse(BaseModel):
    """Order summary."""

    order_id: str
    user_id: str
    total: float
    status: str
    created_at: datetime
    items: list[OrderItemResponse]
