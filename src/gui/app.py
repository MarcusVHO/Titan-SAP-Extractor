import queue
import threading
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

from src.config.app_config import config
from src.core.sap_manipulator import SapManipulator, SapConnectionError
from src.messaging.rabbit_connection import RabbitConnectionManager
from src.messaging.rabbit_producer import RabbitProducer
from src.messaging.rabbit_consumer import RabbitConsumer
from src.services.sap_service import SapService

# Set default CustomTkinter appearance to Light
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class SettingsDialog(ctk.CTkToplevel):
    """
    Modal de Configurações para ajustar Host, Porta, Usuário e Senha do RabbitMQ.
    """

    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.title("⚙️ Configurações de Conexão")
        self.geometry("450x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_save_callback = on_save_callback
        self.configure(fg_color="#F8F9FA")

        # Header
        header = ctk.CTkLabel(
            self,
            text="⚙️ Configuração do RabbitMQ",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#D32F2F"
        )
        header.pack(pady=(20, 15))

        # Form Frame
        form_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E0E0E0")
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        form_frame.grid_columnconfigure(1, weight=1)

        # Host
        ctk.CTkLabel(form_frame, text="Host:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=15, pady=10)
        self.entry_host = ctk.CTkEntry(form_frame, placeholder_text="localhost")
        self.entry_host.insert(0, config.RABBITMQ_HOST)
        self.entry_host.grid(row=0, column=1, sticky="ew", padx=(0, 15), pady=10)

        # Port
        ctk.CTkLabel(form_frame, text="Porta:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=15, pady=10)
        self.entry_port = ctk.CTkEntry(form_frame, placeholder_text="5672")
        self.entry_port.insert(0, str(config.RABBITMQ_PORT))
        self.entry_port.grid(row=1, column=1, sticky="ew", padx=(0, 15), pady=10)

        # User
        ctk.CTkLabel(form_frame, text="Usuário:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="w", padx=15, pady=10)
        self.entry_user = ctk.CTkEntry(form_frame, placeholder_text="guest")
        self.entry_user.insert(0, config.RABBITMQ_USER)
        self.entry_user.grid(row=2, column=1, sticky="ew", padx=(0, 15), pady=10)

        # Password
        ctk.CTkLabel(form_frame, text="Senha:", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="w", padx=15, pady=10)
        self.entry_pass = ctk.CTkEntry(form_frame, show="*", placeholder_text="guest")
        self.entry_pass.insert(0, config.RABBITMQ_PASSWORD)
        self.entry_pass.grid(row=3, column=1, sticky="ew", padx=(0, 15), pady=10)

        # Info Box (Fixed Queues)
        info_lbl = ctk.CTkLabel(
            form_frame,
            text="📌 Filas de Sistema: sap.execute.queue | sap.response.queue",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#F57F17",
            fg_color="#FFFDE7",
            corner_radius=6,
            pady=6
        )
        info_lbl.grid(row=4, column=0, columnspan=2, sticky="ew", padx=15, pady=(5, 10))

        # Save Button
        btn_save = ctk.CTkButton(
            self,
            text="💾 Salvar Configurações",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            text_color="#FFFFFF",
            height=38,
            command=self._save
        )
        btn_save.pack(fill="x", padx=20, pady=(0, 20))

    def _save(self):
        try:
            host = self.entry_host.get().strip()
            port = int(self.entry_port.get().strip())
            user = self.entry_user.get().strip()
            password = self.entry_pass.get().strip()

            config.update_connection(host, port, user, password)
            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Valor inválido informado: {str(e)}", parent=self)


class TitanSapManipulatorApp(ctk.CTk):
    """
    Aplicação Desktop de Página Única Titan-SAP-Manipulator.
    Design predominantemente Light (branco) com detalhes em vermelho e amarelo.
    """

    def __init__(self):
        super().__init__()

        self.title("Titan-SAP-Manipulator - Automação SAP & RabbitMQ")
        self.geometry("1050x720")
        self.minsize(920, 620)
        self.configure(fg_color="#F8F9FA")

        # Thread safe message queues
        self.log_queue = queue.Queue()
        self.metric_queue = queue.Queue()

        # Core Services & State
        self.is_consuming = False
        self.consumer_thread = None
        self.rabbit_manager = None
        self.consumer = None
        self.sap_manipulator = SapManipulator()

        # Metrics counters
        self.cnt_processed = 0
        self.cnt_success = 0
        self.cnt_error = 0
        self.last_item_str = "Nenhum"

        # Build UI
        self._build_ui()

        # Check SAP Connection asynchronously on startup
        self._check_sap_status()

        # GUI queue update loop
        self.after(100, self._process_ui_queues)

    def _build_ui(self):
        """Constrói a interface de página única."""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------------
        # 1. HEADER BAR (Branco com detalhes em Vermelho e Amarelo)
        # -------------------------------------------------------------------
        header_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color="#FFFFFF",
            border_width=2,
            border_color="#D32F2F"
        )
        header_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        # Title & Logo
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        ctk.CTkLabel(
            title_box,
            text="⚡ TITAN-SAP-MANIPULATOR",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#D32F2F"
        ).pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="  v2.0.0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F57F17"
        ).pack(side="left")

        # Status Indicators Frame
        status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        status_frame.grid(row=0, column=2, padx=15, pady=12, sticky="e")

        self.lbl_rabbit_status = ctk.CTkLabel(
            status_frame,
            text="● RabbitMQ: Inativo",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#C62828",
            fg_color="#FFEBEE",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.lbl_rabbit_status.pack(side="left", padx=5)

        self.lbl_sap_status = ctk.CTkLabel(
            status_frame,
            text="● SAP GUI: Checando...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F57F17",
            fg_color="#FFFDE7",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.lbl_sap_status.pack(side="left", padx=5)

        btn_reconnect_sap = ctk.CTkButton(
            status_frame,
            text="🔄 Reconectar SAP",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            text_color="#FFFFFF",
            width=110,
            height=32,
            command=self._check_sap_status
        )
        btn_reconnect_sap.pack(side="left", padx=5)

        # Settings Button
        btn_settings = ctk.CTkButton(
            status_frame,
            text="⚙️ Configurações",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#FBC02D",
            hover_color="#F57F17",
            text_color="#212121",
            width=120,
            height=32,
            command=self._open_settings
        )
        btn_settings.pack(side="left", padx=(10, 0))

        # -------------------------------------------------------------------
        # 2. METRICS CARDS ROW (White Cards with Red & Yellow Details)
        # -------------------------------------------------------------------
        metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        metrics_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        for i in range(4):
            metrics_frame.grid_columnconfigure(i, weight=1)

        # Card 1: Processados
        card1 = ctk.CTkFrame(metrics_frame, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#E0E0E0")
        card1.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkFrame(card1, height=4, fg_color="#D32F2F", corner_radius=0).pack(fill="x") # Red Top Accent line
        ctk.CTkLabel(card1, text="MENSAGENS PROCESSADAS", font=ctk.CTkFont(size=10, weight="bold"), text_color="#757575").pack(anchor="w", padx=15, pady=(8, 2))
        self.lbl_val_processed = ctk.CTkLabel(card1, text="0", font=ctk.CTkFont(size=24, weight="bold"), text_color="#212121")
        self.lbl_val_processed.pack(anchor="w", padx=15, pady=(0, 8))

        # Card 2: Sucessos
        card2 = ctk.CTkFrame(metrics_frame, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#E0E0E0")
        card2.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkFrame(card2, height=4, fg_color="#2E7D32", corner_radius=0).pack(fill="x") # Green Top Accent line
        ctk.CTkLabel(card2, text="SUCESSOS SAP", font=ctk.CTkFont(size=10, weight="bold"), text_color="#757575").pack(anchor="w", padx=15, pady=(8, 2))
        self.lbl_val_success = ctk.CTkLabel(card2, text="0", font=ctk.CTkFont(size=24, weight="bold"), text_color="#2E7D32")
        self.lbl_val_success.pack(anchor="w", padx=15, pady=(0, 8))

        # Card 3: Erros
        card3 = ctk.CTkFrame(metrics_frame, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#E0E0E0")
        card3.grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkFrame(card3, height=4, fg_color="#D32F2F", corner_radius=0).pack(fill="x") # Red Accent
        ctk.CTkLabel(card3, text="FALHAS / ERROS", font=ctk.CTkFont(size=10, weight="bold"), text_color="#757575").pack(anchor="w", padx=15, pady=(8, 2))
        self.lbl_val_errors = ctk.CTkLabel(card3, text="0", font=ctk.CTkFont(size=24, weight="bold"), text_color="#C62828")
        self.lbl_val_errors.pack(anchor="w", padx=15, pady=(0, 8))

        # Card 4: Último SKU
        card4 = ctk.CTkFrame(metrics_frame, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#E0E0E0")
        card4.grid(row=0, column=3, padx=(5, 0), sticky="ew")
        ctk.CTkFrame(card4, height=4, fg_color="#FBC02D", corner_radius=0).pack(fill="x") # Yellow Accent
        ctk.CTkLabel(card4, text="ÚLTIMO SKU PROCESSADO", font=ctk.CTkFont(size=10, weight="bold"), text_color="#757575").pack(anchor="w", padx=15, pady=(8, 2))
        self.lbl_val_last_item = ctk.CTkLabel(card4, text="Nenhum", font=ctk.CTkFont(size=15, weight="bold"), text_color="#F57F17")
        self.lbl_val_last_item.pack(anchor="w", padx=15, pady=(0, 8))

        # -------------------------------------------------------------------
        # 3. MAIN BODY (CONTROL BAR & LIVE TERMINAL LOG)
        # -------------------------------------------------------------------
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="nsew")
        body_frame.grid_rowconfigure(1, weight=1)
        body_frame.grid_columnconfigure(0, weight=1)

        # Main Action Bar (Central Start/Stop Control)
        control_bar = ctk.CTkFrame(body_frame, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E0E0E0")
        control_bar.grid(row=0, column=0, padx=0, pady=(0, 10), sticky="ew")
        control_bar.grid_columnconfigure(0, weight=1)

        self.btn_toggle_consumer = ctk.CTkButton(
            control_bar,
            text="▶️ Iniciar Consumidor RabbitMQ",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            text_color="#FFFFFF",
            height=46,
            command=self._toggle_consumer
        )
        self.btn_toggle_consumer.pack(fill="x", padx=15, pady=12)

        # Terminal Log Container
        log_container = ctk.CTkFrame(body_frame, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E0E0E0")
        log_container.grid(row=1, column=0, sticky="nsew")
        log_container.grid_rowconfigure(1, weight=1)
        log_container.grid_columnconfigure(0, weight=1)

        # Log Header
        log_header = ctk.CTkFrame(log_container, fg_color="#FFFDE7", corner_radius=8) # Amarelo bem claro
        log_header.grid(row=0, column=0, padx=12, pady=10, sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_header,
            text="🖥️ Log de Operações em Tempo Real",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#D32F2F"
        ).grid(row=0, column=0, sticky="w", padx=10)

        self.chk_autoscroll = ctk.CTkCheckBox(
            log_header,
            text="Auto-scroll",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#424242",
            fg_color="#D32F2F",
            checkmark_color="#FFFFFF"
        )
        self.chk_autoscroll.select()
        self.chk_autoscroll.grid(row=0, column=1, padx=5)

        btn_clear_log = ctk.CTkButton(
            log_header,
            text="🗑️ Limpar",
            width=80,
            height=28,
            fg_color="#FBC02D",
            hover_color="#F57F17",
            text_color="#212121",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._clear_logs
        )
        btn_clear_log.grid(row=0, column=2, padx=(5, 10))

        # Rich Console Text Box (Fundo branco/claro com texto nítido)
        self.log_textbox = ctk.CTkTextbox(
            log_container,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#FAFAFA",
            text_color="#212121",
            corner_radius=8,
            border_width=1,
            border_color="#EEEEEE"
        )
        self.log_textbox.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        # Welcome message
        self.append_log("==========================================================================", "INFO")
        self.append_log(f"⚡ Titan-SAP-Manipulator v{config.VERSION} Pronto.", "SUCCESS")
        self.append_log("Fila de Execução: sap.execute.queue | Fila de Resposta: sap.response.queue", "HIGHLIGHT")
        self.append_log("==========================================================================", "INFO")

    # -------------------------------------------------------------------
    # EVENT HANDLERS & THREAD QUEUE LOGIC
    # -------------------------------------------------------------------
    def _open_settings(self):
        """Abre a janela popup de configurações."""
        SettingsDialog(self, on_save_callback=self._on_settings_saved)

    def _on_settings_saved(self):
        self.append_log(f"Configurações atualizadas: Host={config.RABBITMQ_HOST}, Porta={config.RABBITMQ_PORT}, Usuário={config.RABBITMQ_USER}", "HIGHLIGHT")

    def append_log(self, text: str, level: str = "INFO"):
        """Adiciona log ao console da interface."""
        now = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{now}] [{level}] "
        full_line = f"{prefix}{text}\n"

        self.log_textbox.insert("end", full_line)
        if self.chk_autoscroll.get() == 1:
            self.log_textbox.see("end")

    def _queue_log(self, text: str, level: str = "INFO"):
        self.log_queue.put((text, level))

    def _queue_metric(self, metric_data: dict):
        self.metric_queue.put(metric_data)

    def _process_ui_queues(self):
        """Atualiza a UI a partir da fila das threads secundárias."""
        while not self.log_queue.empty():
            try:
                text, level = self.log_queue.get_nowait()
                self.append_log(text, level)
            except queue.Empty:
                break

        while not self.metric_queue.empty():
            try:
                data = self.metric_queue.get_nowait()
                self.cnt_processed += 1
                if data.get("status") == "SUCCESS":
                    self.cnt_success += 1
                    payload = data.get("payload", {})
                    sku = payload.get("sku", "N/A")
                    self.last_item_str = f"SKU {sku}"
                else:
                    self.cnt_error += 1

                self.lbl_val_processed.configure(text=str(self.cnt_processed))
                self.lbl_val_success.configure(text=str(self.cnt_success))
                self.lbl_val_errors.configure(text=str(self.cnt_error))
                self.lbl_val_last_item.configure(text=self.last_item_str)
            except queue.Empty:
                break

        self.after(100, self._process_ui_queues)

    def _check_sap_status(self):
        """Verifica a conexão com o SAP GUI e informa no terminal com guia de solução."""
        def run_check():
            self._queue_log("Verificando sessão do SAP GUI...", "INFO")
            try:
                self.sap_manipulator.connect()
                self.after(0, lambda: self.lbl_sap_status.configure(
                    text="● SAP GUI: Pronto",
                    text_color="#2E7D32",
                    fg_color="#E8F5E9"
                ))
                self._queue_log("✅ Sessão do SAP GUI identificada com sucesso!", "SUCCESS")
            except SapConnectionError as e:
                self.after(0, lambda: self.lbl_sap_status.configure(
                    text="● SAP GUI: Inativo",
                    text_color="#C62828",
                    fg_color="#FFEBEE"
                ))
                self._queue_log("⚠️ SAP GUI não foi identificado.", "WARNING")
                self._queue_log("------------------------------------------------------------------", "WARNING")
                self._queue_log("COMO ATIVAR O SCRIPTING NO SAP GUI:", "WARNING")
                self._queue_log("1. No SAP GUI aberto, acesse Opções -> Acessibilidade e Scripting -> Scripting.", "WARNING")
                self._queue_log("2. Marque a opção: 'Habilitar Scripting'.", "WARNING")
                self._queue_log("3. Desmarque: 'Notificar quando um script se conectar ao SAP GUI'.", "WARNING")
                self._queue_log("4. Certifique-se de estar logado em uma sessão do SAP.", "WARNING")
                self._queue_log("5. Clique no botão '🔄 Reconectar SAP' no topo da tela.", "WARNING")
                self._queue_log("------------------------------------------------------------------", "WARNING")

        threading.Thread(target=run_check, daemon=True).start()

    def _toggle_consumer(self):
        """Inicia ou para o consumidor RabbitMQ em background thread."""
        if not self.is_consuming:
            self.is_consuming = True
            self.btn_toggle_consumer.configure(
                text="⏹️ Parar Consumidor RabbitMQ",
                fg_color="#FBC02D",
                hover_color="#F57F17",
                text_color="#212121"
            )
            self.lbl_rabbit_status.configure(
                text="● RabbitMQ: Conectando...",
                text_color="#F57F17",
                fg_color="#FFFDE7"
            )

            self.consumer_thread = threading.Thread(target=self._run_consumer_loop, daemon=True)
            self.consumer_thread.start()
        else:
            self.is_consuming = False
            if self.consumer:
                self.consumer.stop()
            self._queue_log("Solicitação para parar o consumidor enviada...", "WARNING")
            self.btn_toggle_consumer.configure(
                text="▶️ Iniciar Consumidor RabbitMQ",
                fg_color="#D32F2F",
                hover_color="#B71C1C",
                text_color="#FFFFFF"
            )
            self.lbl_rabbit_status.configure(
                text="● RabbitMQ: Parado",
                text_color="#C62828",
                fg_color="#FFEBEE"
            )

    def _run_consumer_loop(self):
        """Loop de execução do consumidor RabbitMQ em background."""
        try:
            self._queue_log(f"Conectando ao RabbitMQ em {config.RABBITMQ_HOST}:{config.RABBITMQ_PORT}...", "INFO")
            self.rabbit_manager = RabbitConnectionManager(config)
            connection = self.rabbit_manager.create_connection()
            channel = self.rabbit_manager.get_channel()

            self.after(0, lambda: self.lbl_rabbit_status.configure(
                text="● RabbitMQ: Ativo",
                text_color="#2E7D32",
                fg_color="#E8F5E9"
            ))
            self._queue_log(f"✅ Conectado ao RabbitMQ! Fila de consumo: {config.EXECUTE_QUEUE}", "SUCCESS")

            producer = RabbitProducer(channel, config)
            sap_service = SapService(producer, self.sap_manipulator)

            self.consumer = RabbitConsumer(
                channel=channel,
                service=sap_service,
                cfg=config,
                log_callback=self._queue_log,
                metric_callback=self._queue_metric
            )

            self.consumer.start()

        except Exception as e:
            self._queue_log(f"❌ Erro na conexão RabbitMQ: {str(e)}", "ERROR")
            self.after(0, lambda: self.lbl_rabbit_status.configure(
                text="● RabbitMQ: Erro",
                text_color="#C62828",
                fg_color="#FFEBEE"
            ))
        finally:
            if self.rabbit_manager:
                self.rabbit_manager.close()
            self.is_consuming = False
            self.after(0, self._reset_consumer_button)

    def _reset_consumer_button(self):
        self.btn_toggle_consumer.configure(
            text="▶️ Iniciar Consumidor RabbitMQ",
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            text_color="#FFFFFF"
        )
        if "Ativo" not in self.lbl_rabbit_status.cget("text"):
            self.lbl_rabbit_status.configure(
                text="● RabbitMQ: Inativo",
                text_color="#C62828",
                fg_color="#FFEBEE"
            )

    def _clear_logs(self):
        self.log_textbox.delete("1.0", "end")


if __name__ == "__main__":
    app = TitanSapManipulatorApp()
    app.mainloop()
