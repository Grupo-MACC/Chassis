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
import aiormq
from aio_pika import connect_robust, ExchangeType

from microservice_chassis_grupo2.core.config import settings

logger = logging.getLogger(__name__)

# Ruta al public key para verificar JWTs
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "auth_public.pem")


def _build_ssl_context() -> ssl.SSLContext:
    """
    Construye el contexto TLS para verificar RabbitMQ con CA interna.
    """
    ca_file = os.getenv("RABBITMQ_TLS_CA_FILE", "/certs/ca.pem")

    ctx = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile=ca_file,
    )

    # TLS mínimo
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    # Verifica CA, pero sin hostname (evita SAN issues)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = False

    return ctx


async def _connect(url: str, ssl_ctx: ssl.SSLContext | None):
    """Conecta con aio-pika aplicando TLS de forma compatible entre versiones."""
    if ssl_ctx is None:
        return await connect_robust(url)

    # Intento 1: estilo moderno
    try:
        return await connect_robust(url, ssl=ssl_ctx)
    except TypeError:
        # Signature antigua
        pass
    except aiormq.exceptions.AMQPConnectionError as e:
        # Si es error de verificación TLS, probamos el otro estilo
        msg = str(e)
        if "CERTIFICATE_VERIFY_FAILED" not in msg:
            raise

    # Intento 2: estilo compatible
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
