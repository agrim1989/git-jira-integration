"""Amazon-like marketplace API. KAN-81."""
import logging
from fastapi import FastAPI, Header, HTTPException

from marketplace.models import (
    CartAdd,
    CartItemResponse,
    OrderResponse,
    OrderItemResponse,
    ProductResponse,
    UserCreate,
    UserResponse,
)
from marketplace.store import get_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_HEADER = "x-user-id"


def get_user_id(x_user_id: str | None = Header(default=None, alias=USER_HEADER)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    store = get_store()
    if not store.get_user(x_user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return x_user_id


app = FastAPI(
    title="Marketplace API (KAN-81)",
    description="Product catalog, cart, checkout, orders.",
)


@app.post("/users/register", response_model=UserResponse)
def register(body: UserCreate):
    """Register a new user."""
    store = get_store()
    user = store.create_user(body.email, body.name)
    return UserResponse(user_id=user.user_id, email=user.email, name=user.name, created_at=user.created_at)


@app.get("/users/me", response_model=UserResponse)
def get_me(user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    user = store.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(user_id=user.user_id, email=user.email, name=user.name, created_at=user.created_at)


@app.get("/products", response_model=list[ProductResponse])
def list_products(category_id: str | None = None, search: str | None = None):
    """List products; optional filter by category_id or search text."""
    store = get_store()
    products = store.list_products(category_id=category_id, search=search)
    return [
        ProductResponse(
            product_id=p.product_id,
            title=p.title,
            description=p.description,
            price=p.price,
            category_id=p.category_id,
            category_name=store.get_category(p.category_id).name if store.get_category(p.category_id) else "",
        )
        for p in products
    ]


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str):
    store = get_store()
    p = store.get_product(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    cat = store.get_category(p.category_id)
    return ProductResponse(
        product_id=p.product_id,
        title=p.title,
        description=p.description,
        price=p.price,
        category_id=p.category_id,
        category_name=cat.name if cat else "",
    )


@app.post("/cart")
def cart_add(body: CartAdd, user_id: str = Header(..., alias=USER_HEADER)):
    """Add to cart or increase quantity."""
    store = get_store()
    try:
        store.cart_add(user_id, body.product_id, body.quantity)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"added": body.product_id, "quantity": body.quantity}


@app.get("/cart", response_model=list[CartItemResponse])
def cart_list(user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    items = store.cart_list(user_id)
    return [
        CartItemResponse(product_id=p.product_id, title=p.title, quantity=qty, price=p.price, subtotal=round(p.price * qty, 2))
        for p, qty in items
    ]


@app.patch("/cart/{product_id}")
def cart_update(product_id: str, quantity: int, user_id: str = Header(..., alias=USER_HEADER)):
    """Set quantity for product in cart (0 to remove)."""
    store = get_store()
    try:
        store.cart_set(user_id, product_id, quantity)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"product_id": product_id, "quantity": quantity}


@app.delete("/cart/{product_id}")
def cart_remove(product_id: str, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    store.cart_remove(user_id, product_id)
    return {"removed": product_id}


@app.post("/orders", response_model=OrderResponse)
def checkout(user_id: str = Header(..., alias=USER_HEADER)):
    """Create order from cart and clear cart."""
    store = get_store()
    try:
        order = store.checkout(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return OrderResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        total=order.total,
        status=order.status,
        created_at=order.created_at,
        items=[
            OrderItemResponse(product_id=i.product_id, title=i.title, quantity=i.quantity, price=i.price, subtotal=i.subtotal)
            for i in order.items
        ],
    )


@app.get("/orders", response_model=list[OrderResponse])
def list_orders(user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    orders = store.list_orders(user_id)
    return [
        OrderResponse(
            order_id=o.order_id,
            user_id=o.user_id,
            total=o.total,
            status=o.status,
            created_at=o.created_at,
            items=[
                OrderItemResponse(product_id=i.product_id, title=i.title, quantity=i.quantity, price=i.price, subtotal=i.subtotal)
                for i in o.items
            ],
        )
        for o in orders
    ]


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    order = store.get_order(order_id, user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        total=order.total,
        status=order.status,
        created_at=order.created_at,
        items=[
            OrderItemResponse(product_id=i.product_id, title=i.title, quantity=i.quantity, price=i.price, subtotal=i.subtotal)
            for i in order.items
        ],
    )
