#!/usr/bin/env python3
"""
Focused test for primary designation logic and data persistence
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"
API_URL = f"{BASE_URL}/api"

def test_primary_designation_logic():
    """Test that only one primary applicant/credential exists at a time"""
    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json'})
    
    print("🔍 Testing Primary Designation Logic")
    print("=" * 50)
    
    # Create first applicant as primary
    applicant1 = {
        "first_name": "John",
        "last_name": "Doe", 
        "passport_number": "US123456789",
        "nationality": "American",
        "phone_number": "+1234567890",
        "email": "john.doe@email.com",
        "is_primary": True
    }
    
    response1 = session.post(f"{API_URL}/applicants", json=applicant1)
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"✅ Created first applicant: {data1['first_name']} {data1['last_name']} (Primary: {data1['is_primary']})")
        applicant1_id = data1['id']
    else:
        print(f"❌ Failed to create first applicant: {response1.status_code}")
        return
    
    # Create second applicant as primary (should unset first one)
    applicant2 = {
        "first_name": "Jane",
        "last_name": "Smith",
        "passport_number": "CA987654321", 
        "nationality": "Canadian",
        "phone_number": "+1987654321",
        "email": "jane.smith@email.com",
        "is_primary": True
    }
    
    response2 = session.post(f"{API_URL}/applicants", json=applicant2)
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"✅ Created second applicant: {data2['first_name']} {data2['last_name']} (Primary: {data2['is_primary']})")
        applicant2_id = data2['id']
    else:
        print(f"❌ Failed to create second applicant: {response2.status_code}")
        return
    
    # Verify first applicant is no longer primary
    check1 = session.get(f"{API_URL}/applicants/{applicant1_id}")
    if check1.status_code == 200:
        check1_data = check1.json()
        print(f"✅ First applicant primary status: {check1_data['is_primary']} (should be False)")
    
    # Verify only one primary exists
    primary_response = session.get(f"{API_URL}/applicants/primary/info")
    if primary_response.status_code == 200:
        primary_data = primary_response.json()
        print(f"✅ Primary applicant: {primary_data['first_name']} {primary_data['last_name']} (ID: {primary_data['id']})")
        if primary_data['id'] == applicant2_id:
            print("✅ Primary designation logic working correctly!")
        else:
            print("❌ Primary designation logic failed!")
    
    # Test same logic for credentials
    print("\n🔐 Testing Credential Primary Logic")
    print("-" * 30)
    
    # Create first credential as primary
    cred1 = {
        "credential_name": "Account 1",
        "email": "account1@test.com",
        "password": "password123",
        "is_primary": True
    }
    
    cred1_response = session.post(f"{API_URL}/credentials", json=cred1)
    if cred1_response.status_code == 200:
        cred1_data = cred1_response.json()
        print(f"✅ Created first credential: {cred1_data['credential_name']} (Primary: {cred1_data['is_primary']})")
        cred1_id = cred1_data['id']
    
    # Create second credential as primary
    cred2 = {
        "credential_name": "Account 2", 
        "email": "account2@test.com",
        "password": "password456",
        "is_primary": True
    }
    
    cred2_response = session.post(f"{API_URL}/credentials", json=cred2)
    if cred2_response.status_code == 200:
        cred2_data = cred2_response.json()
        print(f"✅ Created second credential: {cred2_data['credential_name']} (Primary: {cred2_data['is_primary']})")
        cred2_id = cred2_data['id']
    
    # Verify primary credential logic
    primary_cred_response = session.get(f"{API_URL}/credentials/primary/info")
    if primary_cred_response.status_code == 200:
        primary_cred_data = primary_cred_response.json()
        print(f"✅ Primary credential: {primary_cred_data['credential_name']} (ID: {primary_cred_data['id']})")
        if primary_cred_data['id'] == cred2_id:
            print("✅ Credential primary designation logic working correctly!")
        else:
            print("❌ Credential primary designation logic failed!")
    
    # Cleanup
    print("\n🧹 Cleanup")
    print("-" * 10)
    session.delete(f"{API_URL}/applicants/{applicant1_id}")
    session.delete(f"{API_URL}/applicants/{applicant2_id}")
    session.delete(f"{API_URL}/credentials/{cred1_id}")
    session.delete(f"{API_URL}/credentials/{cred2_id}")
    print("✅ Cleanup completed")

if __name__ == "__main__":
    test_primary_designation_logic()