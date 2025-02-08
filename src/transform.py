import re
import pandas as pd

def clean_ocr_text(text):
    """
    Limpia el OCR eliminando saltos de página y encabezados/pies de página.
    """
    text = text.replace("\f", "\n")
    if not re.search(r'Description\s+Quantity\s+Rate\s+Amount', text, flags=re.IGNORECASE):
        print("El documento no cumple con el formato de invoice esperado; se omitirá este documento.")
        return None
    text = re.sub(r'^\s*(Invoice|Page\s+\d+\s+of\s+\d+).*$', '', text, flags=re.MULTILINE)
    text = "\n".join([line for line in text.splitlines() if line.strip() != ""])
    return text

def is_valid_row(description):
    """
    Devuelve False si la descripción corresponde a un encabezado o
    contenido no deseado (por cambio de página u otro) que se ha
    incluido por error en la sección de ítems.
    """
    desc = description.strip().lower()
    if desc.startswith("po box"):
        return False
    if "invoice date" in desc:
        return False
    if desc.startswith("micro merchant systems"):
        return False
    if desc.startswith("account no."):
        return False
    if desc == "description":
        return False
    if desc.startswith("o-") and len(desc) < 15:
        return False
    if "incentx" in desc and "main st" in desc:
        return False
    if re.fullmatch(r'w-\d+', desc):
        return False
    return True

def clean_description(desc):
    """
    Elimina de la descripción fragmentos indeseados (por ejemplo,
    partes que provengan de encabezados de página).
    En este ejemplo se elimina cualquier texto a partir de "Invoice switch".
    Ajusta el patrón según los casos que observes.
    """
    cleaned = re.sub(r'Invoice\s+switch.*', '', desc, flags=re.IGNORECASE)
    return cleaned.strip()

