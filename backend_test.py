#!/usr/bin/env python3
"""
BLS-SPANISH Backend API Testing Suite
Tests the newly implemented visa types selection API and other core functionality
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, Any

# Get backend URL - use localhost:8001 as specified in review request due to external URL mapping issues
def get_backend_url():
    # As per review request: "External URL mapping has issues (404s), so use localhost:8001 for testing"
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

class BLSBackendTester:
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    def test_root_endpoint(self):
        """Test GET /api/ endpoint"""
        try:
            response = self.session.get(f"{API_URL}/")
            
            if response.status_code == 200:
                data = response.json()
                if "BLS2" in data.get("message", "") and "version" in data:
                    self.log_test("Root Endpoint", True, f"Version: {data.get('version')}", data)
                else:
                    self.log_test("Root Endpoint", False, "Invalid response format", data)
            else:
                self.log_test("Root Endpoint", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Exception: {str(e)}")

    def test_visa_types_endpoint(self):
        """Test GET /api/visa-types endpoint - NEW FEATURE"""
        try:
            response = self.session.get(f"{API_URL}/visa-types")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                if "visa_types" not in data or "appointment_types" not in data:
                    self.log_test("Visa Types Endpoint", False, "Missing required fields", data)
                    return
                
                visa_types = data["visa_types"]
                appointment_types = data["appointment_types"]
                
                # Validate visa types structure
                expected_visa_types = ["Tourist Visa", "Business Visa", "Student Visa", "Work Visa", "Family Reunion Visa"]
                expected_appointment_types = ["Individual", "Family"]
                
                missing_visa_types = [vt for vt in expected_visa_types if vt not in visa_types]
                missing_appointment_types = [at for at in expected_appointment_types if at not in appointment_types]
                
                if missing_visa_types or missing_appointment_types:
                    details = f"Missing visa types: {missing_visa_types}, Missing appointment types: {missing_appointment_types}"
                    self.log_test("Visa Types Endpoint", False, details, data)
                else:
                    # Check subtypes for each visa type
                    valid_subtypes = True
                    for visa_type, subtypes in visa_types.items():
                        if not isinstance(subtypes, list) or len(subtypes) == 0:
                            valid_subtypes = False
                            break
                    
                    if valid_subtypes:
                        self.log_test("Visa Types Endpoint", True, f"Found {len(visa_types)} visa types with subtypes", data)
                    else:
                        self.log_test("Visa Types Endpoint", False, "Invalid subtypes structure", data)
            else:
                self.log_test("Visa Types Endpoint", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Visa Types Endpoint", False, f"Exception: {str(e)}")

    def test_system_config_endpoint(self):
        """Test GET /api/system/config endpoint - NEW FEATURE"""
        try:
            response = self.session.get(f"{API_URL}/system/config")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required configuration fields
                required_fields = ["status", "check_interval_minutes", "visa_type", "visa_subtype", 
                                 "appointment_type", "number_of_members"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("System Config Endpoint", False, f"Missing fields: {missing_fields}", data)
                else:
                    # Validate field values
                    valid_status = data["status"] in ["stopped", "running", "paused", "error"]
                    valid_interval = isinstance(data["check_interval_minutes"], int) and data["check_interval_minutes"] > 0
                    valid_members = isinstance(data["number_of_members"], int) and data["number_of_members"] > 0
                    
                    if valid_status and valid_interval and valid_members:
                        self.log_test("System Config Endpoint", True, 
                                    f"Status: {data['status']}, Interval: {data['check_interval_minutes']}min, "
                                    f"Visa: {data['visa_type']} ({data['visa_subtype']}), "
                                    f"Type: {data['appointment_type']}, Members: {data['number_of_members']}", data)
                    else:
                        self.log_test("System Config Endpoint", False, "Invalid field values", data)
            else:
                self.log_test("System Config Endpoint", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("System Config Endpoint", False, f"Exception: {str(e)}")

    def test_system_status_endpoint(self):
        """Test GET /api/system/status endpoint"""
        try:
            response = self.session.get(f"{API_URL}/system/status")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["status", "total_checks", "slots_found", "successful_bookings", "error_count"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("System Status Endpoint", False, f"Missing fields: {missing_fields}", data)
                else:
                    self.log_test("System Status Endpoint", True, 
                                f"Status: {data['status']}, Checks: {data['total_checks']}, "
                                f"Slots: {data['slots_found']}, Bookings: {data['successful_bookings']}", data)
            else:
                self.log_test("System Status Endpoint", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("System Status Endpoint", False, f"Exception: {str(e)}")

    def test_system_start_with_visa_config(self):
        """Test POST /api/system/start with new visa configuration parameters - NEW FEATURE"""
        try:
            # Test data as specified in the review request
            test_config = {
                "visa_type": "Business Visa",
                "visa_subtype": "Long Stay", 
                "appointment_type": "Family",
                "number_of_members": 3,
                "check_interval_minutes": 5
            }
            
            response = self.session.post(f"{API_URL}/system/start", json=test_config)
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data and "status" in data:
                    if data["status"] == "running":
                        self.log_test("System Start with Visa Config", True, 
                                    f"System started with config: {test_config}", data)
                        
                        # Wait a moment then verify config was saved
                        time.sleep(2)
                        self.verify_config_saved(test_config)
                    else:
                        self.log_test("System Start with Visa Config", False, 
                                    f"System not running after start: {data['status']}", data)
                else:
                    self.log_test("System Start with Visa Config", False, "Invalid response format", data)
            else:
                self.log_test("System Start with Visa Config", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("System Start with Visa Config", False, f"Exception: {str(e)}")

    def verify_config_saved(self, expected_config: Dict[str, Any]):
        """Verify that the visa configuration was properly saved to database"""
        try:
            response = self.session.get(f"{API_URL}/system/config")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if all expected config values were saved
                config_matches = True
                mismatches = []
                
                for key, expected_value in expected_config.items():
                    if key in data:
                        if data[key] != expected_value:
                            config_matches = False
                            mismatches.append(f"{key}: expected {expected_value}, got {data[key]}")
                    else:
                        config_matches = False
                        mismatches.append(f"{key}: missing from config")
                
                if config_matches:
                    self.log_test("Config Database Persistence", True, 
                                "All visa configuration parameters saved correctly", data)
                else:
                    self.log_test("Config Database Persistence", False, 
                                f"Config mismatches: {mismatches}", data)
            else:
                self.log_test("Config Database Persistence", False, 
                            f"Failed to retrieve config: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Config Database Persistence", False, f"Exception: {str(e)}")

    def test_single_automation_check(self):
        """Test POST /api/test/check-once to verify Playwright browsers are working"""
        try:
            response = self.session.post(f"{API_URL}/test/check-once")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["success", "slots_found", "method"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Single Automation Check", False, f"Missing fields: {missing_fields}", data)
                else:
                    if data.get("method") == "enhanced_automation":
                        self.log_test("Single Automation Check", True, 
                                    f"Playwright browsers working. Success: {data['success']}, "
                                    f"Slots found: {data['slots_found']}", data)
                    else:
                        self.log_test("Single Automation Check", False, 
                                    f"Unexpected method: {data.get('method')}", data)
            else:
                self.log_test("Single Automation Check", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Single Automation Check", False, f"Exception: {str(e)}")

    def test_system_stop(self):
        """Test POST /api/system/stop endpoint"""
        try:
            response = self.session.post(f"{API_URL}/system/stop")
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data and "status" in data:
                    if data["status"] == "stopped":
                        self.log_test("System Stop", True, "System stopped successfully", data)
                    else:
                        self.log_test("System Stop", False, f"System not stopped: {data['status']}", data)
                else:
                    self.log_test("System Stop", False, "Invalid response format", data)
            else:
                self.log_test("System Stop", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("System Stop", False, f"Exception: {str(e)}")

    def test_logs_endpoint(self):
        """Test GET /api/logs endpoint"""
        try:
            response = self.session.get(f"{API_URL}/logs?limit=10")
            
            if response.status_code == 200:
                data = response.json()
                
                if "logs" in data and "total_count" in data:
                    logs = data["logs"]
                    if isinstance(logs, list):
                        self.log_test("Logs Endpoint", True, 
                                    f"Retrieved {len(logs)} logs, Total: {data['total_count']}", 
                                    {"log_count": len(logs), "total_count": data["total_count"]})
                    else:
                        self.log_test("Logs Endpoint", False, "Logs is not a list", data)
                else:
                    self.log_test("Logs Endpoint", False, "Missing required fields", data)
            else:
                self.log_test("Logs Endpoint", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Logs Endpoint", False, f"Exception: {str(e)}")

    def test_appointments_endpoint(self):
        """Test GET /api/appointments/available endpoint"""
        try:
            response = self.session.get(f"{API_URL}/appointments/available?limit=10")
            
            if response.status_code == 200:
                data = response.json()
                
                if "slots" in data and "total_count" in data:
                    slots = data["slots"]
                    if isinstance(slots, list):
                        self.log_test("Appointments Endpoint", True, 
                                    f"Retrieved {len(slots)} slots, Total: {data['total_count']}", 
                                    {"slot_count": len(slots), "total_count": data["total_count"]})
                    else:
                        self.log_test("Appointments Endpoint", False, "Slots is not a list", data)
                else:
                    self.log_test("Appointments Endpoint", False, "Missing required fields", data)
            else:
                self.log_test("Appointments Endpoint", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Appointments Endpoint", False, f"Exception: {str(e)}")

    def test_ocr_endpoint(self):
        """Test POST /api/ocr-match endpoint"""
        try:
            # Test with sample data
            test_data = {
                "target": "5",
                "tiles": [
                    {"base64Image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="},
                    {"base64Image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="}
                ],
                "enhanced_mode": False
            }
            
            response = self.session.post(f"{API_URL}/ocr-match", json=test_data)
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["target", "matching_indices", "processed_tiles", "success"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("OCR Endpoint", False, f"Missing fields: {missing_fields}", data)
                else:
                    if data["success"] and isinstance(data["matching_indices"], list):
                        self.log_test("OCR Endpoint", True, 
                                    f"Processed {data['processed_tiles']} tiles, "
                                    f"Found {len(data['matching_indices'])} matches", data)
                    else:
                        self.log_test("OCR Endpoint", False, "OCR processing failed or invalid format", data)
            else:
                self.log_test("OCR Endpoint", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("OCR Endpoint", False, f"Exception: {str(e)}")

    # =============================================================================
    # APPLICANT MANAGEMENT API TESTS - NEW FEATURES
    # =============================================================================
    
    def test_create_applicant(self):
        """Test POST /api/applicants - create new applicant"""
        try:
            # Test data with realistic information
            test_applicant = {
                "first_name": "Maria",
                "last_name": "Rodriguez",
                "passport_number": "ES123456789",
                "nationality": "Spanish",
                "phone_number": "+34612345678",
                "email": "maria.rodriguez@email.com",
                "date_of_birth": "1990-05-15",
                "gender": "Female",
                "address": "Calle Mayor 123",
                "city": "Madrid",
                "postal_code": "28001",
                "country": "Spain",
                "emergency_contact": "Carlos Rodriguez",
                "emergency_phone": "+34612345679",
                "visa_type_preference": "Tourist Visa",
                "notes": "First time applicant",
                "is_primary": True
            }
            
            response = self.session.post(f"{API_URL}/applicants", json=test_applicant)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify all required fields are present
                required_fields = ["id", "first_name", "last_name", "passport_number", "nationality", 
                                 "phone_number", "email", "is_primary", "created_at", "updated_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Create Applicant", False, f"Missing fields: {missing_fields}", data)
                else:
                    # Verify data integrity
                    if (data["first_name"] == test_applicant["first_name"] and 
                        data["passport_number"] == test_applicant["passport_number"] and
                        data["is_primary"] == test_applicant["is_primary"]):
                        
                        # Store applicant ID for later tests
                        self.test_applicant_id = data["id"]
                        self.log_test("Create Applicant", True, 
                                    f"Created applicant: {data['first_name']} {data['last_name']} "
                                    f"({data['passport_number']}) - Primary: {data['is_primary']}", data)
                    else:
                        self.log_test("Create Applicant", False, "Data integrity check failed", data)
            else:
                self.log_test("Create Applicant", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Create Applicant", False, f"Exception: {str(e)}")

    def test_get_all_applicants(self):
        """Test GET /api/applicants - fetch all applicants"""
        try:
            response = self.session.get(f"{API_URL}/applicants?limit=10")
            
            if response.status_code == 200:
                data = response.json()
                
                if "applicants" in data and "total_count" in data:
                    applicants = data["applicants"]
                    if isinstance(applicants, list):
                        self.log_test("Get All Applicants", True, 
                                    f"Retrieved {len(applicants)} applicants, Total: {data['total_count']}", 
                                    {"applicant_count": len(applicants), "total_count": data["total_count"]})
                    else:
                        self.log_test("Get All Applicants", False, "Applicants is not a list", data)
                else:
                    self.log_test("Get All Applicants", False, "Missing required fields", data)
            else:
                self.log_test("Get All Applicants", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Get All Applicants", False, f"Exception: {str(e)}")

    def test_get_specific_applicant(self):
        """Test GET /api/applicants/{id} - fetch specific applicant"""
        try:
            if not hasattr(self, 'test_applicant_id'):
                self.log_test("Get Specific Applicant", False, "No test applicant ID available")
                return
                
            response = self.session.get(f"{API_URL}/applicants/{self.test_applicant_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["id", "first_name", "last_name", "passport_number"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Get Specific Applicant", False, f"Missing fields: {missing_fields}", data)
                else:
                    if data["id"] == self.test_applicant_id:
                        self.log_test("Get Specific Applicant", True, 
                                    f"Retrieved applicant: {data['first_name']} {data['last_name']}", data)
                    else:
                        self.log_test("Get Specific Applicant", False, "ID mismatch", data)
            else:
                self.log_test("Get Specific Applicant", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Get Specific Applicant", False, f"Exception: {str(e)}")

    def test_update_applicant(self):
        """Test PUT /api/applicants/{id} - update applicant information"""
        try:
            if not hasattr(self, 'test_applicant_id'):
                self.log_test("Update Applicant", False, "No test applicant ID available")
                return
                
            # Update data
            update_data = {
                "phone_number": "+34612345680",
                "city": "Barcelona",
                "notes": "Updated contact information"
            }
            
            response = self.session.put(f"{API_URL}/applicants/{self.test_applicant_id}", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify updates were applied
                if (data["phone_number"] == update_data["phone_number"] and 
                    data["city"] == update_data["city"] and
                    data["notes"] == update_data["notes"]):
                    self.log_test("Update Applicant", True, 
                                f"Updated applicant: {data['first_name']} {data['last_name']} - "
                                f"New phone: {data['phone_number']}, City: {data['city']}", data)
                else:
                    self.log_test("Update Applicant", False, "Update verification failed", data)
            else:
                self.log_test("Update Applicant", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Update Applicant", False, f"Exception: {str(e)}")

    def test_get_primary_applicant(self):
        """Test GET /api/applicants/primary/info - get primary applicant"""
        try:
            response = self.session.get(f"{API_URL}/applicants/primary/info")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["id", "first_name", "last_name", "is_primary"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Get Primary Applicant", False, f"Missing fields: {missing_fields}", data)
                else:
                    if data["is_primary"]:
                        self.log_test("Get Primary Applicant", True, 
                                    f"Primary applicant: {data['first_name']} {data['last_name']}", data)
                    else:
                        self.log_test("Get Primary Applicant", False, "Returned applicant is not primary", data)
            elif response.status_code == 404:
                self.log_test("Get Primary Applicant", True, "No primary applicant found (expected)", None)
            else:
                self.log_test("Get Primary Applicant", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Get Primary Applicant", False, f"Exception: {str(e)}")

    # =============================================================================
    # LOGIN CREDENTIALS MANAGEMENT API TESTS - NEW FEATURES
    # =============================================================================
    
    def test_create_credential(self):
        """Test POST /api/credentials - create new login credential"""
        try:
            # Test data with realistic information
            test_credential = {
                "credential_name": "Primary BLS Account",
                "email": "maria.rodriguez@email.com",
                "password": "SecurePassword123!",
                "is_primary": True,
                "notes": "Main account for automation"
            }
            
            response = self.session.post(f"{API_URL}/credentials", json=test_credential)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify all required fields are present
                required_fields = ["id", "credential_name", "email", "is_active", "is_primary", 
                                 "success_rate", "total_attempts", "successful_attempts", "created_at", "updated_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Create Credential", False, f"Missing fields: {missing_fields}", data)
                else:
                    # Verify data integrity
                    if (data["credential_name"] == test_credential["credential_name"] and 
                        data["email"] == test_credential["email"] and
                        data["is_primary"] == test_credential["is_primary"]):
                        
                        # Store credential ID for later tests
                        self.test_credential_id = data["id"]
                        self.log_test("Create Credential", True, 
                                    f"Created credential: {data['credential_name']} ({data['email']}) - "
                                    f"Primary: {data['is_primary']}, Active: {data['is_active']}", data)
                    else:
                        self.log_test("Create Credential", False, "Data integrity check failed", data)
            else:
                self.log_test("Create Credential", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Create Credential", False, f"Exception: {str(e)}")

    def test_get_all_credentials(self):
        """Test GET /api/credentials - fetch all credentials"""
        try:
            response = self.session.get(f"{API_URL}/credentials?limit=10")
            
            if response.status_code == 200:
                data = response.json()
                
                if "credentials" in data and "total_count" in data:
                    credentials = data["credentials"]
                    if isinstance(credentials, list):
                        self.log_test("Get All Credentials", True, 
                                    f"Retrieved {len(credentials)} credentials, Total: {data['total_count']}", 
                                    {"credential_count": len(credentials), "total_count": data["total_count"]})
                    else:
                        self.log_test("Get All Credentials", False, "Credentials is not a list", data)
                else:
                    self.log_test("Get All Credentials", False, "Missing required fields", data)
            else:
                self.log_test("Get All Credentials", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Get All Credentials", False, f"Exception: {str(e)}")

    def test_get_specific_credential(self):
        """Test GET /api/credentials/{id} - fetch specific credential"""
        try:
            if not hasattr(self, 'test_credential_id'):
                self.log_test("Get Specific Credential", False, "No test credential ID available")
                return
                
            response = self.session.get(f"{API_URL}/credentials/{self.test_credential_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["id", "credential_name", "email", "is_active", "is_primary"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Get Specific Credential", False, f"Missing fields: {missing_fields}", data)
                else:
                    if data["id"] == self.test_credential_id:
                        self.log_test("Get Specific Credential", True, 
                                    f"Retrieved credential: {data['credential_name']} ({data['email']})", data)
                    else:
                        self.log_test("Get Specific Credential", False, "ID mismatch", data)
            else:
                self.log_test("Get Specific Credential", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Get Specific Credential", False, f"Exception: {str(e)}")

    def test_update_credential(self):
        """Test PUT /api/credentials/{id} - update credential information"""
        try:
            if not hasattr(self, 'test_credential_id'):
                self.log_test("Update Credential", False, "No test credential ID available")
                return
                
            # Update data
            update_data = {
                "credential_name": "Updated Primary BLS Account",
                "notes": "Updated account information"
            }
            
            response = self.session.put(f"{API_URL}/credentials/{self.test_credential_id}", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify updates were applied
                if (data["credential_name"] == update_data["credential_name"] and 
                    data["notes"] == update_data["notes"]):
                    self.log_test("Update Credential", True, 
                                f"Updated credential: {data['credential_name']} ({data['email']})", data)
                else:
                    self.log_test("Update Credential", False, "Update verification failed", data)
            else:
                self.log_test("Update Credential", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Update Credential", False, f"Exception: {str(e)}")

    def test_get_primary_credential(self):
        """Test GET /api/credentials/primary/info - get primary credential"""
        try:
            response = self.session.get(f"{API_URL}/credentials/primary/info")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["id", "credential_name", "email", "is_primary", "is_active"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Get Primary Credential", False, f"Missing fields: {missing_fields}", data)
                else:
                    if data["is_primary"] and data["is_active"]:
                        self.log_test("Get Primary Credential", True, 
                                    f"Primary credential: {data['credential_name']} ({data['email']})", data)
                    else:
                        self.log_test("Get Primary Credential", False, 
                                    f"Credential not primary/active: Primary={data['is_primary']}, Active={data['is_active']}", data)
            elif response.status_code == 404:
                self.log_test("Get Primary Credential", True, "No primary credential found (expected)", None)
            else:
                self.log_test("Get Primary Credential", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Get Primary Credential", False, f"Exception: {str(e)}")

    def test_set_primary_credential(self):
        """Test POST /api/credentials/{id}/set-primary - set credential as primary"""
        try:
            if not hasattr(self, 'test_credential_id'):
                self.log_test("Set Primary Credential", False, "No test credential ID available")
                return
                
            response = self.session.post(f"{API_URL}/credentials/{self.test_credential_id}/set-primary")
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data and "successfully" in data["message"].lower():
                    self.log_test("Set Primary Credential", True, data["message"], data)
                    
                    # Verify by getting the credential
                    verify_response = self.session.get(f"{API_URL}/credentials/{self.test_credential_id}")
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        if verify_data.get("is_primary"):
                            self.log_test("Verify Primary Credential Set", True, 
                                        f"Credential is now primary: {verify_data['credential_name']}", verify_data)
                        else:
                            self.log_test("Verify Primary Credential Set", False, "Credential is not primary", verify_data)
                else:
                    self.log_test("Set Primary Credential", False, "Invalid response format", data)
            else:
                self.log_test("Set Primary Credential", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Set Primary Credential", False, f"Exception: {str(e)}")

    def test_credential_functionality(self):
        """Test POST /api/credentials/{id}/test - test credential functionality"""
        try:
            if not hasattr(self, 'test_credential_id'):
                self.log_test("Test Credential Functionality", False, "No test credential ID available")
                return
                
            response = self.session.post(f"{API_URL}/credentials/{self.test_credential_id}/test")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["success", "message", "response_time_ms"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Test Credential Functionality", False, f"Missing fields: {missing_fields}", data)
                else:
                    if isinstance(data["response_time_ms"], int) and data["response_time_ms"] >= 0:
                        self.log_test("Test Credential Functionality", True, 
                                    f"Credential test completed: Success={data['success']}, "
                                    f"Response time: {data['response_time_ms']}ms", data)
                    else:
                        self.log_test("Test Credential Functionality", False, "Invalid response time", data)
            else:
                self.log_test("Test Credential Functionality", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Test Credential Functionality", False, f"Exception: {str(e)}")

    def test_delete_applicant(self):
        """Test DELETE /api/applicants/{id} - delete applicant (cleanup)"""
        try:
            if not hasattr(self, 'test_applicant_id'):
                self.log_test("Delete Applicant", False, "No test applicant ID available")
                return
                
            response = self.session.delete(f"{API_URL}/applicants/{self.test_applicant_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data and "successfully" in data["message"].lower():
                    self.log_test("Delete Applicant", True, data["message"], data)
                    
                    # Verify deletion by trying to get the applicant
                    verify_response = self.session.get(f"{API_URL}/applicants/{self.test_applicant_id}")
                    if verify_response.status_code == 404:
                        self.log_test("Verify Applicant Deletion", True, "Applicant successfully deleted", None)
                    else:
                        self.log_test("Verify Applicant Deletion", False, "Applicant still exists", None)
                else:
                    self.log_test("Delete Applicant", False, "Invalid response format", data)
            else:
                self.log_test("Delete Applicant", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Delete Applicant", False, f"Exception: {str(e)}")

    def test_delete_credential(self):
        """Test DELETE /api/credentials/{id} - delete credential (cleanup)"""
        try:
            if not hasattr(self, 'test_credential_id'):
                self.log_test("Delete Credential", False, "No test credential ID available")
                return
                
            response = self.session.delete(f"{API_URL}/credentials/{self.test_credential_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data and "successfully" in data["message"].lower():
                    self.log_test("Delete Credential", True, data["message"], data)
                    
                    # Verify deletion by trying to get the credential
                    verify_response = self.session.get(f"{API_URL}/credentials/{self.test_credential_id}")
                    if verify_response.status_code == 404:
                        self.log_test("Verify Credential Deletion", True, "Credential successfully deleted", None)
                    else:
                        self.log_test("Verify Credential Deletion", False, "Credential still exists", None)
                else:
                    self.log_test("Delete Credential", False, "Invalid response format", data)
            else:
                self.log_test("Delete Credential", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Delete Credential", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests including NEW applicant and credential management APIs"""
        print(f"🚀 Starting BLS-SPANISH Backend API Comprehensive Tests")
        print(f"Backend URL: {BASE_URL}")
        print(f"API URL: {API_URL}")
        print("=" * 80)
        
        # Test core existing endpoints
        print("📋 TESTING CORE EXISTING APIs")
        print("-" * 40)
        self.test_root_endpoint()
        self.test_system_status_endpoint()
        self.test_visa_types_endpoint()
        self.test_logs_endpoint()
        self.test_appointments_endpoint()
        self.test_ocr_endpoint()
        
        # Test system start/stop with visa configuration
        print("\n🔧 TESTING SYSTEM CONTROL APIs")
        print("-" * 40)
        self.test_system_config_endpoint()
        self.test_system_start_with_visa_config()
        self.test_single_automation_check()
        self.test_system_stop()
        
        # Test NEW applicant management APIs (main focus)
        print("\n👥 TESTING NEW APPLICANT MANAGEMENT APIs")
        print("-" * 40)
        self.test_create_applicant()
        self.test_get_all_applicants()
        self.test_get_specific_applicant()
        self.test_update_applicant()
        self.test_get_primary_applicant()
        
        # Test NEW login credentials management APIs (main focus)
        print("\n🔐 TESTING NEW LOGIN CREDENTIALS MANAGEMENT APIs")
        print("-" * 40)
        self.test_create_credential()
        self.test_get_all_credentials()
        self.test_get_specific_credential()
        self.test_update_credential()
        self.test_get_primary_credential()
        self.test_set_primary_credential()
        self.test_credential_functionality()
        
        # Cleanup tests
        print("\n🧹 CLEANUP TESTS")
        print("-" * 40)
        self.test_delete_applicant()
        self.test_delete_credential()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("🏁 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    tester = BLSBackendTester()
    tester.run_all_tests()