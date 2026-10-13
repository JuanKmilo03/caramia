import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

class OdooClient:
    def __init__(self):
        self.url = os.getenv("ODOO_URL")
        self.db = os.getenv("ODOO_DB")
        self.username = os.getenv("ODOO_USER")
        self.password = os.getenv("ODOO_PASSWORD")
        
        try:
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            if self.uid:
                print("Conexión exitosa a Odoo XML-RPC")
        except Exception as e:
            print(f"Error conectando a Odoo: {e}")

    def buscar_datos(self, modelo, dominio, campos):
        """Método genérico para buscar datos en módulos como caramia_production o facturacion"""
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            modelo, 'search_read', [dominio], {'fields': campos}
        )

# Instancia global para ser reutilizada
odoo_db = OdooClient()