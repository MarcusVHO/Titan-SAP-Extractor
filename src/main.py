from config.rabbit_config import RabbitConfig

from messaging.rabbit_connection import RabbitConnection

from listeners.material_listener import MaterialListener
from service.sap_service import SapService
from src.messaging.rabbit_producer import RabbitProducer

connection = RabbitConnection().create_connection()

channel = connection.channel()


channel.queue_declare(
    queue=RabbitConfig.EXECUTE_QUEUE,
    durable=True
)

producer = RabbitProducer(channel)
sap_service = SapService(producer)

listener = MaterialListener(channel, sap_service)
listener.start()

