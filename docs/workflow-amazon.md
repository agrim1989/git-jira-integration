# Amazon-like E-commerce Marketplace — Workflow Design

Generated for workflow-server. Use with `_agent/workflows/amazon-workflow.md` for full step-by-step execution.

---

## Problem statement

Design an Amazon-like e-commerce marketplace that provides a product catalog, search, shopping cart, checkout, order management, and user accounts. Optional: seller listings, inventory management, and product reviews. The system should be implementable as a REST API (e.g. FastAPI) with in-memory or SQLite persistence and user authentication.

## Functional requirements

- **User accounts:** Register and login; profile (email, name, address); auth (API key or JWT) for protected endpoints.
- **Product catalog:** List products with title, description, price, category, optional image URL; filter by category; search by text.
- **Shopping cart:** Add/remove/update items (product_id, quantity); list cart; cart is per user and persisted.
- **Checkout & orders:** Place order from cart (creates order, clears cart); order has items, total, status, created_at; list user's orders; get single order.
- **Optional:** Seller model (users can list products); inventory (stock count, decrement on order); product reviews (rating, comment); order status workflow (pending, shipped, delivered).

## Non-functional requirements

- REST API (FastAPI); clear API contracts; no hardcoded secrets; config via env.
- In-memory or SQLite persistence; logging, error handling, docstrings; PEP8-compliant code.
- Unit tests with FastAPI TestClient; tests must pass before PR.

## Architecture / design

- **Module layout:** e.g. `marketplace/` or `amazon/` with models, store (in-memory or SQLite), and API routes; `main.py` for FastAPI app.
- **Data:** User (id, email, name, created_at); Product (id, title, description, price, category_id, optional seller_id, stock); Category (id, name); CartItem (user_id, product_id, quantity); Order (id, user_id, total, status, created_at); OrderItem (order_id, product_id, quantity, price). Optional: Review (product_id, user_id, rating, comment, created_at).
- **API:** POST/GET /users/register, GET /users/me; GET /products (list, filter by category, search), GET /products/{id}; POST/GET/DELETE /cart, PATCH /cart/{product_id}; POST /orders (checkout), GET /orders, GET /orders/{id}. Auth: X-User-Id or API key for cart/orders.
- **Auth:** Simple header (X-User-Id) or JWT; middleware to resolve current user for cart and orders.

## Implementation plan

1. Set up FastAPI app and project structure (`marketplace/` or `amazon/`, `tests/`).
2. Implement user model and auth; registration and get profile endpoints.
3. Implement product and category models; product list (with category filter and optional search), get product by id.
4. Implement cart: add, list, update quantity, remove item; cart stored per user.
5. Implement checkout: create order from cart (order items, total), clear cart; list orders, get order by id.
6. Add validation, error handling, logging; requirements.txt and config.
7. Write unit tests for auth, products, cart, checkout, orders; run pytest until green.
8. Optional: seller listings, inventory decrement, reviews, order status transitions.

## Testing plan

- Unit tests: auth (missing/invalid returns 401); list products, get product, filter by category; add to cart, list cart, update/remove; checkout creates order and clears cart; list orders, get order; cannot access another user's cart/orders.
- Use FastAPI `TestClient`; target `tests/test_amazon.py` or `tests/test_marketplace.py`.
- Command: `pytest tests/test_amazon.py -v` (or test_marketplace.py). All tests must pass before commit and PR.

## Deployment plan

- Run locally: `uvicorn` with host/port from config; optional Dockerfile.
- Env: DB path or in-memory flag; secret key if JWT; no secrets in repo.

## Risks & mitigation

- Scope creep: deliver core (catalog, cart, checkout, orders) first; sellers, inventory, reviews as optional.
- Concurrency: for MVP, in-memory or SQLite is sufficient; add locking or proper DB for inventory later.

## Rollback strategy

- Feature developed on branch; if issues, do not merge PR; fix on branch or revert. No production deployment until PR is merged and verified.
