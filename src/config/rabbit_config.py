import os


class RabbitConfig:

    HOST = os.getenv("RABBITMQ_HOST", "localhost")
    PORT = int(os.getenv("RABBITMQ_PORT", 5672))
    USER = os.getenv("RABBITMQ_USERNAME", "guest")
    PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

    EXCHANGE = "sap.exchange"

    EXECUTE_QUEUE = "sap.execute.queue"
    RESPONSE_QUEUE = "sap.response.queue"

    EXECUTE_ROUTING_KEY = "sap.execute"
    RESPONSE_ROUTING_KEY = "sap.response"