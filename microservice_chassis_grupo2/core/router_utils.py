# -*- coding: utf-8 -*-
"""Util/Helper functions for router definitions."""
import logging
from fastapi import HTTPException

ORDER_SERVICE_URL = "https://order:5000"
MACHINE_SERVICE_URL = "https://machine:5001"
DELIVERY_SERVICE_URL = "https://delivery:5002"
PAYMENT_SERVICE_URL = "https://payment:5003"
AUTH_SERVICE_URL = "https://auth:5004"

logger = logging.getLogger(__name__)


def raise_and_log_error(my_logger, status_code: int, message: str):
    """Raises HTTPException and logs an error."""
    my_logger.error(message)
    raise HTTPException(status_code, message)