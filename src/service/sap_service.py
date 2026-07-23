from src.messaging.rabbit_producer import RabbitProducer
from src.sap_manipulator.sap_maniplutaro import SapManipulator


class SapService:
    def __init__(self, producer:RabbitProducer):
        self.manipulator = SapManipulator()
        self.producer = producer

    def process(self, message):
        sapData = self.manipulator.request_item(message["sku"],message["module"])
        sapData["id"] = message["id"]
        self.producer.publish(sapData)

