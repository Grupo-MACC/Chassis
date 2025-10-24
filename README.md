# 🧩 Microservice Chassis Grupo 2

**Repository link:** https://github.com/Grupo-MACC/Chassis

---

## Functionalities

This repository provides a **shared chassis** for microservices, containing configuration, database management, authentication, messaging, and helper utilities.  
It allows microservices to reuse common functionalities such as database connections, JWT validation, RabbitMQ communication, and standardized base models.

Below is a detailed list of the available functionalities:

| **Module** | **Functionality** | **Description** |
|-------------|------------------|-----------------|
| `core/config.py` | **Settings Management** | Centralized configuration for the chassis. Defines constants like the encryption algorithm (`RS256`), RabbitMQ connection parameters (`RABBITMQ_HOST`), and exchange name (`broker`). |
| `core/security.py` | **Token Decoding and Verification** | Handles JWT decoding using a public RSA key. Validates tokens and raises appropriate HTTP errors if invalid or missing. |
| `core/dependencies.py` | **Database Session & Authentication Dependency** | Provides FastAPI dependencies to manage asynchronous database sessions (`get_db`) and current user retrieval (`get_current_user`) from a JWT token. |
| `core/rabbitmq.py` | **RabbitMQ Channel & Exchange Management** | Creates asynchronous connections to RabbitMQ using `aio_pika`. Declares durable topic exchanges for inter-service communication. |
| `core/utils.py` | **Helper Functions and Service URLs** | Defines service URLs (order, machine, delivery, payment, auth) and provides error handling utilities with standardized logging (`raise_and_log_error`). |
| `sql/database.py` | **Database Engine & Session Configuration** | Configures SQLAlchemy’s asynchronous engine and sessionmaker. Supports `SQLALCHEMY_DATABASE_URL` via environment variable (defaults to SQLite). |
| `sql/base_class.py` | **Base Model for ORM Classes** | Provides a reusable abstract base class (`BaseModel`) for all database models, including timestamp columns (`creation_date`, `update_date`) and helper methods for converting models to dictionaries. |

---

## Functionalities per Microservice

| **Microservice** | **Used Functionalities** |
|------------------|--------------------------|
| `payment` | `core/config`, `core/security`, `core/dependencies`, `core/rabbitmq`, `core/utils`, `sql/database`, `sql/base_class` |

---

## Summary

This chassis allows the `payment` microservice (and potentially others in the future) to operate with consistent patterns for:
- Secure token validation.
- Standardized database access and sessions.
- Centralized configuration.
- RabbitMQ-based inter-service communication.
- Common helper utilities and error management.
- Unified base ORM models.

It provides a robust foundation for building scalable and maintainable microservices within the system.
