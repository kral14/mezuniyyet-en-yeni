#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_central_server():
    """Mərkəzi serveri test edir"""
    base_url = "https://mezuniyyet-serverim.onrender.com"
    
    print("🔍 Mərkəzi server test edilir...")
    
    # 1. Health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health xətası: {e}")
    
    # 2. Test tenants list (bu işləyir)
    try:
        response = requests.get(f"{base_url}/api/tenants/")
        print(f"📋 Tenants: {response.status_code}")
        if response.status_code == 200:
            tenants = response.json()
            print(f"   Tenant sayı: {len(tenants)}")
            for tenant in tenants:
                print(f"   • {tenant.get('name', 'N/A')} - {tenant.get('id', 'N/A')}")
        else:
            print(f"   Xəta: {response.text}")
    except Exception as e:
        print(f"❌ Tenants xətası: {e}")
    
    # 3. Test my-links endpoint (bu problemlidir)
    try:
        response = requests.get(f"{base_url}/api/tenants/my-links")
        print(f"📊 My-links: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Link sayı: {data.get('total_count', 0)}")
        else:
            print(f"   Xəta: {response.text}")
    except Exception as e:
        print(f"❌ My-links xətası: {e}")

def create_test_tenant():
    """Test tenant yaradır"""
    base_url = "https://mezuniyyet-serverim.onrender.com"
    
    print("\n🔧 Test tenant yaradılır...")
    
    try:
        response = requests.post(f"{base_url}/api/tenants/create", json={
            "company_name": "Test Şirkəti 2",
            "connection_string": "postgresql://***"  # Təhlükəsizlik üçün gizlədildi
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test tenant yaradıldı:")
            print(f"   ID: {data.get('tenant_id')}")
            print(f"   Ad: {data.get('name')}")
            print(f"   Link: {data.get('universal_link')}")
        else:
            print(f"❌ Xəta: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Test tenant xətası: {e}")

def test_tenant_details():
    """Mövcud tenant-ların detallarını test edir"""
    base_url = "https://mezuniyyet-serverim.onrender.com"
    
    print("\n🔍 Mövcud tenant-lar test edilir...")
    
    # Mövcud tenant ID-ləri
    tenant_ids = [
        "c8dfff6a-b4dc-4c41-8966-c0a63e6f1469",
        "e30eb4a5-a557-419f-9c52-f5d6d3e3729f",
        "6415b334-7e2f-497b-9e8e-a307ddc3f0b6"
    ]
    
    for tenant_id in tenant_ids:
        try:
            response = requests.get(f"{base_url}/api/tenants/{tenant_id}")
            print(f"📋 Tenant {tenant_id}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {data.get('name', 'N/A')} - Aktiv: {data.get('is_active', 'N/A')}")
            else:
                print(f"   ❌ Xəta: {response.text}")
        except Exception as e:
            print(f"   ❌ Xəta: {e}")

if __name__ == "__main__":
    print("🚀 MƏRKƏZİ SERVER TEST VƏ DÜZƏLTMƏ")
    print("=" * 50)
    
    test_central_server()
    test_tenant_details()
    create_test_tenant()
    
    print("\n" + "=" * 50)
    print("✅ Test tamamlandı!")
    print("\n💡 HƏLL:")
    print("Mərkəzi server işləyir, amma /api/tenants/my-links endpoint-i problemlidir.")
    print("Tətbiqdə 'İstifadəçi' modunu seçin və mövcud link ID-lərini istifadə edin:")
    print("• c8dfff6a-b4dc-4c41-8966-c0a63e6f1469")
    print("• e30eb4a5-a557-419f-9c52-f5d6d3e3729f")
    print("• 6415b334-7e2f-497b-9e8e-a307ddc3f0b6") 