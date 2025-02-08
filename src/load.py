# src/load.py
import os
import json

def save_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_veryfi_json(data, file_name, output_folder):
    """
    Guarda el JSON obtenido de Veryfi en el directorio especificado.
    """
    file_path = os.path.join(output_folder, f"{file_name}.json")
    save_json(data, file_path)
    return file_path

def save_processed_json(data, file_name, output_folder):
    """
    Guarda el JSON procesado (resultado de las transformaciones) en el directorio especificado.
    """
    file_path = os.path.join(output_folder, f"{file_name}.json")
    save_json(data, file_path)
    return file_path
