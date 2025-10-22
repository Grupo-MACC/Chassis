import os

class Settings():
    ALGORITHM: str = "RS256"
    RABBITMQ_HOST = "amqp://guest:guest@rabbitmq/"
    EXCHANGE_NAME = ""

settings = Settings()