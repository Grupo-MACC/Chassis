# -*- coding: utf-8 -*-
"""
Configuración del Chassis.

Objetivo:
    - Mantener compatibilidad con el sistema actual (AMQP sin TLS por defecto).
    - Permitir activar TLS (AMQPS) sin tocar el código de los microservicios:
        * RABBITMQ_USE_TLS=1
        * RABBITMQ_PORT=5671
        * RABBITMQ_TLS_CA_FILE=/certs/ca.pem
"""

from __future__ import annotations

import os


def _env_bool(name: str, default: str = "0") -> bool:
    """
    Convierte una variable de entorno a bool de forma tolerante.

    Acepta: 1/true/yes/on/y (case-insensitive).
    """
    val = os.getenv(name, default)
    return str(val).strip().lower() in {"1", "true", "yes", "on", "y"}


class Settings:
    """
    Settings centralizados.

    Nota:
        Mantengo el nombre `RABBITMQ_HOST` porque ya lo usa todo el proyecto.
        Aquí pasa a ser una URL completa (amqp/amqps) con puerto.
    """

    ALGORITHM: str = "RS256"
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    EXCHANGE_NAME = "broker"
    EXCHANGE_NAME_COMMAND = "command"
    EXCHANGE_NAME_SAGA = "saga"
    EXCHANGE_NAME_LOGS = "logs"
    EXCHANGE_NAME_SAGA_CANCEL_CMD = "saga_cancel_cmd"
    EXCHANGE_NAME_SAGA_CANCEL_EVT = "saga_cancel_evt"

    # --- RabbitMQ base ---
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_HOSTNAME = os.getenv("RABBITMQ_HOST", "localhost")

    # --- TLS switch ---
    RABBITMQ_USE_TLS: bool = _env_bool("RABBITMQ_USE_TLS", "0")

    # Puerto por defecto según TLS
    _default_port = "5671" if RABBITMQ_USE_TLS else "5672"
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", _default_port))

    # Override opcional por si alguien quiere pasar una URL completa
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "").strip()

    # URL final (compatibilidad con el resto del código)
    if RABBITMQ_URL:
        RABBITMQ_HOST = RABBITMQ_URL
    else:
        scheme = "amqps" if RABBITMQ_USE_TLS else "amqp"
        RABBITMQ_HOST = (
            f"{scheme}://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}"
            f"@{RABBITMQ_HOSTNAME}:{RABBITMQ_PORT}/"
        )


settings = Settings()
