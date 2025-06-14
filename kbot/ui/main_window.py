# kbot/ui/main_window.py

import sys
import traceback
from typing import Dict, Any
import os

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QTextEdit,
    QSplitter,
    QStatusBar,
    QMenuBar,
    QAction,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap, QImage
from PIL import Image

from core.bot_engine import BotWorker, BotState
from combat.combat_manager import CombatState
from ui.dialogs.window_selector import WindowSelectorDialog
from ui.dialogs.region_config import RegionConfigDialog
from ui.dialogs.skill_config import SkillConfigDialog
from ui.widgets.log_widget import LogWidget
from ui.widgets.status_widget import StatusWidget
from utils.exceptions import BotError


class TantraBotMainWindow(QMainWindow):

    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    pause_resume_signal = pyqtSignal()
    initialize_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tantra Bot v1.0.0 - by 0xkit")
        self.setMinimumSize(700, 400)

        from utils.logger import BotLogger

        self.logger = BotLogger("MainWindow")

        # --- LÓGICA DE HILOS ---
        self.bot_thread = QThread()
        self.bot_worker = BotWorker()

        # Mueve el worker al hilo. Esto es crucial.
        self.bot_worker.moveToThread(self.bot_thread)

        # El bot_engine ahora vive dentro del worker.
        self.bot_engine = self.bot_worker.bot_engine
        # ---------------------

        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._connect_signals()  # Conectará las señales al worker
        self._load_configuration()

        # Inicia el hilo. Ahora está esperando señales.
        self.bot_thread.started.connect(self.bot_worker.initialize_in_thread)
        self.bot_thread.start()

        # El refresh timer para la UI se queda en el hilo principal, lo cual es correcto.
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._update_ui)
        self.refresh_timer.start(1000)

    @pyqtSlot()
    def _select_window(self):
        """
        Abre el diálogo de selección, y si tiene éxito, le pasa el HWND al BotEngine
        para que este configure todos los subsistemas necesarios.
        """
        dialog = WindowSelectorDialog(self.bot_engine.window_manager, self)

        # El diálogo se cierra con `Accepted` solo si se seleccionó una ventana
        if dialog.exec_() == QDialog.Accepted:
            selected_hwnd = dialog.get_selected_window_hwnd()

            if selected_hwnd:
                # Llamamos al método centralizador del BotEngine
                if self.bot_engine.set_target_window(selected_hwnd):
                    window_info = (
                        self.bot_engine.window_manager.get_target_window_info()
                    )
                    self.current_window_label.setText(
                        f"Selected: {window_info['title']}"
                    )
                    self.status_bar.showMessage("Window selected and configured!", 2000)
                else:
                    QMessageBox.critical(
                        self, "Error", "Failed to set target window in the Bot Engine."
                    )

    @pyqtSlot()
    def _test_pixels(self):
        """
        Realiza una prueba de captura de un área específica y la muestra ampliada.
        """
        if not self.bot_engine.window_manager.target_window:
            QMessageBox.warning(
                self, "Test Error", "Please select a game window first."
            )
            return

        try:
            self.logger.info("Performing pixel accuracy test on UI area...")
            regions = self.bot_engine.config_manager.get_regions()

            # --- LÓGICA MÁS EFICIENTE ---
            # 1. Definimos el área de la UI que nos interesa.
            ui_capture_area = (0, 0, 300, 250)

            # 2. Le pedimos al PixelAnalyzer que capture y dibuje SOLO esa área.
            ui_debug_image = self.bot_engine.pixel_analyzer.create_debug_image(
                regions, capture_area=ui_capture_area
            )

            # 3. Hacemos zoom para verla mejor en el diálogo.
            zoom_factor = 1
            zoomed_image = ui_debug_image.resize(
                (
                    ui_debug_image.width * zoom_factor,
                    ui_debug_image.height * zoom_factor,
                ),
                Image.NEAREST,
            )
            # --- FIN DE LA LÓGICA EFICIENTE ---

            dialog = QDialog(self)
            dialog.setWindowTitle("Pixel Accuracy Test Results (UI Zoom)")
            layout = QVBoxLayout(dialog)

            info_label = QLabel(
                "Zoomed capture of the top-left corner of the game window.\n"
                "Check if the colored boxes correctly cover the HP, MP, and Target bars."
            )
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

            q_image = QImage(
                zoomed_image.tobytes("raw", "RGB"),
                zoomed_image.width,
                zoomed_image.height,
                QImage.Format_RGB888,
            )
            pixmap = QPixmap.fromImage(q_image)
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setStyleSheet("border: 2px solid black;")
            layout.addWidget(image_label)

            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            dialog.exec_()
            self.logger.info("Pixel accuracy test finished.")

        except Exception as e:
            self.logger.error(f"Pixel test failed: {e}")
            QMessageBox.critical(
                self,
                "Test Error",
                f"Could not perform pixel test: {e}\n\n{traceback.format_exc()}",
            )

    @pyqtSlot()
    def _test_ocr(self):
        if not self.bot_engine.window_manager.target_window:
            QMessageBox.warning(
                self,
                "Test Error",
                "Please select a game window first using the 'Select Game Window' button.",
            )
            return
        try:
            self.logger.info("Performing OCR test...")
            regions = self.bot_engine.config_manager.get_regions()
            name_region = regions.get("target_name")
            if not name_region:
                QMessageBox.warning(
                    self, "Configuration Error", "Target name region is not configured."
                )
                return
            QMessageBox.information(
                self,
                "Prepare for OCR Test",
                "Please select a target in the game now. The test will run when you click OK.",
            )
            result = self.bot_engine.pixel_analyzer.test_ocr_accuracy(name_region)
            dialog = QDialog(self)
            dialog.setWindowTitle("OCR Test Results")
            layout = QVBoxLayout(dialog)
            result_text = f"<b>Region:</b> {result['region_coords']}<br><b>Extracted:</b> <span style='color:blue;'>{result['extracted_name']}</span>"
            layout.addWidget(QLabel(result_text))
            h_layout = QHBoxLayout()
            orig_v_layout = QVBoxLayout()
            orig_v_layout.addWidget(QLabel("<b>Original:</b>"))
            orig_pixmap = QPixmap.fromImage(
                QImage(
                    result["original_image"].tobytes("raw", "RGB"),
                    result["original_image"].width,
                    result["original_image"].height,
                    QImage.Format_RGB888,
                )
            )
            orig_label = QLabel()
            orig_label.setPixmap(orig_pixmap.scaled(200, 50, Qt.KeepAspectRatio))
            orig_v_layout.addWidget(orig_label)
            h_layout.addLayout(orig_v_layout)
            proc_v_layout = QVBoxLayout()
            proc_v_layout.addWidget(QLabel("<b>Processed:</b>"))
            proc_pixmap = QPixmap.fromImage(
                QImage(
                    result["processed_image"].tobytes("raw", "L"),
                    result["processed_image"].width,
                    result["processed_image"].height,
                    QImage.Format_Grayscale8,
                )
            )
            proc_label = QLabel()
            proc_label.setPixmap(proc_pixmap.scaled(200, 50, Qt.KeepAspectRatio))
            proc_v_layout.addWidget(proc_label)
            h_layout.addLayout(proc_v_layout)
            layout.addLayout(h_layout)
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            dialog.exec_()
            self.logger.info(f"OCR test finished. Result: '{result['extracted_name']}'")
        except Exception as e:
            self.logger.error(f"OCR test failed: {e}")
            QMessageBox.critical(
                self,
                "Test Error",
                f"Could not perform OCR test: {e}\n\n{traceback.format_exc()}",
            )

    # --- El resto del archivo sin cambios ---
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        left_panel_widget = QWidget()
        left_layout = QVBoxLayout(left_panel_widget)
        left_layout.setAlignment(Qt.AlignTop)
        self._create_main_control_buttons(left_layout)
        self._create_window_management_group(left_layout)
        self._create_options_group(left_layout)
        self._create_mob_whitelist_group(left_layout)
        self.save_changes_btn = QPushButton("Save All Changes")
        left_layout.addWidget(self.save_changes_btn)
        left_layout.addStretch(1)
        main_splitter.addWidget(left_panel_widget)
        right_panel_widget = QWidget()
        right_layout = QVBoxLayout(right_panel_widget)
        right_splitter = QSplitter(Qt.Vertical)
        right_layout.addWidget(right_splitter)
        top_info_panel = QWidget()
        top_info_layout = QHBoxLayout(top_info_panel)
        self.status_widget = StatusWidget()
        top_info_layout.addWidget(self.status_widget, 1)
        self._create_stats_group(top_info_layout)
        right_splitter.addWidget(top_info_panel)
        self.log_widget = LogWidget()
        right_splitter.addWidget(self.log_widget)
        main_splitter.addWidget(right_panel_widget)
        main_splitter.setSizes([350, 850])
        right_splitter.setSizes([200, 600])

    def _create_main_control_buttons(self, parent_layout):
        control_group = QGroupBox("Bot Control")
        control_layout = QVBoxLayout(control_group)
        button_layout = QHBoxLayout()
        self.start_stop_btn = QPushButton("Start Bot")
        self.start_stop_btn.setMinimumHeight(40)
        button_layout.addWidget(self.start_stop_btn)
        self.pause_resume_btn = QPushButton("Pause")
        self.pause_resume_btn.setMinimumHeight(40)
        self.pause_resume_btn.setEnabled(False)
        button_layout.addWidget(self.pause_resume_btn)
        control_layout.addLayout(button_layout)
        self.bot_status_label = QLabel("Status: Stopped")
        self.bot_status_label.setStyleSheet("font-weight: bold;")
        control_layout.addWidget(self.bot_status_label)
        parent_layout.addWidget(control_group)

    def _create_window_management_group(self, parent_layout):
        window_group = QGroupBox("Window Management")
        window_layout = QVBoxLayout(window_group)
        self.select_window_btn = QPushButton("Select Game Window")
        window_layout.addWidget(self.select_window_btn)
        self.current_window_label = QLabel("No window selected")
        window_layout.addWidget(self.current_window_label)
        parent_layout.addWidget(window_group)

    def _create_options_group(self, parent_layout):
        options_group = QGroupBox("Options")
        options_layout = QGridLayout(options_group)

        # Fila 0: Checkbox de Auto Potions
        self.auto_pots_cb = QCheckBox("Auto Potions (HP / MP)")
        self.auto_pots_cb.setChecked(True)
        options_layout.addWidget(self.auto_pots_cb, 0, 0, 1, 2)  # Ocupa 2 columnas

        # Fila 1: Checkbox de Looteo
        self.enable_looting_cb = QCheckBox("Enable Looting")
        self.enable_looting_cb.setToolTip(
            "If checked, the bot will press the loot key after each kill."
        )
        self.enable_looting_cb.setChecked(True)
        options_layout.addWidget(self.enable_looting_cb, 1, 0, 1, 2)  # Ocupa 2 columnas

        # Fila 2: Checkbox de Modo Asistir
        self.assist_mode_cb = QCheckBox("Assist Mode")
        self.assist_mode_cb.setToolTip(
            "If checked, the bot will not search for targets and will use the 'Assist' skill instead."
        )
        self.assist_mode_cb.setChecked(False)  # Por defecto desactivado
        options_layout.addWidget(self.assist_mode_cb, 2, 0, 1, 2)  # Ocupa 2 columnas

        # Fila 3: Potion Threshold
        options_layout.addWidget(QLabel("Potion Threshold:"), 3, 0)
        self.potion_threshold_spin = QSpinBox()
        self.potion_threshold_spin.setRange(1, 99)
        self.potion_threshold_spin.setValue(70)
        self.potion_threshold_spin.setSuffix("%")
        options_layout.addWidget(self.potion_threshold_spin, 3, 1)

        # Fila 4: OCR Match Tolerance
        options_layout.addWidget(QLabel("OCR Match Tolerance:"), 4, 0)
        self.ocr_tolerance_spin = QSpinBox()
        self.ocr_tolerance_spin.setRange(50, 100)
        self.ocr_tolerance_spin.setValue(85)
        self.ocr_tolerance_spin.setSuffix("%")
        self.ocr_tolerance_spin.setToolTip(
            "How similar OCR text must be to a whitelist entry (e.g., 85%)."
        )
        options_layout.addWidget(self.ocr_tolerance_spin, 4, 1)

        # Fila 5: Skill Interval
        options_layout.addWidget(QLabel("Skill Interval:"), 5, 0)
        self.skill_interval_spin = QDoubleSpinBox()
        self.skill_interval_spin.setRange(0.5, 5.0)
        self.skill_interval_spin.setSingleStep(0.1)
        self.skill_interval_spin.setValue(1.8)
        self.skill_interval_spin.setSuffix(" s")
        self.skill_interval_spin.setToolTip(
            "Global Cooldown (GCD). Time to wait between using skills."
        )
        options_layout.addWidget(self.skill_interval_spin, 5, 1)

        # Fila 6: Post Combat Delay
        options_layout.addWidget(QLabel("Post-Combat Delay:"), 6, 0)
        self.post_combat_delay_spin = QDoubleSpinBox()
        self.post_combat_delay_spin.setRange(0.0, 10.0)
        self.post_combat_delay_spin.setSingleStep(0.1)
        self.post_combat_delay_spin.setValue(1.5)
        self.post_combat_delay_spin.setSuffix(" s")
        self.post_combat_delay_spin.setToolTip(
            "Time to wait after looting before searching for a new target."
        )
        options_layout.addWidget(self.post_combat_delay_spin, 6, 1)

        parent_layout.addWidget(options_group)

    def _create_mob_whitelist_group(self, parent_layout):
        whitelist_group = QGroupBox("Mob Whitelist")
        whitelist_layout = QVBoxLayout(whitelist_group)
        whitelist_layout.addWidget(QLabel("Allowed mobs (one per line):"))
        self.whitelist_edit = QTextEdit()
        self.whitelist_edit.setPlainText("Byokbo")
        whitelist_layout.addWidget(self.whitelist_edit)
        parent_layout.addWidget(whitelist_group)

    def _create_stats_group(self, parent_layout):
        stats_group = QGroupBox("Session Statistics")
        stats_layout = QGridLayout(stats_group)
        stats_layout.addWidget(QLabel("Runtime:"), 0, 0)
        self.runtime_label = QLabel("00:00:00")
        stats_layout.addWidget(self.runtime_label, 0, 1)
        stats_layout.addWidget(QLabel("Targets Killed:"), 1, 0)
        self.targets_killed_label = QLabel("0")
        stats_layout.addWidget(self.targets_killed_label, 1, 1)
        stats_layout.addWidget(QLabel("Skills Used:"), 2, 0)
        self.skills_used_label = QLabel("0")
        stats_layout.addWidget(self.skills_used_label, 2, 1)
        stats_layout.addWidget(QLabel("Stuck (Combat):"), 3, 0)
        self.stuck_combat_label = QLabel("0")
        stats_layout.addWidget(self.stuck_combat_label, 3, 1)
        stats_layout.addWidget(QLabel("Stuck (Search):"), 4, 0)
        self.stuck_search_label = QLabel("0")
        stats_layout.addWidget(self.stuck_search_label, 4, 1)
        stats_layout.setColumnStretch(1, 1)
        parent_layout.addWidget(stats_group, 1)

    def _setup_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        load_profile_action = QAction("Load Profile...", self)
        load_profile_action.triggered.connect(self._load_profile)
        file_menu.addAction(load_profile_action)

        save_profile_as_action = QAction("Save Profile As...", self)
        save_profile_as_action.triggered.connect(self._save_profile_as)
        file_menu.addAction(save_profile_as_action)
        save_action = QAction("Save All Changes", self)
        save_action.triggered.connect(self._save_configuration)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        tools_menu = menubar.addMenu("Tools")
        regions_action = QAction("Configure Regions", self)
        regions_action.triggered.connect(self._configure_regions)
        tools_menu.addAction(regions_action)
        skills_action = QAction("Configure Skills", self)
        skills_action.triggered.connect(self._open_skill_config)
        tools_menu.addAction(skills_action)
        tools_menu.addSeparator()
        test_pixels_action = QAction("Test Pixel Accuracy", self)
        test_pixels_action.triggered.connect(self._test_pixels)
        tools_menu.addAction(test_pixels_action)
        test_ocr_action = QAction("Test OCR", self)
        test_ocr_action.triggered.connect(self._test_ocr)
        tools_menu.addAction(test_ocr_action)
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.bot_state_label = QLabel("Stopped")
        self.status_bar.addWidget(self.bot_state_label)
        self.status_bar.addPermanentWidget(QLabel("Tantra Bot v1.0.0"))

    def _connect_signals(self):
        # Conecta las señales de la UI (hilo principal) a los slots del worker (hilo del bot)
        self.start_signal.connect(self.bot_worker.start_bot)
        self.stop_signal.connect(self.bot_worker.stop_bot)
        self.pause_resume_signal.connect(self.bot_worker.pause_resume_bot)

        # Conecta las señales del bot_engine (hilo del bot) a los slots de la UI (hilo principal)
        # Qt maneja esta comunicación entre hilos automáticamente.
        self.bot_engine.state_changed.connect(self._on_bot_state_changed)
        self.bot_engine.vitals_updated.connect(self._on_vitals_updated)
        self.bot_engine.error_occurred.connect(self._on_error_occurred)
        self.bot_engine.logger.log_message.connect(self.log_widget.add_message)

        # Conecta los botones de la UI
        self.start_stop_btn.clicked.connect(self._toggle_bot)
        self.pause_resume_btn.clicked.connect(self._pause_resume_bot)
        self.select_window_btn.clicked.connect(self._select_window)
        self.save_changes_btn.clicked.connect(self._save_configuration)

    def _load_configuration(self):
        try:
            config = self.bot_engine.config_manager
            self.auto_pots_cb.setChecked(config.get_option("auto_pots", True))
            self.potion_threshold_spin.setValue(
                config.get_option("potion_threshold", 70)
            )

            self.ocr_tolerance_spin.setValue(config.get_option("ocr_tolerance", 85))

            self.enable_looting_cb.setChecked(
                config.get_option("enable_looting", True)
            )  # Por defecto activado
            self.assist_mode_cb.setChecked(config.get_option("assist_mode", False))

            # Leemos el timing completo y luego el valor específico
            timing = config.get_timing()
            self.skill_interval_spin.setValue(timing.get("skill_interval", 1.8))
            self.post_combat_delay_spin.setValue(timing.get("post_combat_delay", 2.0))

            whitelist = config.get_whitelist()
            self.whitelist_edit.setPlainText("\n".join(whitelist))
            self.status_bar.showMessage("Configuration loaded", 2000)
        except Exception as e:
            QMessageBox.warning(
                self, "Load Error", f"Failed to load configuration: {e}"
            )

    def _save_configuration(self):
        """
        Aplica los cambios de la UI a la configuración en memoria Y LUEGO la guarda en el disco.
        """
        try:
            # 1. Aplicamos los cambios de la UI al BotEngine.
            self._apply_ui_settings()

            # 2. Le pedimos al BotEngine que guarde su estado de configuración actual.
            if self.bot_engine.save_config():
                QMessageBox.information(
                    self, "Success", "Configuration saved successfully!"
                )
                self.logger.info("Configuration saved successfully via Save button.")
            else:
                QMessageBox.critical(
                    self, "Save Error", "Failed to save configuration."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Save Error", f"An unexpected error occurred while saving: {e}"
            )

    @pyqtSlot()
    def _pause_resume_bot(self):
        # Emite una señal en lugar de llamar al método.
        self.pause_resume_signal.emit()  # <-- EMITE SEÑAL

    @pyqtSlot()
    def _toggle_bot(self):
        # Ya no llama a los métodos directamente. Emite señales.
        if self.bot_engine.get_state() == "stopped":
            if not self.bot_engine.window_manager.target_window:
                QMessageBox.warning(
                    self,
                    "No Window Selected",
                    "Please select a game window before starting.",
                )
                return
            self._apply_ui_settings()
            self.start_signal.emit()  # <-- EMITE SEÑAL
        else:
            self.stop_signal.emit()  # <-- EMITE SEÑAL

    def _apply_ui_settings(self):
        """
        Toma los valores de la UI y los pasa al BotEngine para que actualice sus componentes.
        """
        try:
            config = self.bot_engine.config_manager

            config.set_option("auto_pots", self.auto_pots_cb.isChecked())
            config.set_option("potion_threshold", self.potion_threshold_spin.value())
            config.set_option("enable_looting", self.enable_looting_cb.isChecked())
            config.set_option("assist_mode", self.assist_mode_cb.isChecked())
            config.set_option("ocr_tolerance", self.ocr_tolerance_spin.value())

            # Leemos el diccionario de timing actual para no perder otros valores.
            timing = config.get_timing()

            # --- LÍNEA CORREGIDA ---
            # El segundo argumento de round() debe ser un entero para los decimales.
            timing["skill_interval"] = round(self.skill_interval_spin.value(), 2)
            # -----------------------

            timing["post_combat_delay"] = round(self.post_combat_delay_spin.value(), 2)

            # Guardamos el diccionario COMPLETO y MODIFICADO en el ConfigManager.
            config.set_timing(timing)

            # Lista blanca de mobs
            whitelist_text = self.whitelist_edit.toPlainText()
            whitelist = [
                line.strip() for line in whitelist_text.splitlines() if line.strip()
            ]
            config.set_whitelist(whitelist)

            # Le pedimos al BotEngine que aplique estos cambios a sus componentes.
            self.bot_engine.update_components_from_config()
            self.logger.info("UI settings applied to bot engine.")
        except Exception as e:
            self.logger.error(f"Failed to apply UI settings: {e}")
            # Es buena idea mostrar el error al usuario también.
            QMessageBox.critical(
                self, "Apply Settings Error", f"Could not apply settings:\n{e}"
            )

    @pyqtSlot()
    def _configure_regions(self):
        dialog = RegionConfigDialog(self.bot_engine, self)
        if dialog.exec_() == QDialog.Accepted:
            self.status_bar.showMessage("Region configuration updated", 2000)

    @pyqtSlot()
    def _open_skill_config(self):
        dialog = SkillConfigDialog(
            skill_manager=self.bot_engine.skill_manager,
            config_manager=self.bot_engine.config_manager,
            parent=self,
        )
        if dialog.exec_() == QDialog.Accepted:
            self.status_bar.showMessage("Skills configuration updated", 3000)

    @pyqtSlot()
    def _show_about(self):
        QMessageBox.about(self, "About Tantra Bot", "Tantra Bot v1.0.0 by 0xkit")

    def _update_ui(self):
        try:
            state = self.bot_engine.get_state()
            self.bot_status_label.setText(f"Status: {state.title()}")
            self.bot_state_label.setText(state.title())
            vitals = self.bot_engine.get_vitals()
            if vitals:
                self.status_widget.update_vitals(vitals)
            stats = self.bot_engine.get_stats()
            runtime_seconds = int(stats.get("current_runtime", 0))
            hours, remainder = divmod(runtime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.runtime_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")
            self.targets_killed_label.setText(str(stats.get("targets_lost", 0)))
            self.skills_used_label.setText(str(stats.get("skills_used", 0)))
            self.stuck_combat_label.setText(str(stats.get("stuck_in_combat", 0)))
            self.stuck_search_label.setText(str(stats.get("stuck_searching", 0)))
        except Exception as e:
            print(f"Error updating UI: {e}")

    @pyqtSlot(dict)
    def _on_vitals_updated(self, vitals: Dict[str, Any]):
        if self.status_widget:
            self.status_widget.update_vitals(vitals)

    @pyqtSlot(str)
    def _on_bot_state_changed(self, state: str):
        # Este slot recibe la señal desde el hilo del bot y actualiza la UI.
        self.bot_status_label.setText(f"Status: {state.title()}")
        self.bot_state_label.setText(state.title())
        if state == "running":
            self.start_stop_btn.setText("Stop Bot")
            self.start_stop_btn.setStyleSheet(
                "background-color: #f44336; color: white;"
            )
            self.pause_resume_btn.setEnabled(True)
            self.pause_resume_btn.setText("Pause")
        elif state == "stopped":
            self.start_stop_btn.setText("Start Bot")
            self.start_stop_btn.setStyleSheet("")
            self.pause_resume_btn.setEnabled(False)
            self.pause_resume_btn.setText("Pause")
        elif state == "paused":
            self.pause_resume_btn.setText("Resume")

    @pyqtSlot(str)
    def _on_error_occurred(self, error: str):
        QMessageBox.critical(self, "Bot Error", f"An error occurred: {error}")

    @pyqtSlot()
    def _load_profile(self):
        """
        Abre un diálogo para que el usuario seleccione un archivo .ini
        y carga su configuración en el bot.
        """
        self.logger.info("Attempting to load a profile...")
        # Abre un diálogo de archivo, filtrando por archivos .ini
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Load Profile",
            "",  # Directorio inicial (vacío para default)
            "INI Files (*.ini);;All Files (*)",
            options=options,
        )

        if file_name:
            try:
                self.logger.info(f"Loading profile from: {file_name}")
                # 1. Le decimos al ConfigManager que importe el nuevo archivo.
                #    Esto reemplazará la configuración en memoria.
                self.bot_engine.config_manager.import_config(file_name)

                # 2. Le decimos al BotEngine que aplique esta nueva configuración
                #    a todos sus componentes (CombatManager, SkillManager, etc.).
                #    Esto también recargará los skills.
                self.bot_engine._setup_from_config()

                # 3. Refrescamos la UI para que muestre los nuevos valores cargados.
                self._load_configuration()

                self.status_bar.showMessage(
                    f"Profile '{os.path.basename(file_name)}' loaded successfully!",
                    5000,
                )
                QMessageBox.information(
                    self,
                    "Profile Loaded",
                    "The new configuration has been loaded.\nDon't forget to save if you want to make it the new default.",
                )
            except Exception as e:
                self.logger.error(f"Failed to load profile: {e}")
                QMessageBox.critical(
                    self, "Load Profile Error", f"Could not load the profile file:\n{e}"
                )

    @pyqtSlot()
    def _save_profile_as(self):
        """
        Abre un diálogo para que el usuario guarde la configuración actual
        en un nuevo archivo .ini (perfil).
        """
        self.logger.info("Attempting to save a profile...")
        # Primero, nos aseguramos de que la configuración en memoria refleja el estado actual de la UI.
        self._apply_ui_settings()

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Profile As...",
            "",  # Directorio inicial
            "INI Files (*.ini);;All Files (*)",
            options=options,
        )

        if file_name:
            try:
                self.logger.info(
                    f"Saving current configuration to profile: {file_name}"
                )
                # Le pedimos al ConfigManager que exporte la configuración actual
                # (que ya hemos actualizado desde la UI) a un nuevo archivo.
                self.bot_engine.config_manager.export_config(file_name)
                self.status_bar.showMessage(
                    f"Profile saved to '{os.path.basename(file_name)}'!", 5000
                )
            except Exception as e:
                self.logger.error(f"Failed to save profile: {e}")
                QMessageBox.critical(
                    self, "Save Profile Error", f"Could not save the profile file:\n{e}"
                )


def closeEvent(self, event):
    """
    Maneja el cierre de la aplicación de forma segura.
    """
    # No preguntamos, simplemente intentamos cerrar limpiamente.
    self.logger.info("Close event triggered. Shutting down bot thread...")

    # Emite la señal para que el worker detenga el bot.
    self.stop_signal.emit()

    # Le dice al hilo que termine su bucle de eventos cuando pueda.
    self.bot_thread.quit()

    # Espera un máximo de 3 segundos a que el hilo termine limpiamente.
    if not self.bot_thread.wait(3000):
        self.logger.warning("Bot thread did not close gracefully. Terminating.")
        self.bot_thread.terminate()  # Fuerza el cierre si no responde.

    event.accept()
