# OrderFlow — Distributed Order Processing Backend

A production-oriented order processing backend built with **FastAPI, PostgreSQL, Redis, and Docker**.

OrderFlow focuses on reliable checkout and inventory processing, with **database transactions, row-level locking, idempotency, Redis caching, rate limiting, and asynchronous event processing using Redis Streams**.

---

## Architecture

flowchart LR
    Client --> API[FastAPI API]

    API --> PostgreSQL[(PostgreSQL)]
    API --> Redis[(Redis)]

    API --> Stream[Redis Streams]
    Stream --> Worker[Order Worker]

    PostgreSQL --> API
    Redis --> API

### Core flow

Client
  │
  ▼
FastAPI
  │
  ├──────────────► PostgreSQL
  │                    │
  │                    └── Users / Products / Inventory
  │                        Cart / Orders / Idempotency
  │
  ├──────────────► Redis
  │                    ├── Product Cache
  │                    └── Rate Limiting
  │
  └──────────────► Redis Streams
                       │
                       ▼
                  Order Worker




## Key Features

### Authentication & Authorization

* JWT-based authentication
* Password hashing with bcrypt
* Role-based access control
* Admin and customer roles

### Product & Inventory Management

* Product creation and retrieval
* Unique SKU enforcement
* Inventory management
* Active/inactive products

### Shopping Cart

* User-specific carts
* Add, update, and remove cart items
* Automatic quantity accumulation for existing products

### Reliable Checkout

Checkout is implemented as a database transaction that:

1. Reads the user's cart
2. Validates products
3. Locks inventory rows using PostgreSQL row-level locking
4. Verifies sufficient stock
5. Creates the order
6. Creates order items
7. Deducts inventory
8. Clears the cart
9. Commits the transaction

This prevents concurrent checkouts from overselling inventory.

### Idempotent Checkout

Checkout requires an `Idempotency-Key` header.

Repeated requests with the same key for the same user return the existing order instead of creating a duplicate order.


POST /api/v1/orders/checkout
Idempotency-Key: checkout-12345


This protects against duplicate orders caused by retries or repeated client requests.

### Redis Caching

Product listings are cached in Redis:


products:list


The cache expires after 60 seconds and is invalidated when a product is created.

### Rate Limiting

Requests are rate-limited using Redis-backed counters.

Current configuration:


100 requests / minute / IP


Excess requests receive:


429 Too Many Requests


### Asynchronous Order Processing

After a successful checkout, an `order.created` event is published to a Redis Stream.


Checkout
   │
   ▼
PostgreSQL COMMIT
   │
   ▼
Redis Stream
   │
   ▼
Consumer Group
   │
   ▼
Order Worker
   │
   ▼
Process Event
   │
   ▼
XACK


The worker uses Redis consumer groups and acknowledges successfully processed messages with `XACK`.



## Tech Stack

| Technology     | Purpose                                   |
| -------------- | ----------------------------------------- |
| Python         | Backend language                          |
| FastAPI        | REST API framework                        |
| PostgreSQL     | Primary relational database               |
| SQLAlchemy     | ORM and database access                   |
| Alembic        | Database migrations                       |
| Redis          | Caching, rate limiting, message streaming |
| Redis Streams  | Asynchronous event processing             |
| JWT            | Authentication                            |
| bcrypt         | Password hashing                          |
| Pytest         | Automated testing                         |
| Docker         | Containerization                          |
| Docker Compose | Local service orchestration               |



## Project Structure


orderflow/
│
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── v1/
│   │       └── routes/
│   │           ├── auth.py
│   │           ├── admin.py
│   │           ├── products.py
│   │           ├── inventory.py
│   │           ├── cart.py
│   │           └── orders.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── logging_config.py
│   │   ├── queue.py
│   │   ├── rate_limit.py
│   │   ├── redis.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── cart.py
│   │   ├── order.py
│   │   └── idempotency.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── cart.py
│   │   └── order.py
│   │
│   ├── workers/
│   │   └── order_worker.py
│   │
│   └── main.py
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_rbac.py
│   ├── test_products.py
│   ├── test_cart.py
│   ├── test_orders.py
│   └── test_rate_limit.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md




## API Endpoints

### Authentication

| Method | Endpoint                | Description                  |
| ------ | ----------------------- | ---------------------------- |
| POST   | `/api/v1/auth/register` | Register a user              |
| POST   | `/api/v1/auth/login`    | Authenticate and receive JWT |

### Products

| Method | Endpoint                        | Description              |
| ------ | ------------------------------- | ------------------------ |
| GET    | `/api/v1/products`              | List active products     |
| GET    | `/api/v1/products/{product_id}` | Get a product            |
| POST   | `/api/v1/products`              | Create a product (admin) |

