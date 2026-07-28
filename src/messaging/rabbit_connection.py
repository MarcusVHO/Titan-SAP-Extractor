import pika
from typing import Optional
from src.config.app_config import config, AppConfig


class RabbitConnectionManager:
    """
    Gerencia a criação e manutenção da conexão e canal com o RabbitMQ.
    """

    def __init__(self, cfg: Optional[AppConfig] = None):
        self.cfg = cfg or config
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel = None

    def create_connection(self) -> pika.BlockingConnection:
        credentials = pika.PlainCredentials(
            self.cfg.RABBITMQ_USER,
            self.cfg.RABBITMQ_PASSWORD
        )

        parameters = pika.ConnectionParameters(
            host=self.cfg.RABBITMQ_HOST,
            port=self.cfg.RABBITMQ_PORT,
            credentials=credentials,
            connection_attempts=3,
            retry_delay=2
        )

        self._connection = pika.BlockingConnection(parameters)
        return self._connection

    def get_channel(self):
        if not self._connection or self._connection.is_closed:
            self.create_connection()
        
        if not self._channel or self._channel.is_closed:
            self._channel = self._connection.channel()
            self._channel.queue_declare(
                queue=self.cfg.EXECUTE_QUEUE,
                durable=True
            )
            self._channel.queue_declare(
                queue=self.cfg.RESPONSE_QUEUE,
                durable=True
            )
        return self._channel

    def is_connected(self) -> bool:
        return self._connection is not None and self._connection.is_open

    def close(self):
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
            if self._connection and self._connection.is_open:
                self._connection.close()
        except Exception:
            pass
        finally:
            self._connection = None
            self._channel = None


# Retro-compatibilidade com RabbitConnection original
class RabbitConnection:
    def create_connection(self):
        manager = RabbitConnectionManager()
        return manager.create_connection()