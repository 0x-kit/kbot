# kbot/ui/dialogs/icon_selector_dialog.py

import os
import json
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
        """Cargar todos los iconos de skills organizados por clases usando metadata."""
        skills_base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "resources",
            "skills"
        )
        
        if not os.path.exists(skills_base_path):
            return
        
        # Obtener todas las clases que tienen archivos de metadata
        class_metadata_list = []
        for item in os.listdir(skills_base_path):
            class_path = os.path.join(skills_base_path, item)
            if os.path.isdir(class_path):
                metadata_file = os.path.join(class_path, f"{item}_metadata.json")
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            metadata['path'] = class_path
                            class_metadata_list.append(metadata)
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error loading metadata for {item}: {e}")
                        # Fallback al método anterior si no hay metadata
                        self._create_class_tab_fallback(item, class_path)
        
        # Ordenar por order especificado en metadata
        class_metadata_list.sort(key=lambda x: x.get('order', 999))
        
        # Crear tab para cada clase usando metadata
        for class_metadata in class_metadata_list:
            if class_metadata.get('enabled', True):
                self._create_class_tab_with_metadata(class_metadata)
    
    def _create_class_tab_with_metadata(self, class_metadata):
        """Crear una pestaña para una clase usando metadata con agrupación por skill type."""
        class_name = class_metadata['class_name']
        display_name = class_metadata['display_name'] 
        class_path = class_metadata['path']
        skills = class_metadata.get('skills', [])
        
        # Filtrar skills habilitados
        enabled_skills = [skill for skill in skills if skill.get('enabled', True)]
        
        # Si no hay skills y no se muestran tabs vacíos, saltar
        if not enabled_skills and not self.show_empty_tabs.isChecked():
            return
        
        # Agrupar skills por tipo
        skills_by_type = {}
        for skill in enabled_skills:
            skill_type = skill.get('type', 'offensive')
            if skill_type not in skills_by_type:
                skills_by_type[skill_type] = []
            skills_by_type[skill_type].append(skill)
        
        # Crear widget de scroll para el tab principal
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Widget contenedor principal
        container_widget = QWidget()
        main_layout = QVBoxLayout(container_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Ordenar tipos de skills (offensive -> utility -> defensive)
        type_order = ['offensive', 'utility', 'defensive']
        ordered_types = [t for t in type_order if t in skills_by_type]
        ordered_types.extend([t for t in skills_by_type.keys() if t not in type_order])
        
        # Crear sección para cada tipo de skill
        total_skills = 0
        for skill_type in ordered_types:
            type_skills = skills_by_type[skill_type]
            if not type_skills:
                continue
                
            # Título de la sección
            type_label = QLabel(f"{skill_type.title()} Skills ({len(type_skills)})")
            type_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #333; margin: 10px 0 5px 0;")
            main_layout.addWidget(type_label)
            
            # Grid para los iconos de este tipo
            type_grid_widget = QWidget()
            type_grid_layout = QGridLayout(type_grid_widget)
            type_grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            
            max_columns = 6
            for i, skill in enumerate(type_skills):
                row = i // max_columns
                col = i % max_columns
                
                icon_file = skill.get('icon_file', '')
                icon_path = os.path.join(class_path, icon_file)
                
                if os.path.exists(icon_path):
                    icon_label = ClickableIconLabel(icon_path)
                    icon_label.clicked.connect(self._on_icon_selected)
                    # Añadir tooltip con el nombre del skill
                    icon_label.setToolTip(skill.get('name', icon_file))
                    type_grid_layout.addWidget(icon_label, row, col)
                    total_skills += 1
            
            main_layout.addWidget(type_grid_widget)
        
        # Si no hay skills, mostrar mensaje
        if total_skills == 0:
            no_icons_label = QLabel("No skills available in this class")
            no_icons_label.setAlignment(Qt.AlignCenter)
            no_icons_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            main_layout.addWidget(no_icons_label)
        
        main_layout.addStretch()
        scroll_area.setWidget(container_widget)
        
        # Añadir tab al widget
        tab_index = self.tab_widget.addTab(scroll_area, display_name)
        
        # Almacenar información del tab para poder ocultarlo/mostrarlo
        scroll_area.setProperty("class_name", class_name)
        scroll_area.setProperty("has_icons", total_skills > 0)
    
    def _create_class_tab_fallback(self, class_name, class_path):
        """Crear una pestaña para una clase específica (método fallback sin metadata)."""
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