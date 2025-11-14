from aio_pika import connect_robust, ExchangeType
import os
from microservice_chassis_grupo2.core.config import settings

#"/home/pyuser/code/auth_public.pem"
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "auth_public.pem")

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
        settings.EXCHANGE_NAME_COMMAND,
        ExchangeType.TOPIC,
        durable=True
    )

    return exchange

async def declare_exchange_saga(channel):
    exchange = await channel.declare_exchange(
        settings.EXCHANGE_NAME_SAGA,
        ExchangeType.TOPIC,
        durable=True
    )

    return exchange

async def declare_exchange_logs(channel):
    exchange = await channel.declare_exchange(
        settings.EXCHANGE_NAME_LOGS,
        ExchangeType.TOPIC,
        durable=True
    )
    queue = await channel.declare_queue(
        "telegraf_metrics",
        durable=True
    )
    await queue.bind(exchange, routing_key="#")

    return exchange