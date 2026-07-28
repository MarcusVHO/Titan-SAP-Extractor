import json
from typing import Optional
from src.config.app_config import config, AppConfig


class RabbitProducer:
    """
    Publica mensagens de resposta no RabbitMQ.
    """

    def __init__(self, channel, cfg: Optional[AppConfig] = None):
        self.channel = channel
        self.cfg = cfg or config

    def publish(self, message: dict):
        routing_key = self.cfg.RESPONSE_ROUTING_KEY
        exchange = self.cfg.RABBITMQ_EXCHANGE if hasattr(self.cfg, 'RABBITMQ_EXCHANGE') else ""
        
        # Fallback se exchange for string vazia ou se publicar direto na fila
        if not exchange:
            exchange = ""
            routing_key = self.cfg.RESPONSE_QUEUE

        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(message, ensure_ascii=False)
        )
