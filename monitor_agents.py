#!/usr/bin/env python3
"""
Monitoring Script for Vietnamese AI Voice Chat System with Business Agents
Theo dõi liên tục hệ thống và các agent
"""

import requests
import time
import json
import logging
from datetime import datetime, timedelta
import os
import sys

# Configuration
BASE_URL = "http://localhost:8080"
MONITOR_INTERVAL = 30  # seconds
LOG_FILE = "system_monitor.log"
ALERT_EMAIL = "daovinhkhang0834@gmail.com"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitor class for the AI Voice Chat System"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.health_checks = 0
        self.failed_checks = 0
        self.last_alert_time = None
        self.alert_cooldown = 300  # 5 minutes between alerts
        
    def check_system_health(self):
        """Check overall system health"""
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.health_checks += 1
                    logger.info(f"✅ System Health Check #{self.health_checks} - All components ready")
                    return True, data
                else:
                    self.failed_checks += 1
                    logger.error(f"❌ System Health Check #{self.health_checks} - Status: {data.get('status')}")
                    return False, data
            else:
                self.failed_checks += 1
                logger.error(f"❌ System Health Check #{self.health_checks} - HTTP {response.status_code}")
                return False, None
        except Exception as e:
            self.failed_checks += 1
            logger.error(f"❌ System Health Check #{self.health_checks} - Error: {str(e)}")
            return False, None
    
    def check_knowledge_agent(self):
        """Check Knowledge Base Agent"""
        try:
            response = requests.get(f"{BASE_URL}/api/knowledge/summary", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📚 Knowledge Agent - Documents: {data.get('total_documents', 0)}")
                return True
            else:
                logger.error(f"❌ Knowledge Agent - HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Knowledge Agent - Error: {str(e)}")
            return False
    
    def check_booking_agent(self):
        """Check Booking Agent"""
        try:
            response = requests.get(f"{BASE_URL}/api/customers", timeout=10)
            if response.status_code == 200:
                customers = response.json()
                response2 = requests.get(f"{BASE_URL}/api/bookings", timeout=10)
                if response2.status_code == 200:
                    bookings = response2.json()
                    logger.info(f"📅 Booking Agent - Customers: {len(customers)}, Bookings: {len(bookings)}")
                    return True
                else:
                    logger.error(f"❌ Booking Agent - Bookings HTTP {response2.status_code}")
                    return False
            else:
                logger.error(f"❌ Booking Agent - Customers HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Booking Agent - Error: {str(e)}")
            return False
    
    def check_email_functionality(self):
        """Check email functionality"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/test-email",
                json={"email": ALERT_EMAIL},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"📧 Email Test - Success via {data.get('method', 'unknown')}")
                    return True
                else:
                    logger.error(f"❌ Email Test - Failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"❌ Email Test - HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Email Test - Error: {str(e)}")
            return False
    
    def check_performance(self):
        """Check system performance"""
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/api/health", timeout=10)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                if response_time < 100:  # Good performance
                    logger.info(f"⚡ Performance - Response time: {response_time:.2f}ms (Excellent)")
                elif response_time < 500:  # Acceptable performance
                    logger.info(f"⚡ Performance - Response time: {response_time:.2f}ms (Good)")
                else:  # Poor performance
                    logger.warning(f"⚠️ Performance - Response time: {response_time:.2f}ms (Slow)")
                return True
            else:
                logger.error(f"❌ Performance Check - HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Performance Check - Error: {str(e)}")
            return False
    
    def send_alert(self, message):
        """Send alert if cooldown period has passed"""
        current_time = datetime.now()
        if (self.last_alert_time is None or 
            (current_time - self.last_alert_time).total_seconds() > self.alert_cooldown):
            
            try:
                # Send alert via email
                response = requests.post(
                    f"{BASE_URL}/api/test-email",
                    json={
                        "email": ALERT_EMAIL,
                        "subject": "System Alert - Vietnamese AI Voice Chat",
                        "message": f"System Alert: {message}\nTime: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    logger.info(f"📧 Alert sent to {ALERT_EMAIL}")
                    self.last_alert_time = current_time
                else:
                    logger.error(f"❌ Failed to send alert - HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Failed to send alert - Error: {str(e)}")
    
    def generate_report(self):
        """Generate monitoring report"""
        uptime = datetime.now() - self.start_time
        success_rate = ((self.health_checks - self.failed_checks) / max(self.health_checks, 1)) * 100
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "uptime": str(uptime),
            "total_checks": self.health_checks,
            "failed_checks": self.failed_checks,
            "success_rate": f"{success_rate:.2f}%",
            "system_status": "healthy" if success_rate > 95 else "warning" if success_rate > 80 else "critical"
        }
        
        logger.info(f"📊 Monitoring Report: {json.dumps(report, indent=2)}")
        return report
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        logger.info("🔄 Starting monitoring cycle...")
        
        # Check all components
        health_ok, health_data = self.check_system_health()
        knowledge_ok = self.check_knowledge_agent()
        booking_ok = self.check_booking_agent()
        email_ok = self.check_email_functionality()
        performance_ok = self.check_performance()
        
        # Determine overall status
        all_ok = health_ok and knowledge_ok and booking_ok and email_ok and performance_ok
        
        if not all_ok:
            failed_components = []
            if not health_ok: failed_components.append("System Health")
            if not knowledge_ok: failed_components.append("Knowledge Agent")
            if not booking_ok: failed_components.append("Booking Agent")
            if not email_ok: failed_components.append("Email Functionality")
            if not performance_ok: failed_components.append("Performance")
            
            alert_message = f"System monitoring detected issues with: {', '.join(failed_components)}"
            self.send_alert(alert_message)
            logger.warning(f"⚠️ {alert_message}")
        else:
            logger.info("✅ All systems operational")
        
        return all_ok
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        logger.info("🚀 Starting Vietnamese AI Voice Chat System Monitor")
        logger.info(f"📡 Monitoring URL: {BASE_URL}")
        logger.info(f"⏰ Check interval: {MONITOR_INTERVAL} seconds")
        logger.info(f"📧 Alert email: {ALERT_EMAIL}")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"🔄 Monitoring Cycle #{cycle_count}")
                
                success = self.run_monitoring_cycle()
                
                # Generate report every 10 cycles
                if cycle_count % 10 == 0:
                    self.generate_report()
                
                logger.info(f"⏳ Waiting {MONITOR_INTERVAL} seconds until next check...")
                time.sleep(MONITOR_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
            self.generate_report()
        except Exception as e:
            logger.error(f"❌ Monitoring error: {str(e)}")
            self.send_alert(f"Monitoring system error: {str(e)}")

def main():
    """Main function"""
    monitor = SystemMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main() 