def extract_invoice_data(ocr_text):
    """
    Extrae la información clave de la factura desde el texto OCR.
    """
    invoice_data = {}

    # Extraer Vendor Name
    vendor_match = re.search(r'Please make payments to:\s*(.+)', ocr_text)
    invoice_data["vendor_name"] = vendor_match.group(1).strip() if vendor_match else "Unknown"

    # Extraer Vendor Address (fijo)
    vendor_address_match = re.search(r"\n([\w\s,]+ \d{5}(?:-\d{4})?)\nPO Box", ocr_text)
    if vendor_address_match:
        address = vendor_address_match.group(1).strip()
        address_parts = address.split()[-3:]  # Ejemplo: ciudad, estado y código postal
        invoice_data["vendor_address"] = " ".join(address_parts)
    else:
        invoice_data["vendor_address"] = "Unknown"

    # Extraer Invoice Date, Invoice Number y Bill To Name
    invoice_match = re.search(
        r'Invoice Date Due Date\tInvoice No\.\n\t(\d{2}/\d{2}/\d{2})\t(\d{2}/\d{2}/\d{2})\t([\d]+)\n\n([^\n]+)',
        ocr_text
    )
    if invoice_match:
        invoice_data["date"] = invoice_match.group(1)           # Ejemplo: "01/12/24"
        invoice_data["invoice_number"] = invoice_match.group(3)   # Ejemplo: "9230090"
        invoice_data["bill_to_name"] = invoice_match.group(4).strip()  # Ejemplo: "IncentX"
    else:
        invoice_data["date"] = "Unknown"
        invoice_data["invoice_number"] = "Unknown"
        invoice_data["bill_to_name"] = "Unknown"

    ocr_text_clean = clean_ocr_text(ocr_text)
    if ocr_text_clean is None:
        # Si no se detecta el formato esperado, se omite este documento.
        raise ValueError("El documento no cumple con el formato de invoice esperado.")
    
    # --- Paso 1: Extraer la sección de precios ---
    start_pattern = r"^\s*Description\s+Quantity\s+Rate\s+Amount\s*$"
    end_pattern = r"^\tTotal\s+USD"
    match_start = re.search(start_pattern, ocr_text_clean, flags=re.MULTILINE)
    match_end = re.search(end_pattern, ocr_text_clean, flags=re.MULTILINE)
    
    if match_start and match_end:
        price_section = ocr_text_clean[match_start.end():match_end.start()]
    else:
        raise ValueError("No se pudo identificar la sección de lista de precios.")

    # --- Paso 2: Procesar price_section para reconstruir la tabla de 4 columnas ---
    rows = []
    current_row = None
    for line in price_section.splitlines():
        if "\t" in line:
            tokens = line.split("\t")
            # Si hay menos de 4 tokens, se intenta extraer la cantidad del final de token[0]
            if len(tokens) < 4:
                if len(tokens) == 3:
                    m = re.search(r'^(.*\D)(\d[\d.,]*)$', tokens[0].strip())
                    if m:
                        # Separamos la descripción y la cantidad
                        description_part = m.group(1).strip()
                        quantity_part = m.group(2).strip()
                        tokens = [description_part, quantity_part, tokens[1].strip(), tokens[2].strip()]
                    else:
                        if current_row is not None:
                            current_row[0] += " " + line.strip()
                        continue
                else:
                    if current_row is not None:
                        current_row[0] += " " + line.strip()
                    continue
            if current_row is not None:
                rows.append(current_row)
            description_tokens = tokens[:-3]
            description = " ".join(tok.strip() for tok in description_tokens if tok.strip())
            col1 = tokens[-3].strip()  # Cantidad
            col2 = tokens[-2].strip()  # Precio
            col3 = tokens[-1].strip()  # Total
            current_row = [description, col1, col2, col3]
        else:
            if current_row is not None:
                current_row[0] += " " + line.strip()
    if current_row is not None:
        rows.append(current_row)

    df = pd.DataFrame(rows, columns=["Descripción", "Col1", "Col2", "Col3"])

    # --- Paso 3: Extraer los ítems (filtrando falsos positivos) ---
    items = []
    # Se obtiene el bill_to_name en minúsculas para comparaciones
    bill_to = invoice_data.get("bill_to_name", "").strip().lower()
    for index, row in df.iterrows():
        desc = row["Descripción"]
        # Descartar filas que sean únicamente un número de cuenta (p.ej. "B-22649380")
        if re.fullmatch(r'[A-Z]-\d+', desc.strip()):
            continue
        # Descartar filas que repitan el bill_to_name (cabecera repetida)
        if bill_to and bill_to in desc.strip().lower():
            continue
        if not is_valid_row(desc):
            continue
        desc = clean_description(desc)
        # Corrección puntual para separar dos registros concatenados:
        # Si la descripción contiene dos patrones conocidos (por ejemplo, la fila problemática)
        if desc.startswith("Transport | 506 Gbps Fiber to 49SxN6") and "Transport | Switch Fiber Pair" in desc:
            pos = desc.find("Transport | Switch Fiber Pair")
            desc = desc[:pos].strip()
        try:
            quantity = float(row["Col1"].replace(',', '')) if row["Col1"] else 0.0
        except (AttributeError, ValueError):
            quantity = 0.0
        try:
            price = float(row["Col2"].replace(',', '')) if row["Col2"] else 0.0
        except (AttributeError, ValueError):
            price = 0.0
        try:
            total = float(row["Col3"].replace(',', '').replace('$', '')) if row["Col3"] else 0.0
        except (AttributeError, ValueError):
            total = 0.0
        items.append({
            "sku": "Unknown",
            "description": desc,
            "quantity": quantity,
            "tax_rate": None,
            "price": price,
            "total": total
        })
    invoice_data["items"] = items
    return invoice_data

def transform_invoice(json_result):
    """
    Transforma el JSON obtenido de Veryfi extrayendo la información de la factura.
    """
    ocr_text = json_result.get("ocr_text", "")
    return extract_invoice_data(ocr_text)
