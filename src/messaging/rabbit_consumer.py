import json
import logging
from typing import Callable, Optional
from src.config.app_config import config, AppConfig

logger = logging.getLogger("TitanSapManipulator.Consumer")


class RabbitConsumer:
    """
    Consumidor assíncrono/thread-safe de mensagens da fila RabbitMQ.
    """

    def __init__(self, channel, service, cfg: Optional[AppConfig] = None, log_callback: Optional[Callable[[str, str], None]] = None, metric_callback: Optional[Callable[[dict], None]] = None):
        self.channel = channel
        self.service = service
        self.cfg = cfg or config
        self.log_callback = log_callback
        self.metric_callback = metric_callback
        self._is_consuming = False

    def log(self, message: str, level: str = "INFO"):
        logger.info(message)
        if self.log_callback:
            self.log_callback(message, level)

    def start(self):
        """Inicia a escuta da fila."""
        self._is_consuming = True

        # Valida disponibilidade do SAP GUI antes de consumir a fila
        if hasattr(self.service, "manipulator") and self.service.manipulator:
            try:
                self.service.manipulator.connect()
            except Exception as e:
                self.log(f"⚠️ SAP GUI não está disponível ({str(e)}). O consumo da fila NÃO será iniciado.", "WARNING")
                self._is_consuming = False
                if self.metric_callback:
                    self.metric_callback({"status": "SAP_UNAVAILABLE", "error": str(e)})
                return

        self.log(f"Registrando consumidor na fila '{self.cfg.EXECUTE_QUEUE}'...", "INFO")

        try:
            self.channel.basic_consume(
                queue=self.cfg.EXECUTE_QUEUE,
                on_message_callback=self._on_message,
                auto_ack=False
            )
            self.log("Consumidor registrado com sucesso. Aguardando mensagens...", "SUCCESS")
            
            while self._is_consuming and self.channel and self.channel.is_open:
                self.channel.connection.process_data_events(time_limit=1)
                
        except Exception as e:
            if self._is_consuming:
                self.log(f"Erro no loop de consumo RabbitMQ: {str(e)}", "ERROR")
                raise e
        finally:
            self._is_consuming = False
            self.log("Loop de consumo RabbitMQ finalizado.", "WARNING")

    def stop(self):
        """Interrompe o consumo de mensagens."""
        self._is_consuming = False

    def _on_message(self, ch, method, properties, body):
        try:
            raw_text = body.decode('utf-8')
            self.log(f"Mensagem recebida na fila: {raw_text}", "INFO")
            
            message = json.loads(raw_text)
            
            # Delega o processamento ao serviço
            result = self.service.process(message)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.log(f"Mensagem {message.get('id', 'N/A')} processada com sucesso no SAP!", "SUCCESS")
            
            if self.metric_callback:
                self.metric_callback({"status": "SUCCESS", "payload": message, "result": result})

        except json.JSONDecodeError:
            self.log("Falha ao decodificar JSON da mensagem recebida.", "ERROR")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            if self.metric_callback:
                self.metric_callback({"status": "ERROR", "error": "Invalid JSON"})

        except ValueError as ve:
            self.log(f"Mensagem com formato inválido: {str(ve)}", "ERROR")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            if self.metric_callback:
                self.metric_callback({"status": "ERROR", "error": str(ve)})

        except Exception as e:
            self.log(f"Erro ao processar mensagem no SAP ({str(e)}). Devolvendo mensagem para a fila (requeue)...", "ERROR")
            # requeue=True garante que a mensagem NÃO seja consumida/descartada da fila se o SAP falhar
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            if self.metric_callback:
                self.metric_callback({"status": "ERROR", "error": str(e)})

