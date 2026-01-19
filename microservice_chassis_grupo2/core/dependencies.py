import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from microservice_chassis_grupo2.core.security import decode_token, PUBLIC_KEY_PATH
import os

logger = logging.getLogger(__name__)
auth_scheme = HTTPBearer()

# Database #########################################################################################
async def get_db():
    """Genera sesiones de BD y las cierra al terminar.

    Nota:
        - init_database() es idempotente: si ya se inicializó, no repite trabajo.
        - Se mantiene commit/rollback automático como en tu implementación original.
    """
    from microservice_chassis_grupo2.sql.database import init_database, SessionLocal

    # ✅ Asegura engine y SessionLocal listos antes de usarlos
    await init_database()

    if SessionLocal is None:
        raise RuntimeError(
            "SessionLocal no inicializada tras init_database(). "
            "Revisa microservice_chassis_grupo2/sql/database.py"
        )

    db = SessionLocal()
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    """
    Decodifica el JWT y obtiene el usuario actual desde la base de datos.
    """
    token = credentials.credentials

    try:
        payload = decode_token(token) 
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    
    return user_id

def check_public_key():
    if os.path.exists(PUBLIC_KEY_PATH):
        with open(PUBLIC_KEY_PATH, "r", encoding="utf-8") as f:
            f.read()
        return True
    else:
        return False