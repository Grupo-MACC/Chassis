# -*- coding: utf-8 -*-
"""Util/Helper functions for router definitions."""
import logging
import os
from fastapi import HTTPException

ORDER_SERVICE_URL = f"{os.getenv('ORDER_SERVICE', 'http://localhost')}:5000"
MACHINE_SERVICE_URL = f"{os.getenv('MACHINE_SERVICE', 'http://localhost')}:5001"
DELIVERY_SERVICE_URL = f"{os.getenv('DELIVERY_SERVICE', 'http://localhost')}:5002"
PAYMENT_SERVICE_URL = f"{os.getenv('PAYMENT_SERVICE', 'http://localhost')}:5003"
AUTH_SERVICE_URL = f"{os.getenv('AUTH_SERVICE', 'http://localhost')}:5004"

logger = logging.getLogger(__name__)


def raise_and_log_error(my_logger, status_code: int, message: str):
    """Raises HTTPException and logs an error."""
    my_logger.error(message)
    raise HTTPException(status_code, message)
