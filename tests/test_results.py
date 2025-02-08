import os
import json
import unittest
from datetime import datetime

class TestProcessedResults(unittest.TestCase):
    def setUp(self):
        # Define las rutas a las carpetas de salida de Veryfi y de resultados procesados.
        # Se asume que las carpetas "veryfi_jsons" y "results" están en el directorio raíz.
        self.veryfi_folder = os.path.join(os.getcwd(), "veryfi_jsons")
        self.results_folder = os.path.join(os.getcwd(), "results")
    
    def parse_transformed_date(self, date_str):
        """
        Convierte la fecha extraída en el resultado (formato MM/DD/YY) a un objeto date.
        Por ejemplo: "09/22/23" → datetime.date(2023, 9, 22)
        """
        return datetime.strptime(date_str, "%m/%d/%y").date()
    
    def parse_veryfi_date(self, date_str):
        """
        Convierte la fecha del JSON de Veryfi (formato "YYYY-MM-DD HH:MM:SS")
        a un objeto date.
        Por ejemplo: "2023-09-22 00:00:00" → datetime.date(2023, 9, 22)
        """
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
    
    def test_results_match_veryfi(self):
        """
        Para cada archivo JSON en la carpeta de resultados, se busca el archivo con el mismo nombre
        en la carpeta de veryfi_jsons y se comparan los campos clave.
        """
        for file_name in os.listdir(self.results_folder):
            if file_name.endswith(".json"):
                result_file_path = os.path.join(self.results_folder, file_name)
                veryfi_file_path = os.path.join(self.veryfi_folder, file_name)
                
                with self.subTest(file=file_name):
                    # Verifica que exista el archivo correspondiente en veryfi_jsons
                    self.assertTrue(
                        os.path.exists(veryfi_file_path),
                        msg=f"No se encontró el archivo {veryfi_file_path}"
                    )
                    
                    # Carga ambos archivos JSON
                    with open(result_file_path, "r", encoding="utf-8") as f:
                        result_data = json.load(f)
                    with open(veryfi_file_path, "r", encoding="utf-8") as f:
                        veryfi_data = json.load(f)
                    
                    # Comparar el número de factura
                    self.assertEqual(
                        result_data.get("invoice_number"),
                        veryfi_data.get("invoice_number"),
                        msg=f"Invoice number mismatch in {file_name}"
                    )
                    
                    # Comparar el nombre del cliente (bill_to_name en el resultado vs. bill_to.name en Veryfi)
                    self.assertEqual(
                        result_data.get("bill_to_name"),
                        veryfi_data.get("bill_to", {}).get("name"),
                        msg=f"Bill to name mismatch in {file_name}"
                    )
                    
                    # Comparar el nombre del proveedor (vendor_name en el resultado vs. vendor.name en Veryfi)
                    self.assertEqual(
                        result_data.get("vendor_name"),
                        veryfi_data.get("vendor", {}).get("name"),
                        msg=f"Vendor name mismatch in {file_name}"
                    )
                    
                    # Comparar la fecha. Se convierte el formato de ambos para obtener la misma fecha.
                    result_date_str = result_data.get("date")
                    veryfi_date_str = veryfi_data.get("date")
                    try:
                        result_date = self.parse_transformed_date(result_date_str)
                        veryfi_date = self.parse_veryfi_date(veryfi_date_str)
                        self.assertEqual(
                            result_date, 
                            veryfi_date,
                            msg=f"Date mismatch in {file_name}"
                        )
                    except Exception as e:
                        self.fail(f"Date parsing error in {file_name}: {e}")
                    
                    # Comparar la cantidad de ítems (items en el resultado vs. line_items en Veryfi)
                    result_items = result_data.get("items", [])
                    veryfi_items = veryfi_data.get("line_items", [])
                    self.assertEqual(
                        len(result_items),
                        len(veryfi_items),
                        msg=f"Line items count mismatch in {file_name}"
                    )
                    
                    # Comparar, de forma opcional, la suma total de los montos de los ítems
                    result_total = sum(item.get("total", 0) for item in result_items)
                    veryfi_total = sum(item.get("total", 0) for item in veryfi_items)
                    # Se permite una pequeña diferencia por redondeos (2 decimales)
                    self.assertAlmostEqual(
                        result_total,
                        veryfi_total,
                        places=2,
                        msg=f"Total amounts mismatch in {file_name}"
                    )

if __name__ == "__main__":
    unittest.main()
