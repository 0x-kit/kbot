#!/usr/bin/env python3
"""
Script para generar automáticamente los archivos JSON de metadata por clase.
Analiza los iconos existentes y crea la estructura de datos necesaria.
"""

import os
import json
import re
from typing import Dict, List, Any


def classify_skill_type(skill_name: str, icon_filename: str) -> str:
    """
    Clasificar automáticamente el tipo de skill basado en el nombre del archivo.
    
    Args:
        skill_name: Nombre procesado del skill
        icon_filename: Nombre del archivo de icono
        
    Returns:
        "offensive", "utility", o "defensive"
    """
    name_lower = skill_name.lower()
    filename_lower = icon_filename.lower()
    
    # Patrones para offensive skills
    offensive_patterns = [
        'attack', 'damage', 'strike', 'slash', 'punch', 'arrow', 'fire', 
        'lightning', 'ice', 'earth', 'wind', 'explosion', 'blast', 'crush',
        'ao_', 'tripleorapunch', 'suriafirecrack', 'bizsai', 'balukatrash',
        'stun', 'janatipara', 'bisacro', 'pranaarrow', 'agniarrow', 'holdfire'
    ]
    
    # Patrones para utility/buff skills  
    utility_patterns = [
        'buff', 'heal', 'mana', 'speed', 'shield', 'protection', 'boost',
        'av_', 'mantra', 'chakra', 'meditation', 'enhancement', 'aura',
        'orashield', 'indrazala', 'incresespeed', 'cundalini', 'scandapuri'
    ]
    
    # Patrones para defensive skills
    defensive_patterns = [
        'defense', 'block', 'resist', 'armor', 'ward', 'barrier',
        'command_monster_defense', 'against', 'dorbaagainst'
    ]
    
    # Verificar patrones
    text_to_check = f"{name_lower} {filename_lower}"
    
    for pattern in offensive_patterns:
        if pattern in text_to_check:
            return "offensive"
    
    for pattern in utility_patterns:
        if pattern in text_to_check:
            return "utility"
            
    for pattern in defensive_patterns:
        if pattern in text_to_check:
            return "defensive"
    
    # Por defecto, si no se puede clasificar, será offensive
    return "offensive"


def clean_skill_name(icon_filename: str) -> str:
    """
    Generar un nombre limpio para el skill basado en el nombre del archivo.
    
    Args:
        icon_filename: Nombre del archivo de icono
        
    Returns:
        Nombre limpio del skill
    """
    # Remover extensión
    name = os.path.splitext(icon_filename)[0]
    
    # Remover prefijos comunes
    prefixes_to_remove = ['ICON_SKILL_', 'Icon_skill_', 'COMMAND_']
    for prefix in prefixes_to_remove:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    
    # Reemplazar guiones bajos con espacios
    name = name.replace('_', ' ')
    
    # Capitalizar cada palabra
    words = []
    for word in name.split():
        # Manejar casos especiales
        if word.upper() in ['AO', 'AV', 'HP', 'MP']:
            words.append(word.upper())
        elif len(word) <= 2:
            words.append(word.upper())
        else:
            words.append(word.capitalize())
    
    return ' '.join(words)


def generate_skill_id(icon_filename: str) -> str:
    """
    Generar un ID único para el skill basado en el nombre del archivo.
    
    Args:
        icon_filename: Nombre del archivo de icono
        
    Returns:
        ID del skill en formato snake_case
    """
    # Remover extensión
    name = os.path.splitext(icon_filename)[0]
    
    # Remover prefijos comunes
    prefixes_to_remove = ['ICON_SKILL_', 'Icon_skill_', 'COMMAND_']
    for prefix in prefixes_to_remove:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    
    # Convertir a snake_case
    name = name.lower()
    # Reemplazar caracteres especiales con guiones bajos
    name = re.sub(r'[^a-z0-9_]', '_', name)
    # Remover guiones bajos múltiples
    name = re.sub(r'_+', '_', name)
    # Remover guiones bajos al inicio y final
    name = name.strip('_')
    
    return name


def get_class_display_name(class_name: str) -> str:
    """
    Generar nombre amigable para la clase.
    
    Args:
        class_name: Nombre técnico de la clase
        
    Returns:
        Nombre amigable para mostrar
    """
    class_names = {
        'abikara': 'Abikara (Fire Mage)',
        'banar': 'Banar (Warrior)', 
        'druka': 'Druka (Assassin)',
        'karya': 'Karya (Archer)',
        'nakayuda': 'Nakayuda (Monk)',
        'samabat': 'Samabat (Summoner)',
        'satya': 'Satya (Earth Mage)',
        'vidya': 'Vidya (Support)'
    }
    
    return class_names.get(class_name, class_name.capitalize())


def generate_class_metadata(skills_base_path: str) -> None:
    """
    Generar archivos JSON de metadata para todas las clases.
    
    Args:
        skills_base_path: Ruta base a la carpeta de skills
    """
    if not os.path.exists(skills_base_path):
        print(f"❌ Error: No se encontró la carpeta {skills_base_path}")
        return
    
    # Obtener todas las clases (carpetas)
    classes = []
    for item in os.listdir(skills_base_path):
        class_path = os.path.join(skills_base_path, item)
        if os.path.isdir(class_path):
            classes.append(item)
    
    classes.sort()
    print(f"📁 Encontradas {len(classes)} clases: {', '.join(classes)}")
    
    # Procesar cada clase
    for order, class_name in enumerate(classes, 1):
        class_path = os.path.join(skills_base_path, class_name)
        print(f"\n🔄 Procesando clase: {class_name}")
        
        # Obtener todos los archivos de imagen
        icon_files = []
        for file in os.listdir(class_path):
            if file.lower().endswith(('.bmp', '.png', '.jpg', '.jpeg')):
                icon_files.append(file)
        
        icon_files.sort()
        print(f"   📊 Encontrados {len(icon_files)} iconos")
        
        # Generar metadata de skills
        skills_data = []
        for icon_file in icon_files:
            skill_id = generate_skill_id(icon_file)
            skill_name = clean_skill_name(icon_file)
            skill_type = classify_skill_type(skill_name, icon_file)
            
            skill_data = {
                "id": skill_id,
                "name": skill_name,
                "icon_file": icon_file,
                "type": skill_type,
                "enabled": True
            }
            
            skills_data.append(skill_data)
            print(f"   ✅ {skill_name} ({skill_type})")
        
        # Generar metadata de la clase
        class_metadata = {
            "class_name": class_name,
            "display_name": get_class_display_name(class_name),
            "enabled": True,
            "order": order,
            "skills": skills_data
        }
        
        # Guardar archivo JSON
        json_filename = f"{class_name}_metadata.json"
        json_filepath = os.path.join(class_path, json_filename)
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(class_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Guardado: {json_filepath}")
    
    print(f"\n✅ ¡Generación completa! Procesadas {len(classes)} clases.")


def main():
    """Función principal del script."""
    # Determinar ruta base de skills
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skills_base_path = os.path.join(script_dir, "kbot", "resources", "skills")
    
    print("🚀 Generador de Metadata de Skills")
    print(f"📂 Ruta base: {skills_base_path}")
    print("=" * 50)
    
    generate_class_metadata(skills_base_path)


if __name__ == "__main__":
    main()