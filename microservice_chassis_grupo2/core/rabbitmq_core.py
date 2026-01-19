from aio_pika import connect_robust, ExchangeType
import os
from microservice_chassis_grupo2.core.config import settings
from microservice_chassis_grupo2.core.consul import get_service_url
from microservice_chassis_grupo2.core.secrets import SSMSecrets

#"/home/pyuser/code/auth_public.pem"
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "auth_public.pem")

ssm = SSMSecrets(region=os.getenv("AWS_REGION", "us-east-1"))

async def get_channel():
    service_url = await get_service_url("rabbitmq")
    if service_url:
        address = service_url.split("//")[1].split(":")[0]
        port = service_url.split(":")[2]
        rabbitmq_url = f"amqp://{settings.RABBITMQ_USER}:{ssm.get_parameter('/infrastructure/dev/rabbitmq/password')}@{address}:{port}/"
        connection = await connect_robust(rabbitmq_url)
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