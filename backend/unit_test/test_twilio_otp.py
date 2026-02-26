"""
Test script for Twilio OTP integration
Run this to verify your Twilio setup is working
"""

import os
from dotenv import load_dotenv
from twilio_service import twilio_verify

# Load environment variables
load_dotenv()

def test_configuration():
    """Test if Twilio is properly configured"""
    print("=" * 60)
    print("Testing Twilio Configuration")
    print("=" * 60)
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    verify_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')
    
    print(f"Account SID: {'✓ Set' if account_sid else '✗ Missing'}")
    print(f"Auth Token: {'✓ Set' if auth_token else '✗ Missing'}")
    print(f"Verify Service SID: {'✓ Set' if verify_sid else '✗ Missing'}")
    print()
    
    if twilio_verify.is_configured():
        print("✓ Twilio is properly configured!")
        return True
    else:
        print("✗ Twilio configuration incomplete")
        print("\nPlease set the following in your .env file:")
        print("  TWILIO_ACCOUNT_SID=your_account_sid")
        print("  TWILIO_AUTH_TOKEN=your_auth_token")
        print("  TWILIO_VERIFY_SERVICE_SID=your_verify_service_sid")
        return False

def test_send_otp(phone_number):
    """Test sending OTP to a phone number"""
    print("\n" + "=" * 60)
    print(f"Sending OTP to {phone_number}")
    print("=" * 60)
    
    result = twilio_verify.send_otp(phone_number, 'sms')
    
    if result['success']:
        print(f"✓ OTP sent successfully!")
        print(f"  Status: {result['status']}")
        print(f"  To: {result['to']}")
        print(f"  Channel: {result['channel']}")
        return True
    else:
        print(f"✗ Failed to send OTP")
        print(f"  Error: {result.get('error')}")
        if 'code' in result:
            print(f"  Error Code: {result['code']}")
        return False

def test_verify_otp(phone_number, code):
    """Test verifying an OTP code"""
    print("\n" + "=" * 60)
    print(f"Verifying OTP for {phone_number}")
    print("=" * 60)
    
    result = twilio_verify.verify_otp(phone_number, code)
    
    if result['success']:
        print(f"✓ OTP verified successfully!")
        print(f"  Status: {result['status']}")
        print(f"  Valid: {result['valid']}")
        return True
    else:
        print(f"✗ OTP verification failed")
        print(f"  Error: {result.get('error')}")
        if 'code' in result:
            print(f"  Error Code: {result['code']}")
        return False

def main():
    """Main test function"""
    print("\n🔐 Twilio OTP Test Suite\n")
    
    # Test 1: Configuration
    if not test_configuration():
        print("\n❌ Configuration test failed. Please fix configuration and try again.")
        return
    
    # Test 2: Send OTP (interactive)
    print("\n" + "=" * 60)
    print("Interactive OTP Test")
    print("=" * 60)
    print("\nNote: For Twilio trial accounts, you must verify phone numbers first")
    print("Visit: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
    
    phone = input("\nEnter phone number (E.164 format, e.g., +1234567890): ").strip()
    
    if not phone:
        print("❌ No phone number provided. Exiting.")
        return
    
    # Send OTP
    if not test_send_otp(phone):
        print("\n❌ Failed to send OTP. Check your Twilio configuration.")
        return
    
    # Verify OTP
    print("\n📱 Check your phone for the OTP code")
    code = input("Enter the 6-digit code you received: ").strip()
    
    if not code:
        print("❌ No code provided. Exiting.")
        return
    
    if test_verify_otp(phone, code):
        print("\n✅ All tests passed! Twilio OTP is working correctly.")
    else:
        print("\n❌ OTP verification failed. Please check the code and try again.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
