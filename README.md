# Asynchronous Rate Limiter & API Gateway

A high-throughput, production-ready L7 API Gateway and middleware constructed with **Python (FastAPI)**, **Redis**, and atomic **Lua scripting**. Designed to enforce granular, route-level rate limiting using the **Token Bucket Algorithm** to protect downstream microservices against traffic spikes, scraping, and brute-force attacks.

---

## Key Features

* **Asynchronous L7 Gateway:** Non-blocking I/O powered by FastAPI and `uvicorn` delivering ultra-low middleware overhead ($p99 < 2\text{ms}$).
* **Atomic Token Bucket via Redis & Lua:** Solves race conditions in distributed environments by executing token deduction and refill logic atomically inside Redis.
* **Route-Aware Rate Limiting:** Enforces granular limits based on endpoint sensitivity:
  * `POST /api/v1/login`: Strict capacity ($5\text{ tokens}$) to defend against brute-force bot attacks.
  * `GET /api/v1/data`: Generous capacity ($100\text{ tokens}$) to handle rapid user browsing.
* **Standardized HTTP Headers:** Fully compliant with RFC rate-limiting standards (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`).
* **Containerized Deployment:** Fully orchestrated using Docker Compose for reproducible local testing and production readiness.

---

## Tech Stack

* **Language:** Python 3.11+
* **Framework:** FastAPI / AsyncIO
* **In-Memory Store:** Redis
* **Scripting:** Lua
* **Infrastructure:** Docker & Docker Compose
* **Testing Client:** HTTPX / cURL

---

## System Architecture
