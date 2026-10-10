import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("ODOO_URL")
DB = os.getenv("ODOO_DB")
USER = os.getenv("ODOO_USER")
PASSWORD = os.getenv("ODOO_PASSWORD")

class OdooClient:
    def __init__(self):
        self.common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        # Autenticación: obtiene el ID del usuario (uid)
        self.uid = self.common.authenticate(DB, USER, PASSWORD, {})
        self.models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')
        
        if not self.uid:
            raise Exception("No se pudo autenticar con Odoo. Verifica las credenciales.")

    def search_read(self, model_name, domain, fields):
        """Busca registros en Odoo y devuelve los campos solicitados"""
        return self.models.execute_kw(DB, self.uid, PASSWORD,
            model_name, 'search_read', [domain], {'fields': fields})
            
    def create_record(self, model_name, values):
        """Crea un nuevo registro en Odoo"""
        return self.models.execute_kw(DB, self.uid, PASSWORD,
            model_name, 'create', [values])

# Instancia global para usar en nuestra API
odoo_db = OdooClient()