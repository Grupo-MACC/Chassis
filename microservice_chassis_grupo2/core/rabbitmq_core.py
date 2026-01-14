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


def _build_ssl_context() -> ssl.SSLContext | None:
    """
    Crea un SSLContext para AMQPS usando SIEMPRE la CA del proyecto.

    Reglas:
        - Si RABBITMQ_USE_TLS no está activo -> None.
        - La CA se obtiene de RABBITMQ_TLS_CA_FILE; si no existe, usa /certs/ca.pem.
        - Si el fichero no existe o no se puede cargar -> excepción (fail-fast).
    """
    if not getattr(settings, "RABBITMQ_USE_TLS", False):
        return None

    ca_file = os.getenv("RABBITMQ_TLS_CA_FILE", "/certs/ca.pem").strip() or "/certs/ca.pem"

    if not os.path.isfile(ca_file):
        raise FileNotFoundError(f"[RABBITMQ TLS] No existe CA file: {ca_file}")

    ca_bytes = open(ca_file, "rb").read()
    logger.info(
        "[RABBITMQ TLS] CA file=%s sha256=%s bytes=%s",
        ca_file,
        hashlib.sha256(ca_bytes).hexdigest(),
        len(ca_bytes),
    )

    # ✅ EXACTAMENTE como tu prueba que funciona
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=ca_file)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


async def _connect(url: str, ssl_ctx: ssl.SSLContext | None):
    """
    Conecta con aio-pika aplicando TLS de forma compatible.

    Estrategia:
        1) Intentar ssl=SSLContext (lo que suele consumir aiormq directamente).
        2) Si TypeError -> intentar ssl=True + ssl_options=SSLContext.
        3) Si vuelve a fallar -> re-lanzar.
    """
    if ssl_ctx is None:
        return await connect_robust(url)

    # 1) ✅ Primer intento: pasar el contexto por `ssl`
    try:
        return await connect_robust(url, ssl=ssl_ctx)
    except TypeError:
        pass

    # 2) Fallback: ssl=True + ssl_options
    return await connect_robust(url, ssl=True, ssl_options=ssl_ctx)


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
