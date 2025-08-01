#!/usr/bin/env python3
"""
Demo Script for Vietnamese AI Voice Chat System with Business Agents
Demo các tính năng chính của hệ thống
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8080"

def print_demo_header(title):
    """Print demo header"""
    print(f"\n{'='*60}")
    print(f"🎬 DEMO: {title}")
    print(f"{'='*60}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def demo_system_overview():
    """Demo system overview"""
    print_demo_header("System Overview")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success("System is healthy and ready!")
            print_info(f"Components: {', '.join(data.get('components', {}).keys())}")
            print_info(f"Message: {data.get('message', 'N/A')}")
        else:
            print_error(f"System health check failed: HTTP {response.status_code}")
    except Exception as e:
        print_error(f"System health check error: {str(e)}")

def demo_knowledge_agent():
    """Demo Knowledge Base Agent"""
    print_demo_header("Knowledge Base Agent")
    
    # Test knowledge summary
    try:
        response = requests.get(f"{BASE_URL}/api/knowledge/summary", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_info(f"Current documents: {data.get('total_documents', 0)}")
        else:
            print_error(f"Failed to get knowledge summary: HTTP {response.status_code}")
    except Exception as e:
        print_error(f"Knowledge summary error: {str(e)}")
    
    # Test knowledge query
    test_questions = [
        "Xin chào, bạn có thể giúp gì cho tôi?",
        "Tôi muốn tìm hiểu về sản phẩm của công ty",
        "Có thể cho tôi biết về chính sách khách hàng không?"
    ]
    
    for question in test_questions:
        try:
            print_info(f"Question: {question}")
            response = requests.post(
                f"{BASE_URL}/api/knowledge/query",
                json={"question": question},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', 'No answer received')
                print_success(f"Answer: {answer[:100]}...")
            else:
                print_error(f"Query failed: HTTP {response.status_code}")
        except Exception as e:
            print_error(f"Query error: {str(e)}")
        time.sleep(1)

def demo_booking_agent():
    """Demo Booking Agent"""
    print_demo_header("Booking Agent")
    
    # Get current customers and bookings
    try:
        response = requests.get(f"{BASE_URL}/api/customers", timeout=10)
        if response.status_code == 200:
            customers = response.json()
            print_info(f"Current customers: {len(customers)}")
        else:
            print_error(f"Failed to get customers: HTTP {response.status_code}")
    except Exception as e:
        print_error(f"Customers error: {str(e)}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/bookings", timeout=10)
        if response.status_code == 200:
            bookings = response.json()
            print_info(f"Current bookings: {len(bookings)}")
        else:
            print_error(f"Failed to get bookings: HTTP {response.status_code}")
    except Exception as e:
        print_error(f"Bookings error: {str(e)}")
    
    # Add a demo customer
    demo_customer = {
        "name": "Demo Customer",
        "email": f"demo{int(time.time())}@example.com",
        "phone": "0987654321",
        "company": "Demo Company"
    }
    
    try:
        print_info("Adding demo customer...")
        response = requests.post(
            f"{BASE_URL}/api/customers",
            json=demo_customer,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                customer_id = data.get('customer_id')
                print_success(f"Customer added with ID: {customer_id}")
                
                # Create a demo booking
                demo_booking = {
                    "customer_id": customer_id,
                    "service_type": "Demo Consultation",
                    "booking_date": (datetime.now() + timedelta(days=2)).isoformat(),
                    "duration": 90,
                    "notes": "Demo booking for system testing"
                }
                
                print_info("Creating demo booking...")
                response2 = requests.post(
                    f"{BASE_URL}/api/bookings",
                    json=demo_booking,
                    timeout=10
                )
                if response2.status_code == 200:
                    data2 = response2.json()
                    if data2.get('success'):
                        booking_id = data2.get('booking_id')
                        print_success(f"Booking created with ID: {booking_id}")
                    else:
                        print_error(f"Booking creation failed: {data2.get('message')}")
                else:
                    print_error(f"Booking creation failed: HTTP {response2.status_code}")
            else:
                print_error(f"Customer creation failed: {data.get('message')}")
        else:
            print_error(f"Customer creation failed: HTTP {response.status_code}")
    except Exception as e:
        print_error(f"Customer/Booking creation error: {str(e)}")

def demo_email_functionality():
    """Demo Email Functionality"""
    print_demo_header("Email Functionality")
    
    try:
        print_info("Testing email functionality...")
        response = requests.post(
            f"{BASE_URL}/api/test-email",
            json={"email": "daovinhkhang0834@gmail.com"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success(f"Email test successful via {data.get('method', 'unknown')}")
                print_info("Check your email for the test message")
            else:
                print_error(f"Email test failed: {data.get('message')}")
        else:
            print_error(f"Email test failed: HTTP {response.status_code}")
    except Exception as e:
        print_error(f"Email test error: {str(e)}")

def demo_voice_chat_simulation():
    """Demo Voice Chat Simulation"""
    print_demo_header("Voice Chat Simulation")
    
    try:
        print_info("Simulating voice chat with dummy audio...")
        
        # Create a simple test audio file
        import tempfile
        import wave
        import numpy as np
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # Create 2 seconds of silence at 16kHz
            sample_rate = 16000
            duration = 2
            samples = np.zeros(sample_rate * duration, dtype=np.int16)
            
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(samples.tobytes())
            
            # Test voice chat endpoint
            with open(temp_file.name, 'rb') as audio_file:
                files = {'audio': ('demo.wav', audio_file, 'audio/wav')}
                response = requests.post(f"{BASE_URL}/api/voice-chat", files=files, timeout=30)
            
            # Clean up
            import os
            os.unlink(temp_file.name)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    print_success("Voice chat simulation successful!")
                    print_info(f"User text: {data.get('user_text', 'N/A')}")
                    print_info(f"AI response: {data.get('ai_response', 'N/A')[:150]}...")
                else:
                    print_error(f"Voice chat failed: {data.get('error', 'Unknown error')}")
            else:
                print_error(f"Voice chat failed: HTTP {response.status_code}")
                
    except Exception as e:
        print_error(f"Voice chat simulation error: {str(e)}")

def demo_agent_routing():
    """Demo Agent Routing"""
    print_demo_header("Agent Routing Logic")
    
    test_scenarios = [
        ("Tôi muốn hỏi về tài liệu sản phẩm", "Knowledge Base"),
        ("Đặt lịch hẹn tư vấn cho tôi", "Booking"),
        ("Thêm thông tin khách hàng mới", "Booking"),
        ("Xin chào, bạn khỏe không?", "General Chat"),
        ("Tôi cần tư vấn về dịch vụ", "Knowledge Base")
    ]
    
    for query, expected_agent in test_scenarios:
        try:
            print_info(f"Query: {query}")
            print_info(f"Expected Agent: {expected_agent}")
            
            response = requests.post(
                f"{BASE_URL}/api/knowledge/query",
                json={"question": query},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', 'No answer received')
                print_success(f"Response: {answer[:100]}...")
            else:
                print_error(f"Query failed: HTTP {response.status_code}")
        except Exception as e:
            print_error(f"Query error: {str(e)}")
        time.sleep(1)

def demo_performance_test():
    """Demo Performance Test"""
    print_demo_header("Performance Test")
    
    # Test multiple requests
    response_times = []
    success_count = 0
    total_requests = 5
    
    for i in range(total_requests):
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/api/health", timeout=10)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                response_times.append(response_time)
                success_count += 1
                print_info(f"Request {i+1}: {response_time:.2f}ms")
            else:
                print_error(f"Request {i+1}: Failed (HTTP {response.status_code})")
        except Exception as e:
            print_error(f"Request {i+1}: Error - {str(e)}")
        
        time.sleep(0.5)
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print_success(f"Performance Summary:")
        print_info(f"  Success rate: {success_count}/{total_requests} ({success_count/total_requests*100:.1f}%)")
        print_info(f"  Average response time: {avg_time:.2f}ms")
        print_info(f"  Min response time: {min_time:.2f}ms")
        print_info(f"  Max response time: {max_time:.2f}ms")
        
        if avg_time < 100:
            print_success("Performance: Excellent")
        elif avg_time < 500:
            print_success("Performance: Good")
        else:
            print_error("Performance: Needs improvement")

def main():
    """Main demo function"""
    print("🎬 Vietnamese AI Voice Chat System - Agent Demo")
    print(f"📅 Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Run all demos
    demos = [
        demo_system_overview,
        demo_knowledge_agent,
        demo_booking_agent,
        demo_email_functionality,
        demo_voice_chat_simulation,
        demo_agent_routing,
        demo_performance_test
    ]
    
    for demo in demos:
        try:
            demo()
            time.sleep(2)  # Pause between demos
        except Exception as e:
            print_error(f"Demo failed: {str(e)}")
    
    print(f"\n{'='*60}")
    print("🎉 Demo completed!")
    print(f"📅 Demo finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 You can now access the web interface at: http://localhost:8080")
    print("📧 Check your email for test messages")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 