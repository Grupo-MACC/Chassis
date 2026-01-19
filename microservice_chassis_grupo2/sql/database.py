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
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from microservice_chassis_grupo2.core.consul import get_service_url
import logging
from microservice_chassis_grupo2.core.secrets import SSMSecrets

logger = logging.getLogger(__name__)

ssm = SSMSecrets(region=os.getenv("AWS_REGION", "us-east-1"))

async def get_database_url():
    """Get database URL from Consul or fallback to environment variable."""
    print("[DATABASE] Starting get_database_url()")
    
    db_user = os.getenv('DB_USER', 'admin')
    db_password = ssm.get_parameter('/infrastructure/dev/rds/password')
    db_name = os.getenv('DB_NAME')
    
    if not db_name:
        raise ValueError("DB_NAME environment variable is required")
    
    print(f"[DATABASE] Using DB_NAME: {db_name}")
    
    # ✅ Primero intentar RDS_HOST directo
    rds_host = os.getenv('RDS_HOST')
    if rds_host:
        rds_port = os.getenv('RDS_PORT', '3306')
        direct_url = f"mysql+aiomysql://{db_user}:{db_password}@{rds_host}:{rds_port}/{db_name}"
        print(f"[DATABASE] Using direct RDS connection: {rds_host}:{rds_port}")
        logger.info(f"Using direct RDS connection: {rds_host}:{rds_port}/{db_name}")
        return direct_url
    
    try:
        print("[DATABASE] Attempting to get RDS from Consul...")
        rds_info = await get_service_url(
            service_name="rds",
            default_url=None
        )
        
        print(f"[DATABASE] Got RDS info from Consul: {rds_info}")
        
        # ✅ CORRECCIÓN: Remover el prefijo http:// si existe
        if rds_info.startswith('http://'):
            rds_info = rds_info.replace('http://', '')
        elif rds_info.startswith('https://'):
            rds_info = rds_info.replace('https://', '')
        
        print(f"[DATABASE] Cleaned RDS info: {rds_info}")
        
        # Construir URL de conexión MySQL
        database_url = f"mysql+aiomysql://{db_user}:{db_password}@{rds_info}/{db_name}"
        print(f"[DATABASE] Using RDS from Consul for database: {db_name}")
        logger.info(f"Using RDS from Consul: {rds_info} for database: {db_name}")
        return database_url
        
    except Exception as e:
        print(f"[DATABASE] Error getting RDS from Consul: {type(e).__name__}: {str(e)}")
        fallback_url = os.getenv('SQLALCHEMY_DATABASE_URL', 'sqlite+aiosqlite:///./test.db')
        print(f"[DATABASE] Using fallback: {fallback_url}")
        logger.warning(f"Could not get RDS from Consul: {str(e)}, using fallback: {fallback_url}")
        return fallback_url

# Variables globales
engine = None
SessionLocal = None
Base = declarative_base()
_db_initialized = False

async def init_database():
    global engine, SessionLocal, _db_initialized

    print("[DATABASE] init_database() called")

    if _db_initialized:
        print("[DATABASE] Database already initialized")
        return

    database_url = await get_database_url()

    print("[DATABASE] Creating engine...")

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
