# kbot/ui/dialogs/region_config.py

import sys
import win32gui
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSpinBox,
    QLabel,
    QDialogButtonBox,
    QPushButton,
    QGroupBox,
    QMessageBox,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsPixmapItem,
    QApplication,
    QInputDialog,
    QFormLayout,
    QSlider,
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPixmap, QImage, QPen, QBrush, QColor
import os


class RegionSelector(QGraphicsView):
    """Una vista gráfica para dibujar rectángulos sobre una imagen."""

    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.scene.addPixmap(pixmap)
        self.current_rect_item = None
        self.start_pos = None

    def mousePressEvent(self, event):
        self.start_pos = self.mapToScene(event.pos())
        if self.current_rect_item:
            self.scene.removeItem(self.current_rect_item)
        rect = QRectF(self.start_pos, self.start_pos)
        self.current_rect_item = QGraphicsRectItem(rect)
        self.current_rect_item.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        self.scene.addItem(self.current_rect_item)

    def mouseMoveEvent(self, event):
        if self.start_pos:
            end_pos = self.mapToScene(event.pos())
            rect = QRectF(self.start_pos, end_pos).normalized()
            self.current_rect_item.setRect(rect)

    def mouseReleaseEvent(self, event):
        self.start_pos = None

    def get_selected_region(self):
        if self.current_rect_item:
            rect = self.current_rect_item.rect()
            return (
                int(rect.x()),
                int(rect.y()),
                int(rect.x() + rect.width()),
                int(rect.y() + rect.height()),
            )
        return None


class VitalsOverlaySelector(QGraphicsView):
    """Selector de vitals con overlay de imagen de referencia."""

    def __init__(self, screenshot_pixmap, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Add screenshot as background
        self.scene.addPixmap(screenshot_pixmap)

        # Load vitals overlay image
        vitals_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "resources",
            "vitals_region.png",
        )
        self.vitals_pixmap = QPixmap(vitals_path)

        # Create overlay item
        self.overlay_item = QGraphicsPixmapItem(self.vitals_pixmap)
        self.overlay_item.setOpacity(0.7)  # 70% opacity
        self.overlay_item.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
        self.overlay_item.setZValue(1)  # Above screenshot
        self.scene.addItem(self.overlay_item)

        # Position overlay in top-left initially (where vitals usually are)
        self.overlay_item.setPos(50, 50)

        # Store vitals regions (relative to overlay image)
        self.vitals_regions = self._calculate_vitals_regions()

        # Visual feedback for regions
        self.region_indicators = []
        self._create_region_indicators()

    def _calculate_vitals_regions(self):
        """Version con valores absolutos más fáciles de ajustar."""
        w = self.vitals_pixmap.width()

        # ✅ Ajusta estos valores Y directamente
        regions = {
            "hp": (4, 26, w - 2, 31),  # Empieza en Y=8, termina en Y=28
            "mp": (4, 44, w - 2, 49),  # Empieza en Y=28, termina en Y=48
            "target_name": (40, 55, w - 40, 67),  # Empieza en Y=48, termina en Y=63
            "target": (4, 70, w - 1, 73),  # Empieza en Y=63, termina en Y=83
        }

        return regions

    def _create_region_indicators(self):
        """Create visual indicators for each vitals region with better contrast colors."""
        colors = {
            # Para HP (sobre fondo rojo) - usar color complementario
            "hp": QColor(0, 255, 255, 100),  # Cian brillante semi-transparente
            # Para MP (sobre fondo azul) - usar color complementario
            "mp": QColor(255, 255, 0, 100),  # Amarillo brillante semi-transparente
            # Para target_name (sobre fondo blanco/texto) - usar color oscuro
            "target_name": QColor(255, 0, 255, 120),  # Magenta semi-transparente
            # Para target (sobre fondo verde) - usar color complementario
            "target": QColor(255, 100, 0, 120),  # Naranja semi-transparente
        }

        pen_colors = {
            "hp": QColor(0, 200, 200),  # Cian más oscuro para el borde
            "mp": QColor(200, 200, 0),  # Amarillo más oscuro para el borde
            "target_name": QColor(200, 0, 200),  # Magenta más oscuro para el borde
            "target": QColor(200, 80, 0),  # Naranja más oscuro para el borde
        }

        for region_name, (x1, y1, x2, y2) in self.vitals_regions.items():
            rect_item = QGraphicsRectItem(x1, y1, x2 - x1, y2 - y1)

            # Usar colores específicos para mejor contraste
            rect_item.setPen(QPen(pen_colors[region_name], 1, Qt.SolidLine))
            rect_item.setBrush(QBrush(colors[region_name]))

            rect_item.setParentItem(self.overlay_item)
            rect_item.setVisible(False)  # Hidden by default
            self.region_indicators.append(rect_item)

    def set_overlay_opacity(self, opacity):
        """Set the opacity of the overlay (0.0 to 1.0)."""
        self.overlay_item.setOpacity(opacity / 100.0)

    def toggle_region_indicators(self, visible):
        """Show/hide region indicators."""
        for indicator in self.region_indicators:
            indicator.setVisible(visible)

    def get_vitals_regions(self):
        """Get absolute coordinates for all vitals regions."""
        overlay_pos = self.overlay_item.pos()
        absolute_regions = {}

        for region_name, (x1, y1, x2, y2) in self.vitals_regions.items():
            abs_x1 = int(overlay_pos.x() + x1)
            abs_y1 = int(overlay_pos.y() + y1)
            abs_x2 = int(overlay_pos.x() + x2)
            abs_y2 = int(overlay_pos.y() + y2)
            absolute_regions[region_name] = (abs_x1, abs_y1, abs_x2, abs_y2)

        return absolute_regions


