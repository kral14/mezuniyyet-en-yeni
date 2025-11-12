#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Şöbə və Vəzifə İdarəetməsi - Veritabanı Sorğuları
"""

import psycopg2
from .connection import db_connect

def check_tables_exist():
    """Şöbə və vəzifə cədvəllərinin mövcudluğunu yoxlayır"""
    conn = db_connect()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Hər iki cədvəlin mövcudluğunu yoxla
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'departments'
                ) AND EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'positions'
                )
            """)
            result = cur.fetchone()
            return result[0] if result else False
    except psycopg2.Error as e:
        print(f"Cədvəl yoxlaması xətası: {e}")
        return False
    finally:
        conn.close()

def create_departments_table():
    """Şöbələr cədvəlini yaradır"""
    conn = db_connect()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS departments (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Şöbələr cədvəli yaradıla bilmədi: {e}")
        return False
    finally:
        if conn:
            conn.close()

def create_positions_table():
    """Vəzifələr cədvəlini yaradır"""
    conn = db_connect()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Vəzifələr cədvəli yaradıla bilmədi: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_department(name, description=None):
    """Yeni şöbə əlavə edir"""
    conn = db_connect()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO departments (name, description) 
                VALUES (%s, %s)
            """, (name, description))
            conn.commit()
            return True
    except psycopg2.IntegrityError:
        print(f"Şöbə '{name}' artıq mövcuddur")
        return False
    except psycopg2.Error as e:
        print(f"Şöbə əlavə edilə bilmədi: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_position(name, department_id=None, description=None):
    """Yeni vəzifə əlavə edir"""
    conn = db_connect()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO positions (name, department_id, description) 
                VALUES (%s, %s, %s)
            """, (name, department_id, description))
            conn.commit()
            return True
    except psycopg2.IntegrityError:
        print(f"Vəzifə '{name}' artıq mövcuddur")
        return False
    except psycopg2.Error as e:
        print(f"Vəzifə əlavə edilə bilmədi: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_all_departments():
    """Bütün şöbələri gətirir"""
    conn = db_connect()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, description, created_at 
                FROM departments 
                ORDER BY name
            """)
            return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Şöbələr gətirilə bilmədi: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_positions():
    """Bütün vəzifələri gətirir"""
    conn = db_connect()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, p.name, p.description, p.department_id, d.name as department_name, p.created_at
                FROM positions p
                LEFT JOIN departments d ON p.department_id = d.id
                ORDER BY p.name
            """)
            return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Vəzifələr gətirilə bilmədi: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_department(department_id, name, description=None):
    """Şöbəni yeniləyir"""
    conn = db_connect()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE departments 
                SET name = %s, description = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (name, description, department_id))
            conn.commit()
            return True
    except psycopg2.IntegrityError:
        print(f"Şöbə '{name}' artıq mövcuddur")
        return False
    except psycopg2.Error as e:
        print(f"Şöbə yenilənə bilmədi: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_position(position_id, name, department_id=None, description=None):
    """Vəzifəni yeniləyir"""
    conn = db_connect()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE positions 
                SET name = %s, department_id = %s, description = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (name, department_id, description, position_id))
            conn.commit()
            return True
    except psycopg2.IntegrityError:
        print(f"Vəzifə '{name}' artıq mövcuddur")
        return False
    except psycopg2.Error as e:
        print(f"Vəzifə yenilənə bilmədi: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_department(department_id):
    """Şöbəni silir"""
    conn = db_connect()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Əvvəlcə bu şöbəyə aid vəzifələri yoxla
            cur.execute("SELECT COUNT(*) FROM positions WHERE department_id = %s", (department_id,))
            position_count = cur.fetchone()[0]
            
            if position_count > 0:
                print(f"Bu şöbəyə aid {position_count} vəzifə var. Əvvəlcə vəzifələri silin.")
                return False
            
            cur.execute("DELETE FROM departments WHERE id = %s", (department_id,))
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Şöbə silinə bilmədi: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_position(position_id):
    """Vəzifəni silir"""
    conn = db_connect()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM positions WHERE id = %s", (position_id,))
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Vəzifə silinə bilmədi: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_departments_for_combo():
    """Combo box üçün şöbələr siyahısını gətirir"""
    conn = db_connect()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM departments ORDER BY name")
            return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Şöbələr gətirilə bilmədi: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_positions_for_combo():
    """Combo box üçün vəzifələr siyahısını gətirir"""
    conn = db_connect()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM positions ORDER BY name")
            return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Vəzifələr gətirilə bilmədi: {e}")
        return []
    finally:
        if conn:
            conn.close()

def initialize_default_data():
    """Default şöbə və vəzifələri əlavə edir"""
    # Default şöbələr
    default_departments = [
        ("İnsan Resursları", "İnsan resursları idarəetməsi"),
        ("Maliyyə", "Maliyyə və mühasibatlıq"),
        ("İT", "İnformasiya texnologiyaları"),
        ("Marketinq", "Marketinq və satış"),
        ("İstehsal", "İstehsal və keyfiyyət"),
        ("Rəhbərlik", "Rəhbərlik və idarəetmə")
    ]
    
    # Default vəzifələr
    default_positions = [
        ("Direktor", None, "Direktor"),
        ("Baş direktor", None, "Baş direktor"),
        ("Menecer", None, "Menecer"),
        ("Mühasib", 2, "Mühasib"),  # Maliyyə şöbəsi
        ("Proqramçı", 3, "Proqramçı"),  # İT şöbəsi
        ("Dizayner", 4, "Dizayner"),  # Marketinq şöbəsi
        ("Operator", 5, "Operator"),  # İstehsal şöbəsi
        ("HR mütəxəssisi", 1, "HR mütəxəssisi"),  # İnsan Resursları
        ("Satış meneceri", 4, "Satış meneceri"),  # Marketinq
        ("Texnik", 5, "Texnik")  # İstehsal
    ]
    
    # Cədvəlləri yarat
    create_departments_table()
    create_positions_table()
    
    # Default şöbələri əlavə et
    for dept_name, dept_desc in default_departments:
        add_department(dept_name, dept_desc)
    
    # Default vəzifələri əlavə et
    for pos_name, dept_id, pos_desc in default_positions:
        add_position(pos_name, dept_id, pos_desc)
    
    print("Default şöbə və vəzifələr əlavə edildi")


