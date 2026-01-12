# -*- coding: utf-8 -*-
"""microservice_chassis_grupo2.sql.database

Inicialización de SQLAlchemy Async.

Compatibilidad:
    - Si existe SQLALCHEMY_DATABASE_URL, inicializa engine/SessionLocal al importar
      (evita `engine=None` en microservicios que usan `database.engine` directamente).

Modo “avanzado” (AWS/Consul):
    - Si no existe SQLALCHEMY_DATABASE_URL, se puede usar `await init_database()`
      para resolver RDS (por RDS_HOST o descubriendo servicio `rds` en Consul).
"""
from __future__ import annotations

import os
import asyncio
import logging
from typing import Optional

from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine

from microservice_chassis_grupo2.core.consul import get_service_url

logger = logging.getLogger(__name__)

# Estado global
engine: Optional[AsyncEngine] = None
SessionLocal: Optional[sessionmaker] = None
Base = declarative_base()

_db_initialized: bool = False
_init_lock = asyncio.Lock()


def _safe_url_hint(url: str) -> str:
    """Evita volcar credenciales en logs."""
    try:
        return url.split("://", 1)[0] + "://***"
    except Exception:
        return "***"


def _create_engine_and_session(database_url: str) -> None:
    """Crea engine y SessionLocal (sin I/O)."""
    global engine, SessionLocal, _db_initialized

    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        future=True,
    )
    SessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    _db_initialized = True
    logger.info("[DATABASE] Engine creado (%s)", _safe_url_hint(database_url))


async def get_database_url() -> str:
    """Resuelve la URL de BD.

    Prioridad:
        1) SQLALCHEMY_DATABASE_URL
        2) RDS_HOST + DB_USER/DB_PASSWORD + DB_NAME (MySQL)
        3) DB_NAME + Consul(service=rds) + DB_USER/DB_PASSWORD (MySQL)
        4) fallback sqlite default.db
    """
    env_url = os.getenv("SQLALCHEMY_DATABASE_URL")
    if env_url:
        return env_url

    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    if not db_name:
        return "sqlite+aiosqlite:///./default.db"

    rds_host = os.getenv("RDS_HOST")
    if rds_host:
        rds_port = os.getenv("RDS_PORT", "3306")
        if not db_user or not db_password:
            raise RuntimeError("Faltan DB_USER/DB_PASSWORD para RDS_HOST.")
        return f"mysql+aiomysql://{db_user}:{db_password}@{rds_host}:{rds_port}/{db_name}"

    # Consul discovery
    rds_info = await get_service_url(service_name="rds", default_url=None)
    if rds_info.startswith("http://"):
        rds_info = rds_info.replace("http://", "")
    elif rds_info.startswith("https://"):
        rds_info = rds_info.replace("https://", "")

    if not db_user or not db_password:
        raise RuntimeError("Faltan DB_USER/DB_PASSWORD para RDS via Consul.")

    return f"mysql+aiomysql://{db_user}:{db_password}@{rds_info}/{db_name}"


async def init_database() -> None:
    """Inicializa engine y SessionLocal (idempotente y async-safe)."""
    global _db_initialized

    if _db_initialized:
        return

    async with _init_lock:
        if _db_initialized:
            return

        database_url = await get_database_url()
        _create_engine_and_session(database_url)


async def dispose_database() -> None:
    """Libera recursos de BD de forma segura."""
    global engine, SessionLocal, _db_initialized

    if engine is not None:
        await engine.dispose()

    engine = None
    SessionLocal = None
    _db_initialized = False


# ✅ Compatibilidad: init eager si existe SQLALCHEMY_DATABASE_URL
_env_url = os.getenv("SQLALCHEMY_DATABASE_URL")
if _env_url:
    try:
        _create_engine_and_session(_env_url)
    except Exception:
        logger.exception("[DATABASE] Falló la inicialización eager desde SQLALCHEMY_DATABASE_URL.")
