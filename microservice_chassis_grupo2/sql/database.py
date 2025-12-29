import os
import asyncio
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from microservice_chassis_grupo2.core.consul import get_service_url
import logging

logger = logging.getLogger(__name__)

async def get_database_url():
    """Get database URL from Consul or fallback to environment variable."""
    try:
        # Intentar obtener RDS desde Consul
        rds_info = await get_service_url(
            service_name="rds",
            default_url=None
        )
        
        # Construir URL de conexión MySQL
        db_user = os.getenv('DB_USER', 'admin')
        db_password = os.getenv('DB_PASSWORD', 'maccadmin')
        db_name = os.getenv('DB_NAME', 'auth_db')
        
        # rds_info ya viene como "host:port", sin http://
        database_url = f"mysql+aiomysql://{db_user}:{db_password}@{rds_info}/{db_name}"
        logger.info(f"Using RDS from Consul: {rds_info}")
        return database_url
        
    except Exception as e:
        # Fallback a variable de entorno
        fallback_url = os.getenv('SQLALCHEMY_DATABASE_URL', 'sqlite+aiosqlite:///./auth.db')
        logger.warning(f"Could not get RDS from Consul, using fallback: {fallback_url}")
        return fallback_url

# Variables globales
engine = None
SessionLocal = None
Base = declarative_base()
_db_initialized = False

async def init_database():
    """Initialize database connection."""
    global engine, SessionLocal, _db_initialized
    
    if _db_initialized:
        return
    
    database_url = await get_database_url()
    
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,  # Verificar conexiones antes de usarlas
        pool_recycle=3600,   # Reciclar conexiones cada hora
    )
    
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=AsyncSession,
        future=True
    )
    
    _db_initialized = True
    logger.info("Database initialized successfully")

# Inicializar al importar el módulo
def _sync_init():
    """Wrapper síncrono para inicializar la base de datos."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # Si ya hay un loop corriendo, crear una tarea
        asyncio.create_task(init_database())
    else:
        # Si no hay loop, ejecutar sincrónicamente
        loop.run_until_complete(init_database())

# Auto-inicializar cuando se importa
_sync_init()