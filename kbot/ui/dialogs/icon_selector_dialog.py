# kbot/ui/dialogs/icon_selector_dialog.py

import os
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QScrollArea,
    QWidget,
    QGridLayout,
    QPushButton,
    QLabel,
    QCheckBox,
    QDialogButtonBox,
    QFrame,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon


class ClickableIconLabel(QLabel):
    """Label clickable que emite señal cuando se hace clic en un icono."""
    
    clicked = pyqtSignal(str)  # Emite la ruta del archivo cuando se hace clic
    
    def __init__(self, icon_path, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        
        # Cargar y mostrar el icono en tamaño original
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            self.setPixmap(pixmap)
            self.setFixedSize(pixmap.size())
        else:
            self.setText("?")
            self.setFixedSize(32, 32)
        
        # Estilo por defecto
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background-color: white;
                margin: 2px;
            }
            QLabel:hover {
                border: 2px solid #007acc;
                background-color: #f0f8ff;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.icon_path)
    
    def set_selected(self, selected):
        """Marcar/desmarcar este icono como seleccionado."""
        if selected:
            self.setStyleSheet("""
                QLabel {
                    border: 3px solid #007acc;
                    background-color: #e6f3ff;
                    margin: 2px;
                }
                QLabel:hover {
                    border: 3px solid #007acc;
                    background-color: #e6f3ff;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    border: 1px solid #ccc;
                    background-color: white;
                    margin: 2px;
                }
                QLabel:hover {
                    border: 2px solid #007acc;
                    background-color: #f0f8ff;
                }
            """)


class IconSelectorDialog(QDialog):
    """Diálogo para seleccionar iconos de skills organizados por clases."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Skill Icon")
        self.setModal(True)
        self.resize(800, 600)
        
        self.selected_icon_path = None
        self.current_selected_label = None
        
        self._setup_ui()
        self._load_skill_icons()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Select a skill icon from the tabs below. Click on any icon to select it."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; font-weight: bold;")
        layout.addWidget(instructions)
        
        # Tab widget para las clases
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Checkbox para mostrar/ocultar tabs vacíos
        self.show_empty_tabs = QCheckBox("Show empty classes")
        self.show_empty_tabs.setChecked(True)
        self.show_empty_tabs.toggled.connect(self._toggle_empty_tabs)
        button_layout.addWidget(self.show_empty_tabs)
        
        button_layout.addStretch()
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        button_layout.addWidget(self.button_box)
        
        layout.addLayout(button_layout)
        
        # Initially disable OK button
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def _load_skill_icons(self):
        """Cargar todos los iconos de skills organizados por clases."""
        skills_base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "resources",
            "skills"
        )
        
        if not os.path.exists(skills_base_path):
            return
        
        # Obtener todas las clases (carpetas)
        classes = []
        for item in os.listdir(skills_base_path):
            class_path = os.path.join(skills_base_path, item)
            if os.path.isdir(class_path):
                classes.append(item)
        
        classes.sort()  # Orden alfabético
        
        # Crear tab para cada clase
        for class_name in classes:
            class_path = os.path.join(skills_base_path, class_name)
            self._create_class_tab(class_name, class_path)
    
    def _create_class_tab(self, class_name, class_path):
        """Crear una pestaña para una clase específica."""
        # Obtener todos los archivos de imagen en la carpeta
        icon_files = []
        for file in os.listdir(class_path):
            if file.lower().endswith(('.bmp', '.png', '.jpg', '.jpeg')):
                icon_files.append(os.path.join(class_path, file))
        
        icon_files.sort()
        
        # Si no hay iconos y no se muestran tabs vacíos, saltar
        if not icon_files and not self.show_empty_tabs.isChecked():
            return
        
        # Crear widget de scroll para el tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Widget contenedor para el grid
        container_widget = QWidget()
        grid_layout = QGridLayout(container_widget)
        grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # Añadir iconos al grid (6 columnas máximo)
        max_columns = 6
        for i, icon_path in enumerate(icon_files):
            row = i // max_columns
            col = i % max_columns
            
            icon_label = ClickableIconLabel(icon_path)
            icon_label.clicked.connect(self._on_icon_selected)
            grid_layout.addWidget(icon_label, row, col)
        
        # Si no hay iconos, mostrar mensaje
        if not icon_files:
            no_icons_label = QLabel("No icons available in this class")
            no_icons_label.setAlignment(Qt.AlignCenter)
            no_icons_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            grid_layout.addWidget(no_icons_label, 0, 0, 1, max_columns)
        
        scroll_area.setWidget(container_widget)
        
        # Añadir tab al widget
        tab_index = self.tab_widget.addTab(scroll_area, class_name.title())
        
        # Almacenar información del tab para poder ocultarlo/mostrarlo
        scroll_area.setProperty("class_name", class_name)
        scroll_area.setProperty("has_icons", len(icon_files) > 0)
    
    def _on_icon_selected(self, icon_path):
        """Manejar la selección de un icono."""
        # Deseleccionar icono anterior si existe
        if self.current_selected_label:
            self.current_selected_label.set_selected(False)
        
        # Encontrar el label que emitió la señal
        sender = self.sender()
        if isinstance(sender, ClickableIconLabel):
            sender.set_selected(True)
            self.current_selected_label = sender
            self.selected_icon_path = icon_path
            
            # Habilitar botón OK
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
    
    def _toggle_empty_tabs(self, show_empty):
        """Mostrar/ocultar tabs que no tienen iconos."""
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            has_icons = widget.property("has_icons")
            
            if not has_icons:
                self.tab_widget.setTabVisible(i, show_empty)
    
    def get_selected_icon_path(self):
        """Obtener la ruta del icono seleccionado."""
        return self.selected_icon_path
    
    def accept(self):
        """Aceptar solo si hay un icono seleccionado."""
        if self.selected_icon_path:
            super().accept()
    
    def reject(self):
        """Cancelar selección."""
        self.selected_icon_path = None
        super().reject()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = IconSelectorDialog()
    
    if dialog.exec_() == QDialog.Accepted:
        selected_path = dialog.get_selected_icon_path()
        print(f"Selected icon: {selected_path}")
    else:
        print("No icon selected")
    
    app.quit()