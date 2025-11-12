# cache_manager.py

import json
import os
import time
import logging
from datetime import datetime
import base64
from cryptography.fernet import Fernet

# İstifadəçi məlumatları üçün faylın saxlanacağı yer
# APPDATA qovluğu hər istifadəçi üçün fərqli və gizli olduğu üçün daha təhlükəsizdir
APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'MezuniyyetSistemi')
CACHE_FILE = os.path.join(APP_DATA_DIR, 'user_cache.json')
CACHE_META_FILE = os.path.join(APP_DATA_DIR, 'cache_meta.json')
USER_DATA_FILE = os.path.join(APP_DATA_DIR, 'user_data.json')  # Yeni fayl
KEY_FILE = os.path.join(APP_DATA_DIR, 'encryption.key')  # Şifrələmə açarı

def get_or_create_encryption_key():
    """Şifrələmə açarını alır və ya yaradır"""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        # Yeni açar yaradırıq
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        return key

def encrypt_data(data):
    """Məlumatları şifrələyir"""
    try:
        key = get_or_create_encryption_key()
        fernet = Fernet(key)
        # String-ə çevir və şifrələ
        data_str = json.dumps(data, ensure_ascii=False)
        encrypted_data = fernet.encrypt(data_str.encode())
        return base64.b64encode(encrypted_data).decode()
    except Exception as e:
        logging.error(f"Şifrələmə xətası: {e}")
        return None

def decrypt_data(encrypted_data):
    """Məlumatları deşifrələyir"""
    try:
        key = get_or_create_encryption_key()
        fernet = Fernet(key)
        # Base64 decode et və deşifrələ
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(encrypted_bytes)
        return json.loads(decrypted_data.decode())
    except Exception as e:
        logging.error(f"Deşifrələmə xətası: {e}")
        return None

def load_cache():
    """Yadda saxlanmış istifadəçi məlumatlarını fayldan oxuyur - TƏHLÜKƏSİZLİK ÜÇÜN YALNIZ USERNAME"""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # TƏHLÜKƏSİZLİK: Yalnız username və remember_me saxlanılır
            # İşçi məlumatları heç vaxt cache edilmir
            filtered_data = {}
            if 'username' in data:
                filtered_data['username'] = data['username']
            if 'remember_me' in data:
                filtered_data['remember_me'] = data['remember_me']
            return filtered_data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.warning(f"Cache faylı pozulub, təmizlənir: {e}")
        # Pozulmuş cache faylını silirik
        try:
            os.remove(CACHE_FILE)
        except OSError:
            pass
        return {}

def _deserialize_data(data):
    """Date stringlərini date obyektlərinə çevirir"""
    from datetime import date, datetime
    
    if isinstance(data, dict):
        return {key: _deserialize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_deserialize_data(item) for item in data]
    elif isinstance(data, str):
        # Date string formatını yoxla
        try:
            if len(data) == 10 and data.count('-') == 2:  # YYYY-MM-DD formatı
                return datetime.strptime(data, '%Y-%m-%d').date()
            elif len(data) == 19 and data.count('-') == 2 and data.count(':') == 2:  # YYYY-MM-DD HH:MM:SS formatı
                return datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    return data

