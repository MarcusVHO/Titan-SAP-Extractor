import pythoncom
import win32com.client


class SapException(Exception):
    """Exceção base para operações do SAP."""
    pass


class SapConnectionError(SapException):
    """Exceção para falhas de conexão com o SAP GUI."""
    pass


class SapExecutionError(SapException):
    """Exceção para erros durante a execução de transações SAP."""
    pass


class SapManipulator:
    """
    Classe responsável por interagir diretamente com a interface do SAP GUI via COM Scripting.
    Encapsula transações e comandos com tratamento de erros orientado a objetos.
    """

    def __init__(self):
        try:
            pythoncom.CoInitialize()
            SapGuiAuto = win32com.client.GetObject("SAPGUI")
            application = SapGuiAuto.GetScriptingEngine
            connection = application.Children(0)
            self.session = connection.Children(0)
        except Exception:
            self.session = None

    def connect(self) -> bool:
        """Conecta com a sessão ativa do SAP GUI Scripting Engine."""
        try:
            pythoncom.CoInitialize()
        except Exception:
            pass

        errors = []
        sap_gui_auto = None

        # Tentativa 1: GetObject("SAPGUI") - Método padrão
        try:
            sap_gui_auto = win32com.client.GetObject("SAPGUI")
        except Exception as e1:
            errors.append(f"GetObject('SAPGUI'): {str(e1)}")

        # Tentativa 2: Dispatch("Sapgui.ScriptingCtrl.1") - Método alternativo
        if not sap_gui_auto:
            try:
                sap_gui_auto = win32com.client.Dispatch("Sapgui.ScriptingCtrl.1")
            except Exception as e2:
                errors.append(f"Dispatch('Sapgui.ScriptingCtrl.1'): {str(e2)}")

        if not sap_gui_auto:
            err_details = " | ".join(errors)
            raise SapConnectionError(
                "O SAP GUI não está respondendo ao Scripting COM.\n\n"
                "Para resolver:\n"
                "1. No SAP GUI, vá em Opções -> Acessibilidade e Scripting -> Scripting.\n"
                "2. Marque a opção 'Habilitar Scripting'.\n"
                "3. Certifique-se de estar logado em uma sessão do SAP GUI.\n"
                "4. Garanta que o SAP e a aplicação estão rodando no mesmo nível de privilégio (ambos como Usuário ou ambos como Administrador)."
            )

        try:
            application = sap_gui_auto.GetScriptingEngine
            if not application or application.Children.Count == 0:
                raise SapConnectionError("Nenhuma conexão SAP ativa encontrada no Scripting Engine.")

            connection = application.Children(0)
            if not connection or connection.Children.Count == 0:
                raise SapConnectionError("Nenhuma sessão SAP ativa aberta na conexão.")

            self.session = connection.Children(0)
            return True
        except Exception as e:
            self.session = None
            if isinstance(e, SapConnectionError):
                raise e
            raise SapConnectionError(f"Falha ao obter sessão do SAP GUI: {str(e)}") from e

    def is_connected(self) -> bool:
        """Verifica se a sessão SAP está conectada."""
        return self.session is not None

    def request_item(self, sku, modulo):
        try:
            pythoncom.CoInitialize()
        except Exception:
            pass

        self.connect()


        lote = None
        self.session.findById("wnd[0]/tbar[0]/okcd").text = "/nlt01"
        self.session.findById("wnd[0]").sendVKey(0)
        self.session.findById("wnd[0]/usr/ctxtLTAK-LGNUM").text = "b02"
        self.session.findById("wnd[0]/usr/ctxtLTAK-BWLVS").text = "998"
        self.session.findById("wnd[0]/usr/ctxtLTAP-MATNR").text = str(sku)
        self.session.findById("wnd[0]/usr/txtRL03T-ANFME").text = "999999999"
        self.session.findById("wnd[0]/usr/ctxtLTAP-WERKS").text = "brad"
        self.session.findById("wnd[0]").sendVKey(0)
        self.session.findById("wnd[0]/usr/ctxtLTAP-NLTYP").text = "ws5"
        self.session.findById("wnd[0]/usr/txtLTAP-NLPLA").text = f"w{str(modulo)}"
        self.session.findById("wnd[0]").sendVKey(0)
        self.session.findById("wnd[0]/usr/chkRL03T-SQUIT").selected = True
        posicao = self.session.findById("wnd[0]/usr/txtLTAP-VLPLA").text
        try:
            lote = self.session.findById("wnd[0]/usr/ctxtLTAP-CHARG").text
        except:
            pass

        su = self.session.findById("wnd[0]/usr/ctxtLTAP-VLENR").text
        modulo = self.session.findById("wnd[0]/usr/txtLTAP-NLPLA").text
        quantity:str = self.session.findById("wnd[0]/usr/txtLTAP-NSOLA").text
        quantity = quantity.replace(".", "").replace(",", ".")
        return {
            "position": posicao,
            "batch": lote,
            "su": su,
            "quantity":float(quantity),
            "module": modulo,
        }


if __name__ == "__main__":
    app = SapManipulator()
    app.request_item(sku="40111115", modulo="sd21")

