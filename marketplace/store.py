"""In-memory store for marketplace. KAN-81."""
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class User:
    user_id: str
    email: str
    name: str
    created_at: datetime


@dataclass
class Category:
    category_id: str
    name: str


@dataclass
class Product:
    product_id: str
    title: str
    description: str
    price: float
    category_id: str
    created_at: datetime


@dataclass
class CartItem:
    user_id: str
    product_id: str
    quantity: int


@dataclass
class OrderItem:
    order_id: str
    product_id: str
    title: str
    quantity: int
    price: float
    subtotal: float


@dataclass
class Order:
    order_id: str
    user_id: str
    total: float
    status: str
    created_at: datetime
    items: list[OrderItem] = field(default_factory=list)


class Store:
    """In-memory marketplace store."""

    def __init__(self):
        self._users: dict[str, User] = {}
        self._categories: dict[str, Category] = {}
        self._products: dict[str, Product] = {}
        self._cart: dict[tuple[str, str], int] = {}  # (user_id, product_id) -> quantity
        self._orders: dict[str, Order] = {}
        self._order_ids: list[str] = []
        self._seed_data()

    def _seed_data(self) -> None:
        """Seed categories and sample products."""
        c1 = Category(category_id="cat-1", name="Electronics")
        c2 = Category(category_id="cat-2", name="Books")
        self._categories[c1.category_id] = c1
        self._categories[c2.category_id] = c2
        for p in [
            Product("p1", "Widget A", "A useful widget", 19.99, "cat-1", datetime.utcnow()),
            Product("p2", "Widget B", "Another widget", 29.99, "cat-1", datetime.utcnow()),
            Product("p3", "Book X", "A good read", 9.99, "cat-2", datetime.utcnow()),
        ]:
            self._products[p.product_id] = p
        logger.info("Store seeded with categories and products")

    def create_user(self, email: str, name: str) -> User:
        """Register a new user."""
        user_id = f"user-{secrets.token_hex(8)}"
        user = User(user_id=user_id, email=email, name=name, created_at=datetime.utcnow())
        self._users[user_id] = user
        return user

    def get_user(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_product(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    def get_category(self, category_id: str) -> Category | None:
        return self._categories.get(category_id)

    def list_products(self, category_id: str | None = None, search: str | None = None) -> list[Product]:
        """List products, optionally filter by category or search in title/description."""
        out = list(self._products.values())
        if category_id:
            out = [p for p in out if p.category_id == category_id]
        if search:
            q = search.lower()
            out = [p for p in out if q in p.title.lower() or q in p.description.lower()]
        return sorted(out, key=lambda p: p.product_id)

    def cart_add(self, user_id: str, product_id: str, quantity: int) -> None:
        """Add or update cart item."""
        if self.get_product(product_id) is None:
            raise ValueError("Product not found")
        key = (user_id, product_id)
        self._cart[key] = self._cart.get(key, 0) + quantity
        if self._cart[key] <= 0:
            del self._cart[key]

    def cart_set(self, user_id: str, product_id: str, quantity: int) -> None:
        """Set cart item quantity (0 to remove)."""
        if self.get_product(product_id) is None:
            raise ValueError("Product not found")
        key = (user_id, product_id)
        if quantity <= 0:
            self._cart.pop(key, None)
        else:
            self._cart[key] = quantity

    def cart_remove(self, user_id: str, product_id: str) -> None:
        self._cart.pop((user_id, product_id), None)

    def cart_list(self, user_id: str) -> list[tuple[Product, int]]:
        """Return list of (product, quantity) for user's cart."""
        out = []
        for (uid, pid), qty in self._cart.items():
            if uid == user_id and qty > 0:
                p = self._products.get(pid)
                if p:
                    out.append((p, qty))
        return out

    def checkout(self, user_id: str) -> Order:
        """Create order from cart and clear cart."""
        items_data = self.cart_list(user_id)
        if not items_data:
            raise ValueError("Cart is empty")
        order_id = f"ord-{secrets.token_hex(8)}"
        total = 0.0
        order_items: list[OrderItem] = []
        for product, qty in items_data:
            subtotal = round(product.price * qty, 2)
            total += subtotal
            order_items.append(
                OrderItem(order_id=order_id, product_id=product.product_id, title=product.title, quantity=qty, price=product.price, subtotal=subtotal)
            )
        total = round(total, 2)
        order = Order(order_id=order_id, user_id=user_id, total=total, status="pending", created_at=datetime.utcnow(), items=order_items)
        self._orders[order_id] = order
        self._order_ids.append(order_id)
        for (uid, pid), _ in list(self._cart.items()):
            if uid == user_id:
                del self._cart[(uid, pid)]
        return order

    def list_orders(self, user_id: str) -> list[Order]:
        """List orders for user."""
        return [o for o in self._orders.values() if o.user_id == user_id]

    def get_order(self, order_id: str, user_id: str) -> Order | None:
        o = self._orders.get(order_id)
        if o and o.user_id == user_id:
            return o
        return None


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


def reset_store_for_testing() -> None:
    """Reset store for tests."""
    global _store
    _store = Store()
