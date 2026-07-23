import pika
from src.config.rabbit_config import RabbitConfig


class RabbitConnection:

    def create_connection(self):

        credentials = pika.PlainCredentials(
            RabbitConfig.USER,
            RabbitConfig.PASSWORD
        )

        return pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RabbitConfig.HOST,
                port=RabbitConfig.PORT,
                credentials=credentials
            )
        )