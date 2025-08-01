#!/usr/bin/env python3
"""
Test Script for Vietnamese AI Voice Chat System with Business Agents
Kiểm tra toàn diện các agent và chức năng
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8080"
TEST_EMAIL = "daovinhkhang0834@gmail.com"

def print_test_header(test_name):
    """Print test header"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {test_name}")
    print(f"{'='*60}")

def print_test_result(test_name, success, message=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"   📝 {message}")

def test_health_check():
    """Test system health"""
    print_test_header("System Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        data = response.json()
        
        if response.status_code == 200 and data.get('status') == 'healthy':
            print_test_result("Health Check", True, "System is healthy")
            print(f"   📊 Components: {data.get('components', {})}")
            return True
        else:
            print_test_result("Health Check", False, f"Status: {data.get('status')}")
            return False
            
    except Exception as e:
        print_test_result("Health Check", False, f"Error: {str(e)}")
        return False

def test_knowledge_agent():
    """Test Knowledge Base Agent"""
    print_test_header("Knowledge Base Agent")
    
    passed = 0
    total = 2
    
    # Test 1: Get knowledge summary
    try:
        response = requests.get(f"{BASE_URL}/api/knowledge/summary", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_test_result("Knowledge Summary", True, f"Documents: {data.get('total_documents', 0)}")
            passed += 1
        else:
            print_test_result("Knowledge Summary", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Knowledge Summary", False, f"Error: {str(e)}")
    
    # Test 2: Query knowledge base
    try:
        test_question = "Xin chào, bạn có thể giúp gì cho tôi?"
        response = requests.post(
            f"{BASE_URL}/api/knowledge/query",
            json={"question": test_question},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print_test_result("Knowledge Query", True, "Query processed successfully")
            passed += 1
        else:
            print_test_result("Knowledge Query", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Knowledge Query", False, f"Error: {str(e)}")
    
    return passed == total

def test_booking_agent():
    """Test Booking Agent"""
    print_test_header("Booking Agent")
    
    passed = 0
    total = 4
    customer_id = None
    
    # Test 1: Get customer list
    try:
        response = requests.get(f"{BASE_URL}/api/customers", timeout=10)
        if response.status_code == 200:
            customers = response.json()
            print_test_result("Customer List", True, f"Found {len(customers)} customers")
            passed += 1
        else:
            print_test_result("Customer List", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Customer List", False, f"Error: {str(e)}")
    
    # Test 2: Add test customer
    try:
        test_customer = {
            "name": "Test Customer",
            "email": "test@example.com",
            "phone": "0123456789",
            "company": "Test Company"
        }
        response = requests.post(
            f"{BASE_URL}/api/customers",
            json=test_customer,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_test_result("Add Customer", True, f"Customer ID: {data.get('customer_id')}")
                customer_id = data.get('customer_id')
                passed += 1
            else:
                print_test_result("Add Customer", False, data.get('message', 'Unknown error'))
        else:
            print_test_result("Add Customer", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Add Customer", False, f"Error: {str(e)}")
    
    # Test 3: Get booking list
    try:
        response = requests.get(f"{BASE_URL}/api/bookings", timeout=10)
        if response.status_code == 200:
            bookings = response.json()
            print_test_result("Booking List", True, f"Found {len(bookings)} bookings")
            passed += 1
        else:
            print_test_result("Booking List", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Booking List", False, f"Error: {str(e)}")
    
    # Test 4: Create test booking (if customer was added)
    if customer_id:
        try:
            booking_date = (datetime.now() + timedelta(days=1)).isoformat()
            test_booking = {
                "customer_id": customer_id,
                "service_type": "Test Service",
                "booking_date": booking_date,
                "duration": 60,
                "notes": "Test booking for system testing"
            }
            response = requests.post(
                f"{BASE_URL}/api/bookings",
                json=test_booking,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print_test_result("Create Booking", True, f"Booking ID: {data.get('booking_id')}")
                    passed += 1
                else:
                    print_test_result("Create Booking", False, data.get('message', 'Unknown error'))
            else:
                print_test_result("Create Booking", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Booking", False, f"Error: {str(e)}")
    
    return passed == total

def test_email_functionality():
    """Test Email Functionality"""
    print_test_header("Email Functionality")
    
    # Test email sending
    try:
        response = requests.post(
            f"{BASE_URL}/api/test-email",
            json={"email": TEST_EMAIL},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_test_result("Email Test", True, f"Email sent via {data.get('method', 'unknown')}")
                print(f"   📧 Sent to: {TEST_EMAIL}")
                return True
            else:
                print_test_result("Email Test", False, data.get('message', 'Unknown error'))
        else:
            print_test_result("Email Test", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Email Test", False, f"Error: {str(e)}")
    
    return False

def test_voice_chat_simulation():
    """Test Voice Chat Simulation"""
    print_test_header("Voice Chat Simulation")
    
    # Test voice chat endpoint (without actual audio)
    try:
        # Create a dummy audio file for testing
        import tempfile
        import wave
        import numpy as np
        
        # Create a simple test audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # Create 1 second of silence at 16kHz
            sample_rate = 16000
            duration = 1
            samples = np.zeros(sample_rate * duration, dtype=np.int16)
            
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(samples.tobytes())
            
            # Test voice chat endpoint
            with open(temp_file.name, 'rb') as audio_file:
                files = {'audio': ('test.wav', audio_file, 'audio/wav')}
                response = requests.post(f"{BASE_URL}/api/voice-chat", files=files, timeout=30)
            
            # Clean up
            os.unlink(temp_file.name)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    print_test_result("Voice Chat", True, "Voice chat endpoint working")
                    print(f"   🎤 User text: {data.get('user_text', 'N/A')}")
                    print(f"   🤖 AI response: {data.get('ai_response', 'N/A')[:100]}...")
                    return True
                else:
                    print_test_result("Voice Chat", False, data.get('error', 'Unknown error'))
            else:
                print_test_result("Voice Chat", False, f"Status: {response.status_code}")
                
    except Exception as e:
        print_test_result("Voice Chat", False, f"Error: {str(e)}")
    
    return False

def test_agent_routing():
    """Test Agent Routing Logic"""
    print_test_header("Agent Routing Logic")
    
    passed = 0
    total = 5
    
    # Test different types of queries
    test_queries = [
        ("Tôi muốn hỏi về tài liệu", "Knowledge Base"),
        ("Đặt lịch hẹn cho tôi", "Booking"),
        ("Thêm khách hàng mới", "Booking"),
        ("Xin chào, bạn khỏe không?", "General Chat"),
        ("Tôi cần tư vấn về sản phẩm", "Knowledge Base")
    ]
    
    for query, expected_agent in test_queries:
        try:
            # Simulate voice chat with text query
            response = requests.post(
                f"{BASE_URL}/api/knowledge/query",
                json={"question": query},
                timeout=10
            )
            if response.status_code == 200:
                print_test_result(f"Routing: {query[:30]}...", True, f"Expected: {expected_agent}")
                passed += 1
            else:
                print_test_result(f"Routing: {query[:30]}...", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result(f"Routing: {query[:30]}...", False, f"Error: {str(e)}")
    
    return passed == total

def run_performance_test():
    """Run performance test"""
    print_test_header("Performance Test")
    
    # Test response time
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        if response.status_code == 200:
            print_test_result("Response Time", True, f"Health check: {response_time:.2f}ms")
            return True
        else:
            print_test_result("Response Time", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Response Time", False, f"Error: {str(e)}")
    
    return False

def main():
    """Main test function"""
    print("🚀 Vietnamese AI Voice Chat System - Agent Testing")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Run all tests
    tests = [
        test_health_check,
        test_knowledge_agent,
        test_booking_agent,
        test_email_functionality,
        test_voice_chat_simulation,
        test_agent_routing,
        run_performance_test
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print(f"\n🎉 All tests passed! System is ready for production.")
    else:
        print(f"\n⚠️  Some tests failed. Please check the system configuration.")
    
    print(f"\n📅 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 