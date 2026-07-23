import win32com.client

SapGuiAuto = win32com.client.GetObject("SAPGUI")
application = SapGuiAuto.GetScriptingEngine
connection = application.Children(0)
session = connection.Children(0)
def realizar_lt01(sku, modulo):
    lote = None
    session.findById("wnd[0]/tbar[0]/okcd").text = "/nlt01"
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[0]/usr/ctxtLTAK-LGNUM").text = "b02"
    session.findById("wnd[0]/usr/ctxtLTAK-BWLVS").text = "998"
    session.findById("wnd[0]/usr/ctxtLTAP-MATNR").text = str(sku)
    session.findById("wnd[0]/usr/txtRL03T-ANFME").text = "999999999"
    session.findById("wnd[0]/usr/ctxtLTAP-WERKS").text = "brad"
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[0]/usr/ctxtLTAP-NLTYP").text = "ws5"
    session.findById("wnd[0]/usr/txtLTAP-NLPLA").text = f"w{str(modulo)}"
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[0]/usr/chkRL03T-SQUIT").selected = True
    posicao = session.findById("wnd[0]/usr/txtLTAP-VLPLA").text
    try:
        lote = session.findById("wnd[0]/usr/ctxtLTAP-CHARG").text
    except:
        pass

    su = session.findById("wnd[0]/usr/ctxtLTAP-VLENR").text
    modulo = session.findById("wnd[0]/usr/txtLTAP-NLPLA").text
    quantity = session.findById("wnd[0]/usr/txtLTAP-NSOLA").text

    print(posicao)
    print(lote)
    print(su)
    print(modulo)
    print(quantity)



def listar_componentes(obj, caminho=""):
    try:
        for i in range(obj.Children.Count):
            filho = obj.Children(i)

            novo_caminho = f"{caminho}/{i}"

            print(
                novo_caminho,
                filho.Type,
                getattr(filho, "Name", ""),
                getattr(filho, "Text", "")
            )

            listar_componentes(filho, novo_caminho)

    except:
        pass

realizar_lt01(40111115, "fm07")
#listar_componentes(session.findById("wnd[0]"))

