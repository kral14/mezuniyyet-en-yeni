#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def main():
    from database import database as db
    from database.connection import set_connection_params as set_conn
    from core.tenant_manager import SettingsManager, LocalApiLogic
    import psycopg2

    # Bootstrap connection string via tenant
    try:
        settings = SettingsManager()
        tenant_id = settings.get_tenant_id()
        if tenant_id:
            details, error = LocalApiLogic().get_tenant_details(tenant_id)
            if not error and details and details.get('connection_string'):
                set_conn(details['connection_string'])
                db.set_connection_params(details['connection_string'])
    except Exception:
        pass

    conn = db.db_connect()
    if not conn:
        print("XETA: DB baglantisi alinmadi")
        return

    try:
        with conn.cursor() as cur:
            # Create departments table if not exists
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS departments (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

            # Create positions table if not exists
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    department_id INTEGER NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

            # Seed from employees distinct values
            # Departments
            try:
                cur.execute("SELECT DISTINCT department FROM employees WHERE department IS NOT NULL AND department <> ''")
                for (dept_name,) in cur.fetchall():
                    cur.execute("INSERT INTO departments (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (dept_name,))
            except psycopg2.Error:
                pass

            # Positions
            try:
                cur.execute("SELECT DISTINCT position FROM employees WHERE position IS NOT NULL AND position <> ''")
                for (pos_name,) in cur.fetchall():
                    cur.execute("INSERT INTO positions (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (pos_name,))
            except psycopg2.Error:
                pass

        conn.commit()
        print("OK: departments/positions cedvelleri temin olundu ve seed edildi")
    finally:
        conn.close()

if __name__ == "__main__":
    main()


