import os

class Settings():
    ALGORITHM: str = "RS256"
    RABBITMQ_HOST = (
        f"amqp://{os.getenv('RABBITMQ_USER', 'guest')}:"
        f"{os.getenv('RABBITMQ_PASSWORD', 'guest')}@"
        f"{os.getenv('RABBITMQ_HOST', 'localhost')}/"
)
    EXCHANGE_NAME = "broker"
    EXCHANGE_NAME_COMMAND = "command"
    EXCHANGE_NAME_SAGA = "saga"
    EXCHANGE_NAME_LOGS = "logs"

settings = Settings()