class SkillBarOverlaySelector(QGraphicsView):
    """Selector de skillbar con overlay de imagen de referencia."""

    def __init__(self, screenshot_pixmap, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Add screenshot as background
        self.scene.addPixmap(screenshot_pixmap)

        # Load skill bar overlay image
        skill_bar_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "resources",
            "skill_bar.png",
        )
        self.skill_bar_pixmap = QPixmap(skill_bar_path)

        # Create overlay item
        self.overlay_item = QGraphicsPixmapItem(self.skill_bar_pixmap)
        self.overlay_item.setOpacity(0.7)  # 70% opacity
        self.overlay_item.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
        self.overlay_item.setZValue(1)  # Above screenshot
        self.scene.addItem(self.overlay_item)

        # Position overlay in center initially
        screenshot_rect = screenshot_pixmap.rect()
        overlay_rect = self.skill_bar_pixmap.rect()
        center_x = (screenshot_rect.width() - overlay_rect.width()) / 2
        center_y = (screenshot_rect.height() - overlay_rect.height()) / 2
        self.overlay_item.setPos(center_x, center_y)

        # Store slot regions (relative to overlay image)
        self.slot_regions = self._calculate_slot_regions()

        # Visual feedback for slots
        self.slot_indicators = []
        self._create_slot_indicators()

    def _calculate_slot_regions(self):
        """Calculate regions for each of the 10 skill slots based on the overlay image."""
        # Análisis de la imagen skill_bar.png (331x37 pixels)
        # Cada slot es aproximadamente 30x30 pixels
        # La barra tiene un borde y las casillas están centradas

        slot_width = 33
        slot_height = 33

        # Ajustar la posición inicial y el espaciado basado en la imagen real
        start_x = 17.5  # Offset desde el borde izquierdo
        start_y = 4  # Centrado verticalmente (37-30)/2 ≈ 3.5, redondeado a 4
        spacing = 39  # Distancia entre centros de slots (más preciso)

        regions = []
        for i in range(10):
            x1 = start_x + (i * spacing)
            y1 = start_y
            x2 = x1 + slot_width
            y2 = y1 + slot_height
            regions.append((x1, y1, x2, y2))

        return regions

    def _create_slot_indicators(self):
        """Create visual indicators for each slot."""
        for i, (x1, y1, x2, y2) in enumerate(self.slot_regions):
            # Create a semi-transparent rectangle for each slot
            rect_item = QGraphicsRectItem(x1, y1, x2 - x1, y2 - y1)
            rect_item.setPen(QPen(Qt.green, 1, Qt.SolidLine))
            rect_item.setBrush(QBrush(QColor(0, 255, 0, 50)))  # Semi-transparent green
            rect_item.setParentItem(self.overlay_item)
            rect_item.setVisible(False)  # Hidden by default
            self.slot_indicators.append(rect_item)

    def set_overlay_opacity(self, opacity):
        """Set the opacity of the overlay (0.0 to 1.0)."""
        self.overlay_item.setOpacity(opacity / 100.0)

    def toggle_slot_indicators(self, visible):
        """Show/hide slot indicators."""
        for indicator in self.slot_indicators:
            indicator.setVisible(visible)

    def get_slot_regions(self):
        """Get absolute coordinates for all 10 slots."""
        overlay_pos = self.overlay_item.pos()
        absolute_regions = []

        for x1, y1, x2, y2 in self.slot_regions:
            abs_x1 = int(overlay_pos.x() + x1)
            abs_y1 = int(overlay_pos.y() + y1)
            abs_x2 = int(overlay_pos.x() + x2)
            abs_y2 = int(overlay_pos.y() + y2)
            absolute_regions.append((abs_x1, abs_y1, abs_x2, abs_y2))

        return absolute_regions


