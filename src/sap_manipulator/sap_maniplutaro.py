import win32com.client
from pika.compat import long


class SapManipulator:
    def __init__(self):
        SapGuiAuto = win32com.client.GetObject("SAPGUI")
        application = SapGuiAuto.GetScriptingEngine
        connection = application.Children(0)
        self.session = connection.Children(0)


    def request_item(self, sku, modulo):

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
    app.request_item(sku="40111115",modulo="sd21")