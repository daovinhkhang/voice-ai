#!/usr/bin/env python3
"""
Booking Agent - Quản lý booking và gửi email
Hỗ trợ booking lịch hẹn, lưu thông tin khách hàng và gửi email tự động
"""

import os
import logging
import json
import smtplib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Database
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Google Gmail API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import config

logger = logging.getLogger(__name__)

# Database models
Base = declarative_base()

class Customer(Base):
    """Model khách hàng"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20))
    company = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Booking(Base):
    """Model booking"""
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    service_type = Column(String(100), nullable=False)
    booking_date = Column(DateTime, nullable=False)
    duration = Column(Integer, default=60)  # minutes
    status = Column(String(20), default='pending')  # pending, confirmed, cancelled
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class BookingAgent:
    """Agent quản lý booking và gửi email"""
    
    def __init__(self):
        """Khởi tạo Booking Agent"""
        # Database setup
        self.engine = create_engine('sqlite:///booking_system.db')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Email settings
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.smtp_username = config.SMTP_USERNAME
        self.smtp_password = config.SMTP_PASSWORD
        
        # Gmail API settings
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        self.gmail_service = None
        
        logger.info("Booking Agent initialized")
    
    def add_customer(self, customer_data: Dict) -> Dict:
        """
        Thêm khách hàng mới
        
        Args:
            customer_data: Thông tin khách hàng
            
        Returns:
            Kết quả thêm khách hàng
        """
        try:
            # Kiểm tra email đã tồn tại
            existing_customer = self.session.query(Customer).filter_by(
                email=customer_data['email']
            ).first()
            
            if existing_customer:
                return {
                    "success": False,
                    "message": "Email đã tồn tại trong hệ thống",
                    "customer_id": existing_customer.id
                }
            
            # Tạo khách hàng mới
            customer = Customer(
                name=customer_data['name'],
                email=customer_data['email'],
                phone=customer_data.get('phone', ''),
                company=customer_data.get('company', ''),
                notes=customer_data.get('notes', '')
            )
            
            self.session.add(customer)
            self.session.commit()
            
            logger.info(f"Added new customer: {customer.name} ({customer.email})")
            
            return {
                "success": True,
                "message": "Thêm khách hàng thành công",
                "customer_id": customer.id
            }
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding customer: {e}")
            return {
                "success": False,
                "message": f"Lỗi khi thêm khách hàng: {str(e)}"
            }
    
    def create_booking(self, booking_data: Dict) -> Dict:
        """
        Tạo booking mới
        
        Args:
            booking_data: Thông tin booking
            
        Returns:
            Kết quả tạo booking
        """
        try:
            # Kiểm tra khách hàng tồn tại
            customer = self.session.query(Customer).filter_by(
                id=booking_data['customer_id']
            ).first()
            
            if not customer:
                return {
                    "success": False,
                    "message": "Không tìm thấy khách hàng"
                }
            
            # Kiểm tra thời gian booking có hợp lệ
            booking_date = datetime.fromisoformat(booking_data['booking_date'])
            if booking_date < datetime.now():
                return {
                    "success": False,
                    "message": "Thời gian booking không hợp lệ"
                }
            
            # Kiểm tra xung đột lịch
            conflict = self.session.query(Booking).filter(
                Booking.booking_date == booking_date,
                Booking.status == 'confirmed'
            ).first()
            
            if conflict:
                return {
                    "success": False,
                    "message": "Thời gian này đã có lịch hẹn khác"
                }
            
            # Tạo booking
            booking = Booking(
                customer_id=booking_data['customer_id'],
                service_type=booking_data['service_type'],
                booking_date=booking_date,
                duration=booking_data.get('duration', 60),
                notes=booking_data.get('notes', '')
            )
            
            self.session.add(booking)
            self.session.commit()
            
            logger.info(f"Created booking: {booking.id} for {customer.name}")
            
            return {
                "success": True,
                "message": "Tạo booking thành công",
                "booking_id": booking.id
            }
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating booking: {e}")
            return {
                "success": False,
                "message": f"Lỗi khi tạo booking: {str(e)}"
            }
    
    def confirm_booking(self, booking_id: int) -> Dict:
        """
        Xác nhận booking
        
        Args:
            booking_id: ID booking
            
        Returns:
            Kết quả xác nhận
        """
        try:
            booking = self.session.query(Booking).filter_by(id=booking_id).first()
            if not booking:
                return {
                    "success": False,
                    "message": "Không tìm thấy booking"
                }
            
            booking.status = 'confirmed'
            self.session.commit()
            
            # Gửi email xác nhận
            email_sent = self.send_confirmation_email(booking)
            
            logger.info(f"Confirmed booking: {booking_id}")
            
            return {
                "success": True,
                "message": "Xác nhận booking thành công",
                "email_sent": email_sent
            }
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error confirming booking: {e}")
            return {
                "success": False,
                "message": f"Lỗi khi xác nhận booking: {str(e)}"
            }
    
    def send_confirmation_email(self, booking: Booking) -> bool:
        """Gửi email xác nhận booking sử dụng Gmail API"""
        try:
            customer = self.session.query(Customer).filter_by(id=booking.customer_id).first()
            
            # Tạo nội dung email
            subject = f"Xác nhận lịch hẹn - {booking.service_type}"
            
            body = f"""
            Xin chào {customer.name},
            
            Chúng tôi xác nhận lịch hẹn của bạn:
            
            Dịch vụ: {booking.service_type}
            Thời gian: {booking.booking_date.strftime('%d/%m/%Y %H:%M')}
            Thời lượng: {booking.duration} phút
            
            Nếu có thay đổi, vui lòng liên hệ với chúng tôi.
            
            Trân trọng,
            Đội ngũ hỗ trợ
            """
            
            # Thử gửi bằng Gmail API trước
            if self.send_email_gmail_api(customer.email, subject, body):
                logger.info(f"Sent confirmation email via Gmail API to {customer.email}")
                return True
            
            # Fallback to SMTP
            if self.send_email_smtp(customer.email, subject, body):
                logger.info(f"Sent confirmation email via SMTP to {customer.email}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")
            return False
    
    def send_email_gmail_api(self, to_email: str, subject: str, body: str) -> bool:
        """Gửi email sử dụng Gmail API"""
        try:
            if not self.gmail_service:
                self.setup_gmail_api()
            
            if not self.gmail_service:
                return False
            
            # Tạo message
            message = MIMEText(body, 'plain', 'utf-8')
            message['to'] = to_email
            message['from'] = self.smtp_username
            message['subject'] = subject
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Gửi email
            self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email via Gmail API: {e}")
            return False
    
    def send_email_smtp(self, to_email: str, subject: str, body: str) -> bool:
        """Gửi email sử dụng SMTP (fallback)"""
        try:
            # Tạo email
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Gửi email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email via SMTP: {e}")
            return False
    
    def setup_gmail_api(self):
        """Thiết lập Gmail API"""
        try:
            creds = None
            if os.path.exists('gmail_token.json'):
                creds = Credentials.from_authorized_user_file('gmail_token.json', self.SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Sử dụng service account hoặc OAuth2
                    # Tạm thời sử dụng SMTP, có thể cấu hình Gmail API sau
                    logger.warning("Gmail API not configured, using SMTP fallback")
                    return
                
                with open('gmail_token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up Gmail API: {e}")
            logger.info("Will use SMTP fallback for email sending")
    
    def get_customer_list(self) -> List[Dict]:
        """Lấy danh sách khách hàng"""
        try:
            customers = self.session.query(Customer).all()
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "company": c.company,
                    "created_at": c.created_at.isoformat()
                }
                for c in customers
            ]
        except Exception as e:
            logger.error(f"Error getting customer list: {e}")
            return []
    
    def get_booking_list(self, status: str = None) -> List[Dict]:
        """Lấy danh sách booking"""
        try:
            query = self.session.query(Booking)
            if status:
                query = query.filter_by(status=status)
            
            bookings = query.all()
            result = []
            
            for booking in bookings:
                customer = self.session.query(Customer).filter_by(id=booking.customer_id).first()
                result.append({
                    "id": booking.id,
                    "customer_name": customer.name if customer else "Unknown",
                    "customer_email": customer.email if customer else "",
                    "service_type": booking.service_type,
                    "booking_date": booking.booking_date.isoformat(),
                    "duration": booking.duration,
                    "status": booking.status,
                    "notes": booking.notes
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting booking list: {e}")
            return []
    
    def export_customer_data(self, file_path: str) -> bool:
        """
        Xuất dữ liệu khách hàng ra file
        
        Args:
            file_path: Đường dẫn file xuất
            
        Returns:
            True nếu thành công
        """
        try:
            customers = self.get_customer_list()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(customers, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported customer data to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting customer data: {e}")
            return False
    
    def send_test_email(self, to_email: str = None) -> Dict:
        """Gửi email test để kiểm tra cấu hình"""
        try:
            test_email = to_email or "test@example.com"
            subject = "Test Email - Vietnamese AI Voice Chat System"
            body = """
            Đây là email test từ hệ thống Vietnamese AI Voice Chat.
            
            Nếu bạn nhận được email này, có nghĩa là cấu hình email đã hoạt động.
            
            Trân trọng,
            Booking Agent
            """
            
            # Thử Gmail API trước
            if self.send_email_gmail_api(test_email, subject, body):
                return {
                    "success": True,
                    "message": "Test email sent successfully via Gmail API",
                    "method": "gmail_api"
                }
            
            # Fallback to SMTP
            if self.send_email_smtp(test_email, subject, body):
                return {
                    "success": True,
                    "message": "Test email sent successfully via SMTP",
                    "method": "smtp"
                }
            
            return {
                "success": False,
                "message": "Failed to send test email"
            }
            
        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            } 