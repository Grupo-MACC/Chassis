import os

class Settings():
    ALGORITHM: str = "RS256"
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    EXCHANGE_NAME = "broker"
    EXCHANGE_NAME_COMMAND = "command"
    EXCHANGE_NAME_SAGA = "saga"
    EXCHANGE_NAME_LOGS = "logs"

settings = Settings()