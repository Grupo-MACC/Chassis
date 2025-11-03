from aio_pika import connect_robust, ExchangeType
from microservice_chassis_grupo2.core.config import settings

PUBLIC_KEY_PATH = "/home/pyuser/code/auth_public.pem"

async def get_channel():
    connection = await connect_robust(settings.RABBITMQ_HOST)
    channel = await connection.channel()
    
    return connection, channel

async def declare_exchange(channel):
    exchange = await channel.declare_exchange(
        settings.EXCHANGE_NAME,
        ExchangeType.TOPIC,
        durable=True
    )

    return exchange

async def declare_exchange_command(channel):
    exchange = await channel.declare_exchange(
        settings.EXCHANGE_COMMAND_NAME,
        ExchangeType.TOPIC,
        durable=True
    )

    return exchange

async def declare_exchange_saga(channel):
    exchange = await channel.declare_exchange(
        settings.EXCHANGE_SAGA_NAME,
        ExchangeType.TOPIC,
        durable=True
    )

    return exchange