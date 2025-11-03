import os

class Settings():
    ALGORITHM: str = "RS256"
    RABBITMQ_HOST = f"amqp://{os.getenv("RABBITMQ_USER", "guest")}:{os.getenv("RABBITMQ_PASSWORD", "guest")}@{os.getenv("RABBITMQ_HOST", "localhost")}/"
    EXCHANGE_NAME = "broker"
    EXCHANGE_NAME_COMMAND = "command"
    EXCHANGE_NAME_SAGA = "saga"

settings = Settings()