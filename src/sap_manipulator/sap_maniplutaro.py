from src.core.sap_manipulator import SapManipulator, SapConnectionError, SapExecutionError

# Backward compatibility alias
SapManiplutaro = SapManipulator

if __name__ == "__main__":
    app = SapManipulator()
    app.request_item(sku="40111115", modulo="sd21")