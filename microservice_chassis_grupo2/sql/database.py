import os
import asyncio
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from microservice_chassis_grupo2.core.consul import get_service_url
import logging

logger = logging.getLogger(__name__)

async def get_database_url():
    """Get database URL from Consul or fallback to environment variable."""
    print("[DATABASE] Starting get_database_url()")
    
    db_user = os.getenv('DB_USER', 'admin')
    db_password = os.getenv('DB_PASSWORD', 'maccadmin')
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
    """Initialize database connection."""
    global engine, SessionLocal, _db_initialized
    
    print("[DATABASE] init_database() called")
    
    if _db_initialized:
        print("[DATABASE] Database already initialized")
        return
    
    database_url = await get_database_url()
    print(f"[DATABASE] Creating engine with URL (password hidden): {database_url.split('@')[0].split(':')[0]}://***@{database_url.split('@')[1].split('/')[0]}")