def save_cache(data):
    """İstifadəçi məlumatlarını fayla yazır."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        
        # Date obyektlərini string-ə çevir
        serialized_data = _serialize_data(data)
        
        # Əvvəlcə temp fayla yazırıq
        temp_file = CACHE_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(serialized_data, f, indent=4, ensure_ascii=False)
        
        # Əgər temp fayl uğurlu yazıldısa, əsas faylla əvəz edirik
        if os.path.exists(temp_file):
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
            os.rename(temp_file, CACHE_FILE)
            logging.debug(f"Cache faylı uğurla yazıldı: {CACHE_FILE}")
        else:
            logging.error("Temp cache faylı yaradıla bilmədi")
            
    except Exception as e:
        logging.error(f"Cache faylı yazma xətası: {e}")
        # Temp faylı silirik
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except OSError:
            pass
    
    # Cache metadata-nı da yenilə
    save_cache_meta()

def _serialize_data(data):
    """Date obyektlərini string-ə çevirir"""
    if isinstance(data, dict):
        return {key: _serialize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_serialize_data(item) for item in data]
    elif hasattr(data, 'isoformat'):  # datetime.date və datetime.datetime
        return data.isoformat()
    else:
        return data

def load_user_data():
    """İstifadəçi məlumatlarını ayrı fayldan oxuyur (həmişə saxlanılır)"""
    if not os.path.exists(USER_DATA_FILE):
        # Fayl yoxdursa, boş dict qaytarırıq
        return {}
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return _deserialize_data(data)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.warning(f"User data faylı pozulub, təmizlənir: {e}")
        # Pozulmuş user data faylını silirik
        try:
            os.remove(USER_DATA_FILE)
        except OSError:
            pass
        return {}
    except Exception as e:
        logging.error(f"User data faylı oxuma xətası: {e}")
        return {}

def save_user_data(data):
    """İstifadəçi məlumatlarını ayrı fayla yazır (həmişə saxlanılır)"""
    try:
        os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
        
        # Əvvəlcə temp fayla yazırıq
        temp_file = USER_DATA_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Əgər temp fayl uğurlu yazıldısa, əsas faylla əvəz edirik
        if os.path.exists(temp_file):
            if os.path.exists(USER_DATA_FILE):
                os.remove(USER_DATA_FILE)
            os.rename(temp_file, USER_DATA_FILE)
            logging.info("İstifadəçi məlumatları saxlanıldı")
        else:
            logging.error("Temp user data faylı yaradıla bilmədi")
            
    except Exception as e:
        logging.error(f"User data faylı yazma xətası: {e}")
        # Temp faylı silirik
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except OSError:
            pass

def get_user_credentials():
    """İstifadəçi məlumatlarını şifrələnmiş fayllardan oxuyur"""
    try:
        username = ''
        password = ''
        remember_me = False
        
        # Əvvəlcə user_data faylını yoxlayırıq
        if os.path.exists(USER_DATA_FILE):
            try:
                with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                    data_content = f.read().strip()
                
                # Faylın formatını yoxla - JSON və ya şifrələnmiş
                if data_content and data_content.startswith('{'):
                    # JSON formatı (köhnə format)
                    try:
                        user_data = json.loads(data_content)
                        logging.debug("get_user_credentials: user_data JSON formatında tapıldı")
                    except json.JSONDecodeError:
                        logging.warning("user_data JSON formatında deyil, boş hesab edilir")
                        user_data = None
                else:
                    # Şifrələnmiş format
                    user_data = decrypt_data(data_content)
                    logging.debug("get_user_credentials: user_data şifrələnmiş formatda tapıldı")
                
                if user_data and user_data.get('remember_me', False):
                    username = user_data.get('username', '')
                    password = user_data.get('password', '')
                    remember_me = user_data.get('remember_me', False)
                    logging.info("get_user_credentials: user_data-dan məlumatlar alındı")
                else:
                    logging.info(f"get_user_credentials: user_data-dan məlumatlar alına bilmədi - user_data exists: {user_data is not None}, remember_me: {user_data.get('remember_me', False) if user_data else 'N/A'}")
            except Exception as e:
                logging.warning(f"user_data faylı oxuna bilmədi: {e}", exc_info=True)
        
        # Əgər user_data-dan alınmadısa, cache faylını yoxlayırıq
        if not username and os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data_content = f.read().strip()
                
                # Faylın formatını yoxla - JSON və ya şifrələnmiş
                if data_content and data_content.startswith('{'):
                    # JSON formatı (köhnə format)
                    try:
                        cache_data = json.loads(data_content)
                        logging.debug("get_user_credentials: cache JSON formatında tapıldı")
                    except json.JSONDecodeError:
                        logging.warning("cache JSON formatında deyil, boş hesab edilir")
                        cache_data = None
                else:
                    # Şifrələnmiş format
                    cache_data = decrypt_data(data_content)
                    logging.debug("get_user_credentials: cache şifrələnmiş formatda tapıldı")
                
                if cache_data and cache_data.get('remember_me', False):
                    username = cache_data.get('username', '')
                    password = cache_data.get('password', '')
                    remember_me = cache_data.get('remember_me', False)
                    logging.info("get_user_credentials: cache-dən məlumatlar alındı")
                else:
                    logging.info(f"get_user_credentials: cache-dən məlumatlar alına bilmədi - cache_data exists: {cache_data is not None}, remember_me: {cache_data.get('remember_me', False) if cache_data else 'N/A'}")
            except Exception as e:
                logging.warning(f"cache faylı oxuna bilmədi: {e}", exc_info=True)
        
        result = {
            'username': username,
            'password': password,
            'remember_me': remember_me
        }
        
        logging.info(f"get_user_credentials: Final credentials: username='{username}', password_length={len(password) if password else 0}, remember_me={remember_me}")
        return result
    except Exception as e:
        logging.error(f"get_user_credentials xətası: {e}", exc_info=True)
        return {'username': '', 'password': '', 'remember_me': False}

def save_user_credentials(username, password, remember_me):
    """İstifadəçi məlumatlarını şifrələyərək saxlayır - TƏHLÜKƏSİZLİK ÜÇÜN ŞİFRƏLƏNİR"""
    logging.info(f"save_user_credentials çağırıldı: username='{username}', remember_me={remember_me}")
    
    if remember_me:
        # TƏHLÜKƏSİZLİK: Məlumatlar şifrələnərək saxlanılır
        user_data = {
            'username': username,
            'password': password,  # Şifrələnəcək
            'remember_me': True,
            'last_saved': datetime.now().isoformat()
        }
        
        # Məlumatları şifrələyirik
        encrypted_data = encrypt_data(user_data)
        if encrypted_data:
            # Şifrələnmiş məlumatları fayla yazırıq
            os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
            with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
            logging.info("İstifadəçi məlumatları şifrələnərək saxlanıldı")
        else:
            logging.error("Məlumatlar şifrələnə bilmədi")
            return
        
        # Cache-də də şifrələnmiş məlumatları saxlayırıq
        cache_data = {
            'username': username,
            'password': password,  # Şifrələnəcək
            'remember_me': True
        }
        encrypted_cache = encrypt_data(cache_data)
        if encrypted_cache:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                f.write(encrypted_cache)
            logging.info("Cache məlumatları şifrələnərək saxlanıldı")
        else:
            logging.error("Cache məlumatları şifrələnə bilmədi")
    else:
        # Remember me seçilməyibsə, bütün məlumatları silirik
        if os.path.exists(USER_DATA_FILE):
            os.remove(USER_DATA_FILE)
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        logging.info("İstifadəçi məlumatları silindi")

def clear_cache():
    """Bütün cache fayllarını təmizləyir (istifadəçi məlumatları da daxil)"""
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except OSError as e:
            logging.warning(f"Cache faylı silinə bilmədi: {e}")
    
    if os.path.exists(CACHE_META_FILE):
        try:
            os.remove(CACHE_META_FILE)
        except OSError as e:
            logging.warning(f"Cache meta faylı silinə bilmədi: {e}")
    
    if os.path.exists(USER_DATA_FILE):
        try:
            os.remove(USER_DATA_FILE)
        except OSError as e:
            logging.warning(f"User data faylı silinə bilmədi: {e}")
    
    # Şifrələmə açarını da silirik
    if os.path.exists(KEY_FILE):
        try:
            os.remove(KEY_FILE)
            logging.info("Şifrələmə açarı silindi")
        except OSError as e:
            logging.warning(f"Şifrələmə açarı silinə bilmədi: {e}")

def clear_database_cache_only():
    """Yalnız database cache-ini təmizləyir, istifadəçi məlumatlarını saxlayır"""
    if os.path.exists(CACHE_META_FILE):
        try:
            os.remove(CACHE_META_FILE)
            logging.info("Yalnız database cache təmizləndi")
        except OSError as e:
            logging.warning(f"Cache meta faylı silinə bilmədi: {e}")
    
    # İstifadəçi məlumatları saxlanılır
    logging.info("İstifadəçi məlumatları saxlanıldı")

def save_cache_meta():
    """Cache metadata-nı saxlayır"""
    meta = {
        'last_updated': datetime.now().isoformat(),
        'timestamp': time.time()
    }
    os.makedirs(os.path.dirname(CACHE_META_FILE), exist_ok=True)
    with open(CACHE_META_FILE, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=4)

def load_cache_meta():
    """Cache metadata-nı oxuyur"""
    if not os.path.exists(CACHE_META_FILE):
        return None
    try:
        with open(CACHE_META_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def is_cache_valid(max_age_seconds=1800):  # 30 dəqiqə default - performans üçün artırıldı
    """Cache-in etibarlı olub-olmadığını yoxlayır"""
    meta = load_cache_meta()
    if not meta:
        return False
    
    current_time = time.time()
    cache_time = meta.get('timestamp', 0)
    return (current_time - cache_time) < max_age_seconds

def is_cache_valid_for_user(max_age_seconds=3600):  # 1 saat user cache üçün - performans artırıldı
    """User cache-in etibarlı olub-olmadığını yoxlayır"""
    meta = load_cache_meta()
    if not meta:
        return False
    
    current_time = time.time()
    cache_time = meta.get('timestamp', 0)
    return (current_time - cache_time) < max_age_seconds

def invalidate_cache():
    """Cache-i etibarsız edir (yalnız database cache)"""
    clear_database_cache_only()

def force_cache_refresh():
    """Cache-i məcburi yeniləyir (yalnız database cache)"""
    clear_database_cache_only()
    logging.info("Database cache məcburi yeniləndi")

def clear_all_cache():
    """Bütün cache fayllarını təmizləyir (istifadəçi məlumatları da daxil)"""
    clear_cache()
    logging.info("Bütün cache faylları təmizləndi")

def has_saved_credentials():
    """Saxlanmış istifadəçi məlumatlarının olub-olmadığını yoxlayır - ŞİFRƏLƏNİR"""
    try:
        # Əvvəlcə user_data faylını yoxlayırıq
        if os.path.exists(USER_DATA_FILE):
            try:
                with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                    encrypted_data = f.read()
                
                user_data = decrypt_data(encrypted_data)
                if user_data and user_data.get('username') and user_data.get('remember_me', False):
                    logging.debug("has_saved_credentials: user_data-dan şifrələnmiş məlumatlar tapıldı")
                    return True
            except Exception as e:
                logging.warning(f"user_data faylı oxuna bilmədi: {e}")
        
        # Əgər user_data-dan tapılmadısa, cache faylını yoxlayırıq
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    encrypted_data = f.read()
                
                cache_data = decrypt_data(encrypted_data)
                if cache_data and cache_data.get('username') and cache_data.get('remember_me', False):
                    logging.debug("has_saved_credentials: cache-dən şifrələnmiş məlumatlar tapıldı")
                    return True
            except Exception as e:
                logging.warning(f"cache faylı oxuna bilmədi: {e}")
        
        logging.debug("has_saved_credentials: heç bir yerdə tapılmadı")
        return False
    except Exception as e:
        logging.error(f"has_saved_credentials xətası: {e}")
        return False