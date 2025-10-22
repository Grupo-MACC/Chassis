from aio_pika import connect_robust, ExchangeType
from config import settings

async def get_channel():
    connection = await connect_robust(settings.RABBITMQ_HOST)
    channel = await connection.channel()
    
    return channel

async def declare_exchange(channel):
    exchange = channel.declare_exchange(
        settings.EXCHANGE_NAME,
        ExchangeType.TOPIC,
        durable=True
    )

    return exchange