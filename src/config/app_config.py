import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AppConfig:
    # RabbitMQ Connection Settings
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", 5672))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USERNAME", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_EXCHANGE: str = os.getenv("RABBITMQ_EXCHANGE", "sap.exchange")

    # Fixed Queue System Names
    EXECUTE_QUEUE: str = "sap.execute.queue"
    RESPONSE_QUEUE: str = "sap.response.queue"

    EXECUTE_ROUTING_KEY: str = "sap.execute"
    RESPONSE_ROUTING_KEY: str = "sap.response"

    # Application Settings
    APP_NAME: str = "Titan-SAP-Manipulator"
    VERSION: str = "2.0.0"

    def update_connection(self, host: str, port: int, user: str, password: str):
        self.RABBITMQ_HOST = host
        self.RABBITMQ_PORT = port
        self.RABBITMQ_USER = user
        self.RABBITMQ_PASSWORD = password


# Default instance
config = AppConfig()
