import requests
import unittest
import sys
import time
import json
from datetime import datetime

class TrolixVEAPITester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TrolixVEAPITester, self).__init__(*args, **kwargs)
        # Use the public endpoint from frontend/.env
        self.base_url = "https://a8a867d5-2481-4c3b-994e-28d1139c90e5.preview.emergentagent.com"
        self.sandbox_id = None
        self.test_sandbox_name = f"Test-Sandbox-{datetime.now().strftime('%H%M%S')}"

    def test_01_health_check(self):
        """Test the health check endpoint"""
        print("\n🔍 Testing health check endpoint...")
        response = requests.get(f"{self.base_url}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["service"], "TrolixVE")
        print("✅ Health check passed")

    def test_02_get_os_templates(self):
        """Test getting OS templates"""
        print("\n🔍 Testing OS templates endpoint...")
        response = requests.get(f"{self.base_url}/api/os-templates")
        self.assertEqual(response.status_code, 200)
        templates = response.json()
        self.assertIsInstance(templates, dict)
        self.assertIn("kali", templates)
        self.assertIn("ubuntu", templates)
        self.assertIn("windows", templates)
        print(f"✅ OS templates endpoint passed - Found {len(templates)} templates")

    def test_03_get_sandboxes(self):
        """Test getting list of sandboxes"""
        print("\n🔍 Testing get sandboxes endpoint...")
        response = requests.get(f"{self.base_url}/api/sandboxes")
        self.assertEqual(response.status_code, 200)
        sandboxes = response.json()
        self.assertIsInstance(sandboxes, list)
        print(f"✅ Get sandboxes endpoint passed - Found {len(sandboxes)} sandboxes")

    def test_04_create_sandbox(self):
        """Test creating a new sandbox"""
        print(f"\n🔍 Testing create sandbox endpoint with name: {self.test_sandbox_name}...")
        config = {
            "name": self.test_sandbox_name,
            "os_type": "kali",
            "cpu_cores": 2,
            "ram_gb": 4,
            "disk_gb": 20,
            "network_isolated": True
        }
        response = requests.post(
            f"{self.base_url}/api/sandboxes",
            json=config
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sandbox_id", data)
        self.assertIn("message", data)
        self.sandbox_id = data["sandbox_id"]
        print(f"✅ Create sandbox endpoint passed - Created sandbox with ID: {data['sandbox_id']}")
        
        # Wait for sandbox to be fully created
        time.sleep(3)

    def test_05_verify_sandbox_created(self):
        """Verify the sandbox was created successfully"""
        print("\n🔍 Verifying sandbox was created...")
        response = requests.get(f"{self.base_url}/api/sandboxes")
        self.assertEqual(response.status_code, 200)
        sandboxes = response.json()
        
        found = False
        for sandbox in sandboxes:
            if sandbox["name"] == self.test_sandbox_name:
                found = True
                self.assertEqual(sandbox["os_type"], "kali")
                self.assertEqual(sandbox["cpu_cores"], 2)
                self.assertEqual(sandbox["ram_gb"], 4)
                self.assertEqual(sandbox["disk_gb"], 20)
                self.assertEqual(sandbox["network_isolated"], True)
                break
                
        self.assertTrue(found, "Created sandbox not found in the list")
        print("✅ Sandbox creation verified")

    def test_06_stop_sandbox(self):
        """Test stopping a sandbox"""
        if not hasattr(self, 'sandbox_id') or not self.sandbox_id:
            self.skipTest("No sandbox ID available")
            
        print(f"\n🔍 Testing stop sandbox endpoint for ID: {self.sandbox_id}...")
        response = requests.post(
            f"{self.base_url}/api/sandboxes/{self.sandbox_id}/stop"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Sandbox stopped")
        print("✅ Stop sandbox endpoint passed")
        
        # Verify sandbox status
        response = requests.get(f"{self.base_url}/api/sandboxes")
        sandboxes = response.json()
        for sandbox in sandboxes:
            if sandbox["id"] == self.sandbox_id:
                self.assertEqual(sandbox["status"], "stopped")
                break

    def test_07_start_sandbox(self):
        """Test starting a sandbox"""
        if not hasattr(self, 'sandbox_id') or not self.sandbox_id:
            self.skipTest("No sandbox ID available")
            
        print(f"\n🔍 Testing start sandbox endpoint for ID: {self.sandbox_id}...")
        response = requests.post(
            f"{self.base_url}/api/sandboxes/{self.sandbox_id}/start"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Sandbox started")
        print("✅ Start sandbox endpoint passed")
        
        # Verify sandbox status
        response = requests.get(f"{self.base_url}/api/sandboxes")
        sandboxes = response.json()
        for sandbox in sandboxes:
            if sandbox["id"] == self.sandbox_id:
                self.assertEqual(sandbox["status"], "running")
                break

    def test_08_save_sandbox(self):
        """Test saving a sandbox"""
        if not TrolixVEAPITester.sandbox_id:
            self.skipTest("No sandbox ID available")
            
        print(f"\n🔍 Testing save sandbox endpoint for ID: {TrolixVEAPITester.sandbox_id}...")
        response = requests.post(
            f"{self.base_url}/api/sandboxes/{TrolixVEAPITester.sandbox_id}/save"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Sandbox saved successfully")
        print("✅ Save sandbox endpoint passed")
        
        # Verify sandbox status
        response = requests.get(f"{self.base_url}/api/sandboxes")
        sandboxes = response.json()
        for sandbox in sandboxes:
            if sandbox["id"] == TrolixVEAPITester.sandbox_id:
                self.assertEqual(sandbox["status"], "saved")
                break

    def test_09_execute_terminal_command(self):
        """Test executing a terminal command"""
        if not TrolixVEAPITester.sandbox_id:
            self.skipTest("No sandbox ID available")
            
        print(f"\n🔍 Testing terminal command execution for sandbox ID: {TrolixVEAPITester.sandbox_id}...")
        
        # Start the sandbox first to ensure it's running
        requests.post(f"{self.base_url}/api/sandboxes/{TrolixVEAPITester.sandbox_id}/start")
        
        # Test basic command
        command_data = {
            "sandbox_id": TrolixVEAPITester.sandbox_id,
            "command": "ls"
        }
        response = requests.post(
            f"{self.base_url}/api/terminal/execute",
            json=command_data
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["command"], "ls")
        self.assertIn("bin", result["output"])
        print("✅ Basic terminal command execution passed")
        
        # Test cybersecurity command
        command_data = {
            "sandbox_id": TrolixVEAPITester.sandbox_id,
            "command": "nmap"
        }
        response = requests.post(
            f"{self.base_url}/api/terminal/execute",
            json=command_data
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["command"], "nmap")
        self.assertIn("Starting Nmap scan", result["output"])
        print("✅ Cybersecurity terminal command execution passed")

    def test_10_get_terminal_history(self):
        """Test getting terminal command history"""
        if not TrolixVEAPITester.sandbox_id:
            self.skipTest("No sandbox ID available")
            
        print(f"\n🔍 Testing terminal history endpoint for sandbox ID: {TrolixVEAPITester.sandbox_id}...")
        response = requests.get(
            f"{self.base_url}/api/terminal/{TrolixVEAPITester.sandbox_id}/history"
        )
        self.assertEqual(response.status_code, 200)
        history = response.json()
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 2)  # We executed at least 2 commands
        
        # Verify history entries
        for entry in history:
            self.assertIn("command", entry)
            self.assertIn("output", entry)
            self.assertIn("timestamp", entry)
            self.assertEqual(entry["sandbox_id"], TrolixVEAPITester.sandbox_id)
            
        print(f"✅ Terminal history endpoint passed - Found {len(history)} history entries")

    def test_11_delete_sandbox(self):
        """Test deleting a sandbox"""
        if not TrolixVEAPITester.sandbox_id:
            self.skipTest("No sandbox ID available")
            
        print(f"\n🔍 Testing delete sandbox endpoint for ID: {TrolixVEAPITester.sandbox_id}...")
        response = requests.delete(
            f"{self.base_url}/api/sandboxes/{TrolixVEAPITester.sandbox_id}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Sandbox deleted")
        print("✅ Delete sandbox endpoint passed")
        
        # Verify sandbox was deleted
        response = requests.get(f"{self.base_url}/api/sandboxes")
        sandboxes = response.json()
        for sandbox in sandboxes:
            self.assertNotEqual(sandbox["id"], TrolixVEAPITester.sandbox_id)

    def test_12_error_handling(self):
        """Test error handling for non-existent sandbox"""
        print("\n🔍 Testing error handling for non-existent sandbox...")
        fake_id = "nonexistent-id-12345"
        
        # Test start endpoint
        response = requests.post(f"{self.base_url}/api/sandboxes/{fake_id}/start")
        self.assertEqual(response.status_code, 404)
        
        # Test stop endpoint
        response = requests.post(f"{self.base_url}/api/sandboxes/{fake_id}/stop")
        self.assertEqual(response.status_code, 404)
        
        # Test save endpoint
        response = requests.post(f"{self.base_url}/api/sandboxes/{fake_id}/save")
        self.assertEqual(response.status_code, 404)
        
        # Test delete endpoint
        response = requests.delete(f"{self.base_url}/api/sandboxes/{fake_id}")
        self.assertEqual(response.status_code, 404)
        
        print("✅ Error handling tests passed")

if __name__ == "__main__":
    # Run the tests in order
    test_suite = unittest.TestSuite()
    test_suite.addTest(TrolixVEAPITester('test_01_health_check'))
    test_suite.addTest(TrolixVEAPITester('test_02_get_os_templates'))
    test_suite.addTest(TrolixVEAPITester('test_03_get_sandboxes'))
    test_suite.addTest(TrolixVEAPITester('test_04_create_sandbox'))
    test_suite.addTest(TrolixVEAPITester('test_05_verify_sandbox_created'))
    test_suite.addTest(TrolixVEAPITester('test_06_stop_sandbox'))
    test_suite.addTest(TrolixVEAPITester('test_07_start_sandbox'))
    test_suite.addTest(TrolixVEAPITester('test_08_save_sandbox'))
    test_suite.addTest(TrolixVEAPITester('test_09_execute_terminal_command'))
    test_suite.addTest(TrolixVEAPITester('test_10_get_terminal_history'))
    test_suite.addTest(TrolixVEAPITester('test_11_delete_sandbox'))
    test_suite.addTest(TrolixVEAPITester('test_12_error_handling'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n📊 Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)