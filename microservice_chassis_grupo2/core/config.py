import os

class Settings():
    ALGORITHM: str = "RS256"
    RABBITMQ_HOST = (
        f"amqp://{os.getenv('RABBITMQ_USER', 'guest')}:"
        f"{os.getenv('RABBITMQ_PASSWORD', 'guest')}@"
        f"{os.getenv('RABBITMQ_HOST', 'localhost')}/"
    )
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
    CONSUL_HOST: str = os.getenv("CONSUL_HOST", "10.0.11.40")
    CONSUL_PORT: int = int(os.getenv("CONSUL_PORT", 8500))
    EXCHANGE_NAME = "broker"
    EXCHANGE_NAME_COMMAND = "command"
    EXCHANGE_NAME_SAGA = "saga"
    EXCHANGE_NAME_LOGS = "logs"

settings = Settings()