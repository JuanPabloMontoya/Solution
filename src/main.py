# src/main.py
import os
import json
import veryfi

from .extract import extract_veryfi_json
from .transform import transform_invoice
from .load import save_veryfi_json, save_processed_json

def run_pipeline():
    # Cargar credenciales desde src/static/credentials.json
    static_path = os.path.join(os.path.dirname(__file__), "static", "credentials.json")
    with open(static_path, "r", encoding="utf-8") as f:
        credentials = json.load(f)
    
    client_id = credentials.get("client_id")
    client_secret = credentials.get("client_secret")
    username = credentials.get("username")
    api_key = credentials.get("api_key")
    
    # Inicializar el cliente de Veryfi
    client = veryfi.Client(client_id, client_secret, username, api_key)
    
    # Directorios de entrada y salida
    input_folder = "Documents"
    veryfi_output_folder = "veryfi_jsons"
    processed_output_folder = "results"
    
    os.makedirs(veryfi_output_folder, exist_ok=True)
    os.makedirs(processed_output_folder, exist_ok=True)
    
    # Procesar cada archivo PDF en la carpeta de entrada
    for file_name in os.listdir(input_folder):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(input_folder, file_name)
            print(f"Procesando: {file_name}")
            
            # === EXTRACT ===
            # Extrae el JSON inicial usando el cliente de Veryfi
            json_result = extract_veryfi_json(file_path, client)#descomendar

            ###################### Trabajando con archivos ya descargados
            # veryfi_output_file = os.path.join(veryfi_output_folder, f"{file_name}.json")
            # with open(veryfi_output_file, "r", encoding="utf-8") as f:
            #     json_result = json.load(f)
                
            #######################
            
            # Guarda el JSON obtenido de Veryfi
            veryfi_output_file = save_veryfi_json(json_result, file_name, veryfi_output_folder)
            print(f"Resultado guardado en: {veryfi_output_file}")
            
            # === TRANSFORM ===
            # Extrae la información de la factura a partir del campo 'ocr_text'
            try:
                invoice_info = transform_invoice(json_result)
            except ValueError as ve:
                print(f"El documento '{file_name}' se omitirá: {ve}")
                continue
            
            # === LOAD ===
            # Guarda el JSON procesado en la carpeta de resultados
            processed_output_file = save_processed_json(invoice_info, file_name, processed_output_folder)
            print(f"Datos procesados guardados en: {processed_output_file}")
    
    print("Procesamiento completado.")
