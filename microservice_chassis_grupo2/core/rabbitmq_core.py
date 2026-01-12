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
import hashlib
from aio_pika import connect_robust, ExchangeType

from microservice_chassis_grupo2.core.config import settings

logger = logging.getLogger(__name__)

# Ruta al public key para verificar JWTs
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "auth_public.pem")


def _build_ssl_context() -> ssl.SSLContext:
    """
    Construye un SSLContext que CONFÍA en la CA del proyecto.

    Reglas:
        - La CA debe estar en /certs/ca.pem (o en RABBITMQ_TLS_CA_FILE).
        - Si la CA no existe o no se puede cargar, se lanza excepción (fail-fast).
    """
    ca_file = os.getenv("RABBITMQ_TLS_CA_FILE", "/certs/ca.pem").strip() or "/certs/ca.pem"

    if not os.path.isfile(ca_file):
        raise FileNotFoundError(f"No existe el CA file para RabbitMQ TLS: {ca_file}")

    # Log útil (sin exponer secretos)
    ca_bytes = open(ca_file, "rb").read()
    logger.info(
        "[RABBITMQ TLS] Usando CA file: %s (sha256=%s bytes=%s)",
        ca_file,
        hashlib.sha256(ca_bytes).hexdigest(),
        len(ca_bytes),
    )

    # create_default_context(cafile=...)
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=ca_file)

    # Opcional: endurecer versión mínima (sin romper TLSv1.3)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    return ctx


async def _connect(url: str, ssl_ctx: ssl.SSLContext | None):
    """
    Abre conexión robusta a RabbitMQ con TLS correctamente aplicado.

    Reglas:
        - Sin TLS -> connect_robust(url)
        - Con TLS:
            * Si existe parámetro `ssl_options`, usar: ssl=True, ssl_options=ssl_ctx
            * Si no existe, intentar: ssl=ssl_ctx (modo antiguo)
    """
    if ssl_ctx is None:
        return await connect_robust(url)

    params = inspect.signature(connect_robust).parameters

    # ✅ Camino preferido en versiones modernas
    if "ssl_options" in params:
        return await connect_robust(url, ssl=True, ssl_options=ssl_ctx)

    # ✅ Camino alternativo (versiones antiguas)
    if "ssl" in params:
        return await connect_robust(url, ssl=ssl_ctx)

    # Último recurso (muy raro)
    return await connect_robust(url, ssl=True)


async def get_channel():
    """
    Devuelve (connection, channel) listo para declarar colas/exchanges.
    """
    use_tls = os.getenv("RABBITMQ_USE_TLS", "0").strip().lower() in {"1", "true", "yes", "on"}
    ssl_ctx = _build_ssl_context() if use_tls else None
    connection = await _connect(settings.RABBITMQ_HOST, ssl_ctx)
    channel = await connection.channel()
    return connection, channel


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
