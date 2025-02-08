# src/extract.py
def extract_veryfi_json(file_path, client):
    """
    Procesa el documento usando el cliente de Veryfi y retorna el JSON resultante.
    """
    json_result = client.process_document(file_path)
    return json_result
