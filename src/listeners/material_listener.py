import json

from src.config.rabbit_config import RabbitConfig
from src.service.sap_service import SapService


class MaterialListener:

    def __init__(self, channel, sap_service: SapService):
        self.channel = channel
        self.sap_service = sap_service

    def start(self):
        print("Registrando consumer...")

        self.channel.basic_consume(
            queue=RabbitConfig.EXECUTE_QUEUE,
            on_message_callback=self.receive,
            auto_ack=False
        )

        print("Consumer registrado")
        print("Consumindo...")

        self.channel.start_consuming()

        print("Saiu do consuming")

    def receive(self, ch, method, properties, body):
        message = json.loads(body)
        print(message)
        self.sap_service.process(message)

        ch.basic_ack(delivery_tag=method.delivery_tag)