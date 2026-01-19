# -*- coding: utf-8 -*-
"""
RabbitMQ core del Chassis (aio-pika).

Objetivo:
    - Si TLS está activo, usar AMQPS con verificación del servidor por CA.
    - SIN mTLS: no cargamos certificado/clave de cliente (no hace falta).
"""

from __future__ import annotations

import os
import ssl
import inspect
import logging
from aio_pika.exceptions import AMQPConnectionError
from aio_pika import connect_robust, ExchangeType

from microservice_chassis_grupo2.core.config import settings
from microservice_chassis_grupo2.core.consul import get_service_url
from microservice_chassis_grupo2.core.secrets import SSMSecrets

logger = logging.getLogger(__name__)

# Ruta al public key para verificar JWTs
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "auth_public.pem")

ssm = SSMSecrets(region=os.getenv("AWS_REGION", "us-east-1"))

async def get_channel():
    service_url = await get_service_url("rabbitmq")
    if service_url:
        address = service_url.split("//")[1].split(":")[0]
        port = service_url.split(":")[2]
        rabbitmq_url = f"amqp://{settings.RABBITMQ_USER}:{ssm.get_parameter('/infrastructure/dev/rabbitmq/password')}@{address}:{port}/"
        connection = await connect_robust(rabbitmq_url)
    channel = await connection.channel()
    
    return connection, channel

def _env_bool(name: str, default: str = "0") -> bool:
    """
    Convierte una variable de entorno a bool de forma tolerante.

    Acepta: 1/true/yes/on/y (case-insensitive).
    """
    val = os.getenv(name, default)
    return str(val).strip().lower() in {"1", "true", "yes", "on", "y"}


def _build_ssl_context() -> ssl.SSLContext:
    """
    Construye un SSLContext para TLS simple (server-auth).

    Requisitos:
        - RABBITMQ_TLS_CA_FILE debe apuntar al CA que firmó el cert del servidor RabbitMQ.
        - No se carga cert/key de cliente (NO mTLS).

    Decisiones:
        - TLSv1.2+.
        - check_hostname=False para evitar problemas típicos de CN/SAN en entornos docker.
          (Si tus certs están bien con SAN, puedes ponerlo True sin problema.)
    """
    ca_file = os.getenv("RABBITMQ_TLS_CA_FILE", "/certs/ca.pem")

    if not os.path.exists(ca_file):
        raise FileNotFoundError(f"CA file no encontrado: {ca_file}")

    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=ca_file)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.check_hostname = False

    # Verificación estricta del servidor (lo normal en TLS simple)
    ctx.verify_mode = ssl.CERT_REQUIRED

    return ctx


async def _connect(url: str, ssl_ctx: ssl.SSLContext | None):
    """
    Conecta con aio-pika de forma robusta.

    Estrategia:
        - Si no hay TLS (ssl_ctx is None): conexión normal.
        - Si hay TLS: pasar el SSLContext usando el parámetro correcto
          para la versión de aio-pika instalada.

    Compatibilidad:
        - Algunas versiones soportan `ssl_context=SSLContext`.
        - Otras usan `ssl=True` + `ssl_options` (dict u objeto SSLOptions).
    """
    if ssl_ctx is None:
        return await connect_robust(url)

    sig = inspect.signature(connect_robust)
    params = sig.parameters

    # Opción 1 (preferida): ssl_context=
    if "ssl_context" in params:
        return await connect_robust(url, ssl_context=ssl_ctx)

    # Opción 2: ssl=True + ssl_options=dict(...)
    if "ssl_options" in params:
        # Para aiormq, suele funcionar pasando el contexto dentro de ssl_options.
        # Si tu versión exige keys tipo cafile/certfile/keyfile,
        # aquí también podrías pasar {"cafile": "..."} en vez de context.
        return await connect_robust(url, ssl=True, ssl_options={"context": ssl_ctx})

    # Último recurso: algunas versiones aceptan ssl como contexto
    return await connect_robust(url, ssl=ssl_ctx)


async def get_channel():
    """
    Devuelve (connection, channel) listo para usar.

    Nota profesional:
        - Abrir/cerrar conexión por cada publish es caro.
          Para producción, lo suyo es pool o conexión global por proceso.
        - Aquí mantengo tu contrato actual por compatibilidad.
    """
    use_tls = _env_bool("RABBITMQ_USE_TLS", "0")

    ssl_ctx = _build_ssl_context() if use_tls else None

    try:
        connection = await _connect(settings.RABBITMQ_HOST, ssl_ctx)
        channel = await connection.channel()
        return connection, channel
    except AMQPConnectionError as e:
        # Re-lanzamos con contexto útil (no lo escondas con un fallback “mágico”).
        raise RuntimeError(f"RabbitMQ connection failed (TLS={use_tls}) to {settings.RABBITMQ_HOST}: {e}") from e


async def declare_exchange(channel):
    """Declara el exchange general (broker)."""
    return await channel.declare_exchange(
        settings.EXCHANGE_NAME,
        ExchangeType.TOPIC,
        durable=True,
    )


async def declare_exchange_command(channel):
    """Declara el exchange de comandos (command)."""
    return await channel.declare_exchange(
        settings.EXCHANGE_NAME_COMMAND,
        ExchangeType.TOPIC,
        durable=True,
    )


async def declare_exchange_saga(channel):
    """Declara el exchange de saga (saga)."""
    return await channel.declare_exchange(
        settings.EXCHANGE_NAME_SAGA,
        ExchangeType.TOPIC,
        durable=True,
    )

async def declare_exchange_saga_cancelation_commands(channel):
    """Declara el exchange de comandos (command)."""
    return await channel.declare_exchange(
        settings.EXCHANGE_NAME_SAGA_CANCEL_CMD,
        ExchangeType.TOPIC,
        durable=True,
    )


async def declare_exchange_saga_cancelation_events(channel):
    """Declara el exchange de saga (saga)."""
    return await channel.declare_exchange(
        settings.EXCHANGE_NAME_SAGA_CANCEL_EVT,
        ExchangeType.TOPIC,
        durable=True,
    )

async def declare_exchange_logs(channel):
    """
    Declara el exchange de logs (logs) y asegura la cola telegraf_metrics.
    """
    exchange = await channel.declare_exchange(
        settings.EXCHANGE_NAME_LOGS,
        ExchangeType.TOPIC,
        durable=True,
    )
    queue = await channel.declare_queue("telegraf_metrics", durable=True)
    await queue.bind(exchange, routing_key="#")
    return exchange
