from src.config.app_config import config, AppConfig

# Backward compatibility alias
class RabbitConfig:
    @property
    def HOST(self):
        return config.RABBITMQ_HOST

    @property
    def PORT(self):
        return config.RABBITMQ_PORT

    @property
    def USER(self):
        return config.RABBITMQ_USER

    @property
    def PASSWORD(self):
        return config.RABBITMQ_PASSWORD

    EXCHANGE = config.RABBITMQ_EXCHANGE
    EXECUTE_QUEUE = config.EXECUTE_QUEUE
    RESPONSE_QUEUE = config.RESPONSE_QUEUE
    EXECUTE_ROUTING_KEY = config.EXECUTE_ROUTING_KEY
    RESPONSE_ROUTING_KEY = config.RESPONSE_ROUTING_KEY