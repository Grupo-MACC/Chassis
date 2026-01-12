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
from aio_pika import connect_robust, ExchangeType

from microservice_chassis_grupo2.core.config import settings

PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "auth_public.pem")


def _build_ssl_context() -> ssl.SSLContext | None:
    """
    Crea un SSLContext para AMQPS.

    Requisitos (sin mTLS):
        - RABBITMQ_TLS_CA_FILE debe apuntar al ca.pem que firmó el cert del servidor.
    """
    if not settings.RABBITMQ_USE_TLS:
        return None

    ca_file = os.getenv("RABBITMQ_TLS_CA_FILE", "").strip()
    if not ca_file:
        raise RuntimeError(
            "RABBITMQ_USE_TLS=1 pero falta RABBITMQ_TLS_CA_FILE "
            "(ej: /certs/ca.pem)."
        )
    if not os.path.exists(ca_file):
        raise RuntimeError(f"No existe el CA file: {ca_file}")

    ctx = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile=ca_file,
    )

    # Mínimo razonable para entrega
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    # Con tu cert CN=rabbitmq y RABBITMQ_HOST=rabbitmq, esto debe pasar.
    ctx.check_hostname = True

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
    ssl_ctx = _build_ssl_context()
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
