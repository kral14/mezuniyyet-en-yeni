#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# src yolunu əlavə edək
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def main():
    from database import database as db
    import psycopg2
    import json
    # Bağlantını bootstrap et (mövcud connection və ya tenant konfiqurasiyasından)
    try:
        # 1) Əvvəlcə mövcud connection string varsa ondan istifadə et
        existing_conn = db.get_connection_params()
        if not existing_conn:
            from core.tenant_manager import SettingsManager, LocalApiLogic
            from database.connection import set_connection_params as set_conn
            settings = SettingsManager()
            tenant_id = settings.get_tenant_id()
            if tenant_id:
                details, error = LocalApiLogic().get_tenant_details(tenant_id)
                if not error and details and details.get('connection_string'):
                    set_conn(details['connection_string'])
                    db.set_connection_params(details['connection_string'])
    except Exception:
        pass

    result = {
        'connected': False,
        'server_version': None,
        'current_database': None,
        'employee_count': None,
        'has_departments_table': None,
        'has_positions_table': None,
        'sample_departments': [],
        'sample_positions': []
    }

    conn = None
    try:
        conn = db.db_connect()
        if not conn:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        result['connected'] = True
        with conn.cursor() as cur:
            # Server və baza adı
            cur.execute("SELECT version(), current_database()")
            version, current_db = cur.fetchone()
            result['server_version'] = version
            result['current_database'] = current_db

            # Employees sayı
            try:
                cur.execute("SELECT COUNT(*) FROM employees")
                result['employee_count'] = cur.fetchone()[0]
            except psycopg2.Error:
                result['employee_count'] = 'table_missing'

            # Cədvəllərin olub-olmaması
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='departments')")
            result['has_departments_table'] = cur.fetchone()[0]
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='positions')")
            result['has_positions_table'] = cur.fetchone()[0]

            # Fallback oxunuşları
            if result['has_departments_table']:
                try:
                    cur.execute("SELECT name FROM departments WHERE is_active = TRUE ORDER BY name LIMIT 10")
                    result['sample_departments'] = [r[0] for r in cur.fetchall()]
                except psycopg2.Error:
                    pass
            else:
                try:
                    cur.execute("SELECT DISTINCT department FROM employees WHERE department IS NOT NULL AND department <> '' ORDER BY department LIMIT 10")
                    result['sample_departments'] = [r[0] for r in cur.fetchall()]
                except psycopg2.Error:
                    pass

            if result['has_positions_table']:
                try:
                    cur.execute("SELECT name FROM positions WHERE is_active = TRUE ORDER BY name LIMIT 10")
                    result['sample_positions'] = [r[0] for r in cur.fetchall()]
                except psycopg2.Error:
                    pass
            else:
                try:
                    cur.execute("SELECT DISTINCT position FROM employees WHERE position IS NOT NULL AND position <> '' ORDER BY position LIMIT 10")
                    result['sample_positions'] = [r[0] for r in cur.fetchall()]
                except psycopg2.Error:
                    pass

        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()


