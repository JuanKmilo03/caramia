import xmlrpc.client
import os

class OdooClient:
    def __init__(self):
        self.url = os.getenv("ODOO_URL")
        self.db = os.getenv("ODOO_DB")
        self.username = os.getenv("ODOO_USER")
        self.password = os.getenv("ODOO_PASSWORD")
        self.models = None
        self.uid = None

    def conectar(self):
        if self.uid and self.models:
            return True
            
        try:
            print(f"Intentando conectar a Odoo en {self.url}...")
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            
            if self.uid:
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                print("Conexión exitosa a Odoo XML-RPC")
                return True
            else:
                print("Fallo la autenticación: Credenciales o Base de Datos incorrectas.")
                return False
        except Exception as e:
            print(f"Error conectando a Odoo: {e}")
            return False

    def buscar_datos(self, modelo, dominio, campos):
        if not self.conectar():
            return None
            
        try:
            registros = self.models.execute_kw(
                self.db, self.uid, self.password,
                modelo, 'search_read',
                [dominio],
                {'fields': campos}
            )
            return registros
        except Exception as e:
            print(f"Error ejecutando búsqueda en Odoo: {e}")
            return None

odoo_db = OdooClient()