import os

class Settings():
    ALGORITHM: str = "RS256"
    RABBITMQ_HOST = f"amqp://{os.getenv("RABBITMQ_USER", "guest")}:{os.getenv("RABBITMQ_PASSWORD", "guest")}@rabbitmq/"
    EXCHANGE_NAME = "broker"

settings = Settings()