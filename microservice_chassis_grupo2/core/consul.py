import os
import asyncio
import httpx

class ConsulClient:
    def __init__(self, host: str, port: str):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/v1"

    async def deregister_service(
        self,
        service_id: str
    ) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/agent/service/deregister/{service_id}",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return True
                else:
                    return False
        except Exception as e:
            return False
    
    async def discover_service(
        self,
        service_name: str
    ) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/catalog/service/{service_name}",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    services = response.json()
                    if services:
                        service = services[0]
                        return {
                            "address": service.get("ServiceAddress") or service.get("Address"),
                            "port": service.get("ServicePort"),
                        }
        except Exception as e:
            return None

_consul_client = None

def create_consul_client() -> ConsulClient:
    global _consul_client
    if _consul_client is None:
        host = os.getenv("CONSUL_HOST", "localhost")
        port = int(os.getenv("CONSUL_PORT", 8500))
        _consul_client = ConsulClient(host, port)
    return _consul_client

async def get_service_url(service_name: str, default_url: str = None) -> str:
    """Get service URL from Consul with retry and fallback."""
    consul_client = create_consul_client()
    max_retries = 5
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            service_info = await consul_client.discover_service(service_name)
            if service_info:
                url = f"http://{service_info['address']}:{service_info['port']}"
                return url
        except Exception as e:
            pass
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)

    # Fallback to default
    if default_url:
        return default_url

    raise Exception(f"Could not discover service: {service_name}")