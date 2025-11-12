# tenant_manager.py (relink funksiyası əlavə edilmiş)

import os
import json
import uuid
import logging
# YENİ VƏZİYYƏT (Düzəldilmiş) - Yalnız Neon bazası istifadə edilir
# SQLAlchemy import-ları silindi - lokal bazaya ehtiyac yoxdur

# Logging səviyyəsini DEBUG-a təyin edirik - bütün loglar görünsün
logging.getLogger().setLevel(logging.DEBUG)

# === Mərkəzi Baza və Modellər (Yalnız Neon bazası istifadə edilir) ===
# Lokal SQLite bazası tamamilə silindi - bütün məlumatlar Neon bazasına yazılır

def init_main_db():
    """Lokal bazanı başlatmaq lazım deyil - bütün məlumatlar Neon bazasındadır."""
    logging.info("Lokal bazanı başlatmaq lazım deyil - bütün məlumatlar Neon bazasındadır")

# === Mərkəzi Server Client ===
import requests

class CentralServerClient:
    def __init__(self, server_url: str = "https://mezuniyyet-serverim.onrender.com"):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
    
    def create_tenant(self, company_name: str, connection_string: str):
        """Mərkəzi serverdə yeni şirkət yaradır"""
        try:
            response = self.session.post(
                f"{self.server_url}/api/tenants/create",
                json={
                    "company_name": company_name,
                    "connection_string": connection_string
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Server xətası: {str(e)}"}
    
    def get_tenant(self, tenant_id: str):
        """Mərkəzi serverdən şirkət məlumatlarını alır"""
        try:
            response = self.session.get(f"{self.server_url}/api/tenants/{tenant_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Server xətası: {str(e)}"}
    
    def search_tenant_by_name(self, company_name: str):
        """Şirkət adına görə axtarış edir"""
        try:
            response = self.session.get(f"{self.server_url}/api/tenants/search/{company_name}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Server xətası: {str(e)}"}
    
    def find_tenant_by_connection(self, connection_string: str):
        """Connection string-ə görə tenant tapır"""
        import hashlib
        try:
            # Connection string-in hash-ini hesablayırıq
            conn_hash = hashlib.md5(connection_string.encode()).hexdigest()
            response = self.session.get(f"{self.server_url}/api/tenants/link/{conn_hash}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Server xətası: {str(e)}"}
    
    def get_tenant_stats(self, tenant_id: str):
        """Şirkətin statistikasını alır"""
        try:
            response = self.session.get(f"{self.server_url}/api/tenants/stats/{tenant_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Server xətası: {str(e)}"}
    
    def get_all_my_links(self):
        """Bütün aktiv linkləri alır"""
        try:
            response = self.session.get(f"{self.server_url}/api/tenants/my-links")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Server xətası: {str(e)}"}
    
    def send_reset_email(self, to_email: str, employee_name: str, tenant_id: str = None):
        """Server-ə email göndərmə sorğusu göndərir"""
        import logging
        logging.info(f"📤 [SERVER_REQUEST] Email göndərmə sorğusu hazırlanır: Email={to_email}, Ad={employee_name}, TenantID={tenant_id}")
        
        try:
            payload = {
                "to_email": to_email,
                "employee_name": employee_name
            }
            if tenant_id:
                payload["tenant_id"] = tenant_id
            
            logging.info(f"📤 [SERVER_REQUEST] Sorğu göndərilir: URL={self.server_url}/api/email/send-reset, Payload={payload}")
            
            response = self.session.post(
                f"{self.server_url}/api/email/send-reset",
                json=payload,
                timeout=15  # Optimallaşdırıldı: 30 → 15 saniyə
            )
            
            logging.info(f"📥 [SERVER_REQUEST] Server cavabı alındı: Status={response.status_code}, Email={to_email}")
            
            response.raise_for_status()
            result = response.json()
            logging.info(f"✅ [SERVER_REQUEST] Server cavabı uğurlu: {result}, Email={to_email}")
            return result
        except requests.exceptions.Timeout:
            return {"error": "Server cavab vermədi (timeout 15 saniyə). Zəhmət olmasa yenidən cəhd edin.", "error_type": "TIMEOUT"}
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            # Daha yaxşı error mesajları
            if "Network is unreachable" in error_msg or "101" in error_msg:
                return {"error": "İnternet bağlantısı yoxdur və ya server əlçatan deyil. Zəhmət olmasa internet bağlantınızı yoxlayın.", "error_type": "NETWORK_ERROR"}
            elif "Name or service not known" in error_msg:
                return {"error": "Server ünvanı tapılmadı. Zəhmət olmasa server statusunu yoxlayın.", "error_type": "DNS_ERROR"}
            else:
                return {"error": f"Server-ə qoşula bilmədi: {error_msg}. Zəhmət olmasa internet bağlantınızı yoxlayın.", "error_type": "CONNECTION_ERROR"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Server xətası: {str(e)}", "error_type": "REQUEST_ERROR"}
    
    def verify_reset_code(self, email: str, code: str, tenant_id: str = None):
        """Server-ə reset kodu yoxlama sorğusu göndərir"""
        try:
            payload = {
                "email": email,
                "code": code
            }
            if tenant_id:
                payload["tenant_id"] = tenant_id
            
            response = self.session.post(
                f"{self.server_url}/api/email/verify-reset-code",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "Server cavab vermədi (timeout)"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Server xətası: {str(e)}"}

# === Lokal API Məntiqi (Serverə ehtiyac olmadan şirkət məlumatlarını idarə edir) ===
class LocalApiLogic:
    """ HTTP sorğuları yerinə birbaşa Neon bazası ilə işləyir. """
    def get_tenant_details(self, tenant_id_str: str):
        logging.info(f"get_tenant_details çağırıldı. Axtarılan ID: {tenant_id_str}")
        
        # Mərkəzi serverdən məlumatları alırıq
        central_client = CentralServerClient()
        result = central_client.get_tenant(tenant_id_str)
        
        if "error" in result:
            logging.error(f"Mərkəzi server xətası: {result['error']}")
            return None, f"Mərkəzi server xətası: {result['error']}"
        
        if "id" in result:
            logging.info(f"Şirkət tapıldı: {result['name']} (ID: {result['id']})")
            # Təhlükəsizlik: Connection string log-larda göstərilmir, yalnız tenant_id log-lanır
            logging.info(f"Database konfiqurasiyası təyin edildi (tenant_id: {result['id']})")
            return {
                "tenant_id": result["id"], 
                "name": result["name"], 
                "connection_string": result["connection_string"]
            }, None
        else:
            logging.warning(f"ID {tenant_id_str} ilə heç bir şirkət tapılmadı.")
            return None, "Şirkət tapılmadı"

    def create_tenant(self, company_name: str, connection_string: str):
        logging.info(f"create_tenant çağırıldı. Şirkət adı: {company_name}")
        
        # Veritaban qoşulmasını test edirik
        from database_manager import DatabaseManager
        db_manager = DatabaseManager()
        success, message = db_manager.test_connection(connection_string)
        
        if not success:
            logging.error(f"Veritaban qoşulma xətası: {message}")
            return None, f"Veritaban qoşulma xətası: {message}"
        
        # Veritaban məlumatlarını alırıq
        db_info = db_manager.get_database_info(connection_string)
        logging.info(f"Veritaban növü: {db_info['name']} ({db_info['type']})")
        
        # Mərkəzi serverə göndəririk
        central_client = CentralServerClient()
        result = central_client.create_tenant(company_name, connection_string)
        
        if "error" in result:
            logging.error(f"Mərkəzi server xətası: {result['error']}")
            return None, f"Mərkəzi server xətası: {result['error']}"
        
        if "tenant_id" in result:
            logging.info(f"Universal link yaradıldı: {result['tenant_id']}")
            return {
                "tenant_id": result["tenant_id"], 
                "universal_link": result.get("universal_link"),
                "database_type": db_info['name'],
                "database_info": db_info
            }, None
        else:
            logging.error("Mərkəzi serverdən düzgün cavab alınmadı")
            return None, "Mərkəzi serverdən düzgün cavab alınmadı"

    # --- YENİ FUNKSİYA BURADADIR ---
    def relink_to_tenant(self, connection_string: str):
        """Verilmiş qoşulma sətrinə görə mövcud şirkəti tapıb linkini qaytarır."""
        logging.info(f"relink_to_tenant çağırıldı.")
        
        # Connection string boşdursa və ya None-dursa, xəta qaytarırıq
        if not connection_string or connection_string.strip() == "":
            logging.warning("Database konfiqurasiyası boşdur")
            return None, "Veritaban qoşulma məlumatları boşdur"
        
        # Mərkəzi serverdən axtarış edirik
        central_client = CentralServerClient()
        result = central_client.find_tenant_by_connection(connection_string)
        
        if "error" in result:
            logging.error(f"Mərkəzi server xətası: {result['error']}")
            return None, f"Mərkəzi server xətası: {result['error']}"
        
        if "id" in result:
            logging.info(f"Şirkət tapıldı: {result['name']}")
            return {
                "tenant_id": result["id"], 
                "name": result["name"],
                "universal_link": result.get("universal_link"),
                "access_count": result.get("access_count", "0")
            }, None
        else:
            logging.warning("Bu database konfiqurasiyası ilə heç bir şirkət tapılmadı.")
            return None, "Bu verilənlər bazası məlumatları ilə heç bir şirkət qeydiyyatdan keçməyib."
    
    def search_company_by_name(self, company_name: str):
        """Şirkət adına görə axtarış edir"""
        logging.info(f"search_company_by_name çağırıldı: {company_name}")
        
        central_client = CentralServerClient()
        result = central_client.search_tenant_by_name(company_name)
        
        if "error" in result:
            logging.error(f"Mərkəzi server xətası: {result['error']}")
            return None, f"Mərkəzi server xətası: {result['error']}"
        
        if "results" in result:
            logging.info(f"{len(result['results'])} şirkət tapıldı")
            return result, None
        else:
            logging.warning("Axtarış nəticəsi alına bilmədi")
            return None, "Axtarış nəticəsi alına bilmədi"
    
    def get_my_all_links(self):
        """Bütün aktiv linkləri alır"""
        logging.info("get_my_all_links çağırıldı")
        
        central_client = CentralServerClient()
        result = central_client.get_all_my_links()
        
        if "error" in result:
            logging.error(f"Mərkəzi server xətası: {result['error']}")
            return None, f"Mərkəzi server xətası: {result['error']}"
        
        if "links" in result:
            logging.info(f"{len(result['links'])} link tapıldı")
            return result["links"], None
        else:
            logging.warning("Linklər alına bilmədi")
            return None, "Linklər alına bilmədi"
            
class SettingsManager:
    """Client tərəfdə tenant_id-ni saxlamaq üçün menecer."""
    def __init__(self, filename="tenant_settings.json"):
        app_data_dir = os.path.join(os.getenv('APPDATA'), 'MezuniyyetSistemi')
        os.makedirs(app_data_dir, exist_ok=True)
        
        self.filepath = os.path.join(app_data_dir, filename)
        self.data = self._load()

    def _load(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"tenant_id": None, "company_name": None}

    def save(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    def get_tenant_id(self):
        return self.data.get("tenant_id")

    def get_company_name(self):
        return self.data.get("company_name")

    def set_active_tenant(self, tenant_id, company_name):
        self.data["tenant_id"] = str(tenant_id) if tenant_id else None
        self.data["company_name"] = company_name if tenant_id else None
        self.save()

    def clear_active_tenant(self):
        self.set_active_tenant(None, None)

# init_main_db() çağırılması silindi - lokal bazaya ehtiyac yoxdur