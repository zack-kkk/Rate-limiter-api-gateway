import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
import redis.asyncio as redis
import httpx

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# --------------------------------------------------------------------------
# Route-Specific Rate Limit Configurations
# Format: "path_prefix": {"capacity": max_burst, "refill_rate": tokens_per_sec}
# --------------------------------------------------------------------------
ROUTE_LIMITS = {
    "/api/v1/login": {"capacity": 5, "refill_rate": 0.2},     # Very strict: 5 burst, 1 token every 5 sec
    "/api/v1/checkout": {"capacity": 3, "refill_rate": 0.1},  # Strict: 3 burst, 1 token every 10 sec
    "/api/v1/data": {"capacity": 100, "refill_rate": 10.0},   # Generous: 100 burst, 10 tokens per sec
}

# Default fallback limit for unconfigured routes
DEFAULT_LIMIT = {"capacity": 20, "refill_rate": 2.0}

redis_client = None
rate_limit_lua = None
http_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, rate_limit_lua, http_client
    
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    http_client = httpx.AsyncClient()
    
    script_path = os.path.join(os.path.dirname(__file__), "../scripts/token_bucket.lua")
    with open(script_path, "r") as f:
        lua_code = f.read()
    rate_limit_lua = redis_client.register_script(lua_code)
    
    yield
    
    await redis_client.close()
    await http_client.aclose()

app = FastAPI(title="Route-Aware Async API Gateway", lifespan=lifespan)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path

    # Skip health checks from rate limiting
    if path == "/health":
        return await call_next(request)

    # 1. Determine rate limit configuration based on request path
    config = DEFAULT_LIMIT
    for route_prefix, route_config in ROUTE_LIMITS.items():
        if path.startswith(route_prefix):
            config = route_config
            break

    capacity = config["capacity"]
    refill_rate = config["refill_rate"]

    # 2. Build unique Redis key incorporating IP/API-Key AND route
    api_key = request.headers.get("X-API-Key")
    client_id = api_key if api_key else (request.client.host if request.client else "unknown")
    
    # Key isolated per route: e.g., "rate_limit:127.0.0.1:/api/v1/login"
    redis_key = f"rate_limit:{client_id}:{path}"
    
    current_time = time.time()
    
    # 3. Execute atomic Redis Lua script with route-specific capacity/refill
    allowed, remaining_tokens = await rate_limit_lua(
        keys=[redis_key],
        args=[capacity, refill_rate, current_time, 1]
    )
    
    # Block excess requests
    if not allowed:
        return Response(
            content='{"error": "Too Many Requests", "message": "Rate limit exceeded for this endpoint."}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json",
            headers={
                "X-RateLimit-Limit": str(capacity),
                "X-RateLimit-Remaining": "0",
                "Retry-After": str(int(1 / refill_rate))
            }
        )
    
    # Process request
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(capacity)
    response.headers["X-RateLimit-Remaining"] = str(remaining_tokens)
    return response


# --- Sample API Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/login")
async def login_endpoint():
    return {"status": "success", "message": "Login attempt processed"}

@app.get("/api/v1/data")
async def data_endpoint():
    return {"status": "success", "data": "Browsing product data"}
