import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
import redis.asyncio as redis
import httpx

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Configuration: Rate Limiting Parameters
CAPACITY = 10       # Max burst capacity
REFILL_RATE = 2.0   # Refill 2 tokens every second

redis_client = None
rate_limit_lua = None
http_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, rate_limit_lua, http_client
    
    # Initialize async Redis pool & HTTP client
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    http_client = httpx.AsyncClient()
    
    # Load Lua script into Redis script cache
    script_path = os.path.join(os.path.dirname(__file__), "../scripts/token_bucket.lua")
    with open(script_path, "r") as f:
        lua_code = f.read()
    rate_limit_lua = redis_client.register_script(lua_code)
    
    yield
    
    # Cleanup resources
    await redis_client.close()
    await http_client.aclose()

app = FastAPI(title="Async Rate Limiting API Gateway", lifespan=lifespan)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Extract client identification (Header API key or IP address)
    api_key = request.headers.get("X-API-Key")
    client_id = api_key if api_key else (request.client.host if request.client else "unknown")
    redis_key = f"rate_limit:{client_id}"
    
    current_time = time.time()
    
    # Execute atomic Redis Token Bucket operation
    allowed, remaining_tokens = await rate_limit_lua(
        keys=[redis_key],
        args=[CAPACITY, REFILL_RATE, current_time, 1]
    )
    
    # Block excess requests immediately
    if not allowed:
        return Response(
            content='{"error": "Too Many Requests", "message": "Rate limit exceeded. Try again later."}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json",
            headers={
                "X-RateLimit-Limit": str(CAPACITY),
                "X-RateLimit-Remaining": "0",
                "Retry-After": "1"
            }
        )
    
    # Process allowed request
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(CAPACITY)
    response.headers["X-RateLimit-Remaining"] = str(remaining_tokens)
    return response

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "API Gateway"}

@app.get("/api/v1/data")
async def sample_endpoint():
    return {
        "status": "success",
        "data": "This request passed through the asynchronous rate-limited API gateway."
    }
