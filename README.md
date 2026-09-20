# High-Throughput Asynchronous Rate Limiter & API Gateway

An asynchronous L7 API Gateway and Rate Limiting engine built with **Python (FastAPI)**, **Redis**, **Lua**, and **Docker**. Designed to prevent service outages caused by traffic bursts, brute-force attacks, and API abuse.

## Architecture & Features

- **Token Bucket Algorithm:** Supports bursting traffic up to a configurable capacity while enforcing a smooth steady-state request rate.
- **Atomic Concurrency Guarantee:** Uses **Lua scripts** executed inside Redis memory space to perform atomicity checks, eliminating race conditions across multiple concurrent requests.
- **Asynchronous I/O:** Built on non-blocking async handlers (`FastAPI` + `redis-py` async pool) to ensure latency overhead remains under **2ms**.
- **Standardized HTTP Headers:** Injects `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After` headers according to RFC standards.

## Tech Stack
- **Language:** Python 3.11 (FastAPI, Uvicorn)
- **Database:** Redis (In-Memory Data Store)
- **Scripting:** Lua (Embedded Redis Execution)
- **Containerization:** Docker, Docker Compose

## Quickstart & Running Locally

1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/rate-limiter-api-gateway.git](https://github.com/YOUR_USERNAME/rate-limiter-api-gateway.git)
   cd rate-limiter-api-gateway
