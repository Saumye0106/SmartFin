"""
Twilio Verify Service for OTP Authentication
Handles sending and verifying OTP codes via SMS, Email, or WhatsApp
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Load environment variables
load_dotenv()

class TwilioVerifyService:
    def __init__(self):
        # Get credentials from environment variables
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.verify_service_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')
        
        # Initialize Twilio client
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            print("Warning: Twilio credentials not configured")
    
    def is_configured(self):
        """Check if Twilio is properly configured"""
        return self.client is not None and self.verify_service_sid is not None
    
    def send_otp(self, to, channel='sms'):
        """
        Send OTP to user via specified channel
        
        Args:
            to (str): Phone number (E.164 format: +1234567890) or email
            channel (str): 'sms', 'email', or 'whatsapp'
        
        Returns:
            dict: Success status and message
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Twilio not configured'
            }
        
        try:
            verification = self.client.verify.v2.services(
                self.verify_service_sid
            ).verifications.create(
                to=to,
                channel=channel
            )
            
            return {
                'success': True,
                'status': verification.status,
                'to': verification.to,
                'channel': verification.channel
            }
        
        except TwilioRestException as e:
            return {
                'success': False,
                'error': str(e),
                'code': e.code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_otp(self, to, code):
        """
        Verify OTP code
        
        Args:
            to (str): Phone number or email (same as used in send_otp)
            code (str): 6-digit OTP code
        
        Returns:
            dict: Verification result
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Twilio not configured'
            }
        
        try:
            verification_check = self.client.verify.v2.services(
                self.verify_service_sid
            ).verification_checks.create(
                to=to,
                code=code
            )
            
            return {
                'success': verification_check.status == 'approved',
                'status': verification_check.status,
                'valid': verification_check.valid
            }
        
        except TwilioRestException as e:
            return {
                'success': False,
                'error': str(e),
                'code': e.code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Singleton instance
twilio_verify = TwilioVerifyService()
