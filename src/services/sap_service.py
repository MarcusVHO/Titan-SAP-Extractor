from typing import Optional
from src.core.sap_manipulator import SapManipulator
from src.messaging.rabbit_producer import RabbitProducer


class SapService:
    """
    Camada de Serviço responsável por orquestrar a leitura da fila,
    interação com a automação SAP e publicação dos resultados.
    """

    def __init__(self, producer: RabbitProducer, manipulator: Optional[SapManipulator] = None):
        self.manipulator = manipulator or SapManipulator()
        self.producer = producer

    def process(self, message: dict) -> dict:
        """
        Processa uma mensagem recebida e responde com os dados do SAP.
        """
        sku = message.get("sku")
        modulo = message.get("module") or message.get("modulo")
        msg_id = message.get("id")

        if not sku or not modulo:
            raise ValueError(f"Mensagem inválida: 'sku' ({sku}) e 'module' ({modulo}) são obrigatórios.")

        # Executa operação no SAP GUI
        sap_data = self.manipulator.request_item(sku=str(sku), modulo=str(modulo))
        
        # Anexa metadados da requisição
        if msg_id:
            sap_data["id"] = msg_id

        # Publica resultado no RabbitMQ
        self.producer.publish(sap_data)

        return sap_data
