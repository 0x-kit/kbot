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
    QApplication,
    QInputDialog,
    QFormLayout,
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QImage, QPen


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
        else:  # Botones individuales para vitals
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
        pixmap, (offset_x, offset_y) = self._get_capture_for_selection()
        if not pixmap:
            return

        if not self._get_region_from_user(
            "Draw a box over a SINGLE skill slot (ideally the first one)", pixmap
        ):
            return

        first_slot_rel_region = self.temp_region

        num_slots, ok1 = QInputDialog.getInt(
            self, "Number of Slots", "How many skill slots in the bar?", 10, 1, 12, 1
        )
        if not ok1:
            return
        spacing, ok2 = QInputDialog.getInt(
            self, "Spacing", "Horizontal space between slots (in pixels)?", 5, 0, 50, 1
        )
        if not ok2:
            return

        x1, y1, x2, y2 = first_slot_rel_region
        width = x2 - x1
        height = y2 - y1

        for i in range(num_slots):
            slot_x1 = x1 + i * (width + spacing)
            slot_x2 = slot_x1 + width

            # Coordenadas relativas a la captura
            rel_region = (slot_x1, y1, slot_x2, y2)
            # Como la captura empieza en (0,0), las coordenadas absolutas son las mismas que las relativas.
            self._update_spinboxes(f"slot_{i}", rel_region)

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