class RegionConfigDialog(QDialog):
    """Diálogo interactivo para configurar todas las regiones."""

    def __init__(self, bot_engine, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine
        self.setWindowTitle("Interactive Region Configuration")
        self.resize(800, 600)

        import copy

        self.original_config = copy.deepcopy(
            self.bot_engine.config_manager.get_all_config()
        )

        self._setup_ui()
        self._load_coords_to_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        info_label = QLabel(
            "Usa los botones de abajo para capturar la pantalla y dibujar las regiones con el ratón."
        )
        main_layout.addWidget(info_label)
        self.coords_layout = QGridLayout()
        main_layout.addLayout(self.coords_layout)
        self.spinboxes = {}
        self._create_spinbox_group(
            "Vitals & Target", ["hp", "mp", "target", "target_name"]
        )
        self._create_spinbox_group("Skill Bar", [f"slot_{i}" for i in range(10)])
        main_layout.addStretch()
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _create_spinbox_group(self, title, region_keys):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        form_layout = QFormLayout()

        if title == "Skill Bar":
            btn = QPushButton("Auto-Configure Skill Bar...")
            btn.clicked.connect(self.launch_skill_bar_selector)
            layout.addWidget(btn)
        elif title == "Vitals & Target":
            # Botón para auto-configurar todas las regiones de vitals
            auto_btn = QPushButton("Auto-Configure All Vitals...")
            auto_btn.clicked.connect(self.launch_vitals_selector)
            layout.addWidget(auto_btn)

            # Botones individuales para configuración manual (opcional)
            for key in region_keys:
                btn = QPushButton(f"Select {key.replace('_', ' ').title()} Region...")
                btn.clicked.connect(lambda _, k=key: self.launch_region_selector(k))
                form_layout.addRow(btn)
        else:  # Otros grupos
            for key in region_keys:
                btn = QPushButton(f"Select {key.replace('_', ' ').title()} Region...")
                btn.clicked.connect(lambda _, k=key: self.launch_region_selector(k))
                form_layout.addRow(btn)

        for key in region_keys:
            coords_layout = QHBoxLayout()
            spin_row = []
            for lbl in ["X1", "Y1", "X2", "Y2"]:
                coords_layout.addWidget(QLabel(lbl))
                sb = QSpinBox()
                sb.setRange(0, 8000)
                sb.setFixedWidth(70)
                coords_layout.addWidget(sb)
                spin_row.append(sb)
            self.spinboxes[key] = spin_row
            form_layout.addRow(
                QLabel(f"{key.replace('_', ' ').title()}:"), coords_layout
            )

        layout.addLayout(form_layout)
        self.coords_layout.addWidget(group)

    def _get_capture_for_selection(self) -> (QPixmap, tuple):
        """
        ✅ LÓGICA CENTRALIZADA: Realiza la captura forzada a 1360x768.
        Devuelve el QPixmap y las coordenadas de la esquina superior izquierda de la captura.
        """
        try:
            # Forzar captura desde el origen de la pantalla para garantizar nitidez
            capture_area = (0, 0, 1360, 768)
            capture = self.bot_engine.pixel_analyzer.capture_screen(region=capture_area)

            q_image = QImage(
                capture.tobytes("raw", "RGB"),
                capture.width,
                capture.height,
                QImage.Format_RGB888,
            )
            pixmap = QPixmap.fromImage(q_image)

            return pixmap, (capture_area[0], capture_area[1])
        except Exception as e:
            QMessageBox.critical(
                self, "Capture Error", f"Could not capture screen: {e}"
            )
            return None, None

    def launch_region_selector(self, region_key):
        pixmap, (offset_x, offset_y) = self._get_capture_for_selection()
        if not pixmap:
            return

        if self._get_region_from_user(f"Draw rect for: {region_key}", pixmap):
            region = self.temp_region
            # Las coordenadas del rectángulo son relativas a la captura (0,0,1360,768).
            # Como la captura empieza en (0,0), estas son también las coordenadas absolutas.
            self._update_spinboxes(region_key, region)

    def launch_skill_bar_selector(self):
        """New skill bar selector with overlay image."""
        pixmap, (offset_x, offset_y) = self._get_capture_for_selection()
        if not pixmap:
            return

        # Create dialog with overlay selector
        selector_dialog = QDialog(self)
        selector_dialog.setWindowTitle(
            "Position Skill Bar Overlay - Drag to align with your skill bar"
        )
        selector_dialog.setWindowState(Qt.WindowMaximized)

        layout = QVBoxLayout(selector_dialog)

        # Instructions
        instructions = QLabel(
            "🎯 Instructions:\n"
            "1. Drag the skill bar overlay to align it with your game's skill bar\n"
            "2. Use the opacity slider to see through the overlay\n"
            "3. Toggle slot indicators to verify alignment\n"
            "4. Click OK when perfectly aligned"
        )
        instructions.setStyleSheet(
            "background-color: #f0f0f0; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(instructions)

        # Controls
        controls_layout = QHBoxLayout()

        # Opacity slider
        controls_layout.addWidget(QLabel("Overlay Opacity:"))
        opacity_slider = QSlider(Qt.Horizontal)
        opacity_slider.setRange(10, 100)
        opacity_slider.setValue(70)
        opacity_slider.setFixedWidth(200)
        controls_layout.addWidget(opacity_slider)

        # Show indicators checkbox
        indicators_btn = QPushButton("Toggle Slot Indicators")
        indicators_btn.setCheckable(True)
        controls_layout.addWidget(indicators_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Overlay selector
        overlay_selector = SkillBarOverlaySelector(pixmap)
        layout.addWidget(overlay_selector)

        # Connect controls
        opacity_slider.valueChanged.connect(overlay_selector.set_overlay_opacity)
        indicators_btn.toggled.connect(overlay_selector.toggle_slot_indicators)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(selector_dialog.accept)
        buttons.rejected.connect(selector_dialog.reject)
        layout.addWidget(buttons)

        if selector_dialog.exec_() == QDialog.Accepted:
            # Get all 10 slot regions
            slot_regions = overlay_selector.get_slot_regions()

            # Update all 10 slots
            for i, region in enumerate(slot_regions):
                self._update_spinboxes(f"slot_{i}", region)

            QMessageBox.information(
                self,
                "Success",
                f"✅ Successfully configured all 10 skill slots!\n"
                f"Slot regions have been automatically calculated.",
            )

    def launch_vitals_selector(self):
        """New vitals selector with overlay image."""
        pixmap, _ = self._get_capture_for_selection()
        if not pixmap:
            return

        # Create dialog with vitals overlay selector
        selector_dialog = QDialog(self)
        selector_dialog.setWindowTitle(
            "Position Vitals Overlay - Drag to align with your vitals"
        )
        selector_dialog.setWindowState(Qt.WindowMaximized)

        layout = QVBoxLayout(selector_dialog)

        # Instructions
        instructions = QLabel(
            "🎯 Instructions:\n"
            "1. Drag the vitals overlay to align it with your game's HP/MP/Target bars\n"
            "2. Use the opacity slider to see through the overlay\n"
            "3. Toggle region indicators to verify alignment\n"
            "4. Click OK when perfectly aligned"
        )
        instructions.setStyleSheet(
            "background-color: #f0f0f0; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(instructions)

        # Controls
        controls_layout = QHBoxLayout()

        # Opacity slider
        controls_layout.addWidget(QLabel("Overlay Opacity:"))
        opacity_slider = QSlider(Qt.Horizontal)
        opacity_slider.setRange(10, 100)
        opacity_slider.setValue(70)
        opacity_slider.setFixedWidth(200)
        controls_layout.addWidget(opacity_slider)

        # Show indicators checkbox
        indicators_btn = QPushButton("Toggle Region Indicators")
        indicators_btn.setCheckable(True)
        controls_layout.addWidget(indicators_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Vitals overlay selector
        vitals_selector = VitalsOverlaySelector(pixmap)
        layout.addWidget(vitals_selector)

        # Connect controls
        opacity_slider.valueChanged.connect(vitals_selector.set_overlay_opacity)
        indicators_btn.toggled.connect(vitals_selector.toggle_region_indicators)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(selector_dialog.accept)
        buttons.rejected.connect(selector_dialog.reject)
        layout.addWidget(buttons)

        if selector_dialog.exec_() == QDialog.Accepted:
            # Get all vitals regions
            vitals_regions = vitals_selector.get_vitals_regions()

            # Update all vitals regions
            for region_name, region_coords in vitals_regions.items():
                self._update_spinboxes(region_name, region_coords)

            QMessageBox.information(
                self,
                "Success",
                f"✅ Successfully configured all vitals regions!\n"
                f"HP, MP, Target, and Target Name regions have been automatically calculated.",
            )

    def _get_region_from_user(self, title, pixmap):
        selector_dialog = QDialog(self)
        selector_dialog.setWindowTitle(title)
        selector_dialog.setWindowState(Qt.WindowMaximized)

        layout = QVBoxLayout(selector_dialog)
        selector_view = RegionSelector(pixmap)
        layout.addWidget(selector_view)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(selector_dialog.accept)
        buttons.rejected.connect(selector_dialog.reject)
        layout.addWidget(buttons)

        if selector_dialog.exec_() == QDialog.Accepted:
            self.temp_region = selector_view.get_selected_region()
            return self.temp_region is not None
        return False

    def _update_spinboxes(self, key, region):
        if key in self.spinboxes:
            sbs = self.spinboxes[key]
            for i, val in enumerate(region):
                sbs[i].setValue(val)

    def _load_coords_to_ui(self):
        config = self.bot_engine.config_manager.get_all_config()
        vitals_regions = config.get("regions", {})
        for key, coords in vitals_regions.items():
            self._update_spinboxes(key, coords)

        skill_bar_slots = config.get("skill_bar", {}).get("slots", [])
        for i, coords in enumerate(skill_bar_slots):
            self._update_spinboxes(f"slot_{i}", coords)

    def _apply_ui_to_config(self):
        config = self.bot_engine.config_manager.get_all_config()

        vitals_regions = config.get("regions", {})
        for key in ["hp", "mp", "target", "target_name"]:
            vitals_regions[key] = [sb.value() for sb in self.spinboxes[key]]
        config["regions"] = vitals_regions

        skill_slots = []
        for i in range(10):
            key = f"slot_{i}"
            if key in self.spinboxes:
                skill_slots.append([sb.value() for sb in self.spinboxes[key]])
        if "skill_bar" not in config:
            config["skill_bar"] = {}
        config["skill_bar"]["slots"] = skill_slots

        self.bot_engine.config_manager.config_data = config

    def accept(self):
        self._apply_ui_to_config()
        self.bot_engine.config_manager.save_config()
        super().accept()

    def reject(self):
        self.bot_engine.config_manager.config_data = self.original_config
        super().reject()
