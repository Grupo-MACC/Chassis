# -*- coding: utf-8 -*-
"""Util/Helper functions for router definitions."""
import logging
import os
from fastapi import HTTPException

ORDER_SERVICE_URL = f"https://{os.getenv("ORDER_SERVICE", "locahost")}:5000"
MACHINE_SERVICE_URL = f"https://{os.getenv("MACHINE_SERVICE", "locahost")}:5001"
DELIVERY_SERVICE_URL = f"https://{os.getenv("DELIVERY_SERVICE", "locahost")}:5002"
PAYMENT_SERVICE_URL = f"https://{os.getenv("PAYMENT_SERVICE", "locahost")}:5003"
AUTH_SERVICE_URL = f"https://{os.getenv("AUTH_SERVICE", "locahost")}:5004"

logger = logging.getLogger(__name__)


def raise_and_log_error(my_logger, status_code: int, message: str):
    """Raises HTTPException and logs an error."""
    my_logger.error(message)
    raise HTTPException(status_code, message)