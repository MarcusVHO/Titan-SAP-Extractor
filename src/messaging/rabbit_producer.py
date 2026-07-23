import json

from src.config.rabbit_config import RabbitConfig

class RabbitProducer:

    def __init__(self, channel):
        self.channel = channel

    def publish(self, message: dict):
        self.channel.basic_publish(
            exchange=RabbitConfig.EXCHANGE,
            routing_key=RabbitConfig.RESPONSE_ROUTING_KEY,
            body=json.dumps(message)
        )



