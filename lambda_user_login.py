"""
AWS Lambda function for user login authentication.

Handles POST requests from API Gateway, validates credentials,
and returns a JWT token on successful authentication.
"""

import hashlib
import hmac
import json
import logging
import os
import re
import time
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Configuration (set via Lambda environment variables)
# ---------------------------------------------------------------------------
JWT_SECRET = os.environ.get("JWT_SECRET", "default-secret-change-in-production")
JWT_EXPIRY_SECONDS = int(os.environ.get("JWT_EXPIRY_SECONDS", "3600"))

# ---------------------------------------------------------------------------
# Simulated user store (replace with DynamoDB / RDS in production)
# ---------------------------------------------------------------------------
USERS_DB: dict[str, dict] = {
    "admin@example.com": {
        "user_id": "u-001",
        "name": "Admin User",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
    },
    "user@example.com": {
        "user_id": "u-002",
        "name": "Regular User",
        "password_hash": hashlib.sha256("password456".encode()).hexdigest(),
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Content-Type": "application/json",
}


def _response(status_code: int, body: dict) -> dict:
    """Build a properly formatted API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }


def _validate_email(email: str) -> bool:
    """Basic email format validation."""
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def _create_jwt(user_id: str, email: str, name: str) -> str:
    """Create a simple JWT token (HS256).

    In production, use a library like PyJWT or AWS Cognito.
    """
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()

    now = int(time.time())
    payload = base64.urlsafe_b64encode(
        json.dumps({
            "sub": user_id,
            "email": email,
            "name": name,
            "iat": now,
            "exp": now + JWT_EXPIRY_SECONDS,
        }).encode()
    ).rstrip(b"=").decode()

    message = f"{header}.{payload}"
    signature = hmac.new(
        JWT_SECRET.encode(), message.encode(), hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

    return f"{header}.{payload}.{sig_b64}"


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------
def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda entry point for user login.

    Expects an API Gateway proxy event with a JSON body containing:
        - email (str): User's email address
        - password (str): User's password

    Returns:
        API Gateway response with JWT token or error message.
    """
    logger.info("Login request received")

    # Handle CORS preflight
    http_method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method", ""))
    if http_method == "OPTIONS":
        return _response(200, {"message": "OK"})

    # Parse request body
    body = event.get("body", "{}")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in request body")
            return _response(400, {"error": "Invalid JSON in request body"})

    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    # Input validation
    if not email or not password:
        return _response(400, {"error": "Email and password are required"})

    if not _validate_email(email):
        return _response(400, {"error": "Invalid email format"})

    # Authenticate
    user = USERS_DB.get(email)
    if not user:
        logger.info("Login failed: user not found (%s)", email)
        return _response(401, {"error": "Invalid email or password"})

    if user["password_hash"] != _hash_password(password):
        logger.info("Login failed: wrong password (%s)", email)
        return _response(401, {"error": "Invalid email or password"})

    # Success — generate token
    token = _create_jwt(user["user_id"], email, user["name"])
    logger.info("Login successful for user %s", user["user_id"])

    return _response(200, {
        "message": "Login successful",
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": email,
            "name": user["name"],
        },
    })
