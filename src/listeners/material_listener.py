from src.messaging.rabbit_consumer import RabbitConsumer

# Backward compatibility wrapper
class MaterialListener:
    def __init__(self, channel, sap_service):
        self.consumer = RabbitConsumer(channel, sap_service)

    def start(self):
        self.consumer.start()

    def receive(self, ch, method, properties, body):
        self.consumer._on_message(ch, method, properties, body)