### Inventory

| Method | Endpoint                         | Description             |
| ------ | -------------------------------- | ----------------------- |
| GET    | `/api/v1/inventory/{product_id}` | Get inventory           |
| POST   | `/api/v1/inventory`              | Create/update inventory |

### Cart

| Method | Endpoint                          | Description             |
| ------ | --------------------------------- | ----------------------- |
| GET    | `/api/v1/cart`                    | Get current user's cart |
| POST   | `/api/v1/cart/items`              | Add an item             |
| PATCH  | `/api/v1/cart/items/{product_id}` | Update quantity         |
| DELETE | `/api/v1/cart/items/{product_id}` | Remove an item          |

### Orders

| Method | Endpoint                  | Description           |
| ------ | ------------------------- | --------------------- |
| POST   | `/api/v1/orders/checkout` | Checkout current cart |

### Health


GET /health


Response:


{
  "status": "ok",
  "service": "orderflow"
}




## Concurrency Control

A key part of OrderFlow is preventing inventory overselling during concurrent checkouts.

During checkout, inventory rows are locked using PostgreSQL:


select(Inventory).where(
    Inventory.product_id == product_id
).with_for_update()


This means concurrent transactions attempting to modify the same inventory row cannot both proceed as though the stock were available.

The transaction then:


Lock inventory
      ↓
Check stock
      ↓
Create order
      ↓
Deduct inventory
      ↓
Commit


If an error occurs, the transaction is rolled back.



## Idempotency

Checkout uses a dedicated idempotency table with a unique constraint on:


(user_id, idempotency_key)


The first request creates the order and associates the key with it.

A repeated request with the same key returns the previously created order.

This prevents:


Client retry
     │
     ├── Request 1 → Order #101
     │
     └── Request 2 → Order #101


instead of accidentally creating:


Order #101
Order #102  ❌




## Redis Usage

Redis is used for three purposes:

### 1. Product caching


products:list


with a 60-second TTL.

### 2. Rate limiting


rate_limit:{ip}:{window}


using Redis atomic increments.

### 3. Asynchronous events


order_events


using Redis Streams and consumer groups.

This demonstrates using Redis for both **performance optimization** and **distributed event processing**.



## Running Locally

### Prerequisites

* Python 3.13+
* Docker Desktop
* Docker Compose

### Start services


docker compose up -d


This starts:


PostgreSQL
Redis
FastAPI
Order Worker


### Check containers


docker compose ps


### API

The API runs at:


http://localhost:8000


Interactive API documentation:


http://localhost:8000/docs


### Health check


curl http://localhost:8000/health


### Worker logs


docker compose logs worker


### API logs


docker compose logs api




## Database Migrations

Create a migration:


alembic revision --autogenerate -m "migration message"


Apply migrations:


alembic upgrade head




## Testing

The project contains automated tests covering:

* User registration
* Authentication
* Invalid login
* RBAC
* Product creation
* Product retrieval
* Duplicate SKUs
* Cart operations
* Checkout
* Inventory deduction
* Inventory validation
* Cart clearing
* Idempotency
* Rate limiting

Current test suite:


25 passed


Run:


pytest


---

## Docker Architecture

Docker Compose runs four services:


┌───────────────┐
│    FastAPI    │
│      API      │
└───────┬───────┘
        │
   ┌────┴─────┐
   ▼          ▼
┌───────┐  ┌───────┐
│Postgres│  │ Redis │
└───────┘  └───┬───┘
                │
                ▼
          ┌──────────┐
          │  Worker  │
          └──────────┘


All application services communicate over the Docker Compose network using service names rather than `localhost`.

---

## Engineering Concepts Demonstrated

OrderFlow was designed to demonstrate practical backend engineering concepts rather than simply CRUD operations:

* REST API design
* Authentication and authorization
* Relational database modeling
* Database transactions
* ACID-style transactional checkout
* Row-level locking
* Concurrency control
* Idempotent APIs
* Redis caching
* Cache invalidation
* Rate limiting
* Redis Streams
* Consumer groups
* Asynchronous processing
* Database migrations
* Automated testing
* Structured logging
* Docker containerization
* Docker Compose service orchestration

---

## Project Goal

OrderFlow was built as a focused backend engineering project to explore how reliable order processing systems handle **concurrency, consistency, retries, caching, and asynchronous workloads** while remaining understandable and testable.

The project intentionally avoids unnecessary infrastructure complexity such as Kubernetes, Kafka, microservices, and external payment integrations.
