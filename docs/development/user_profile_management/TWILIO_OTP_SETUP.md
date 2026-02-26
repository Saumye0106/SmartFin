# Twilio OTP Integration Guide

Complete guide to integrate Twilio Verify for OTP authentication in SmartFin.

## 🚀 Quick Start

### 1. Get Twilio Credentials

1. **Sign up for Twilio**: https://www.twilio.com/try-twilio
   - Free trial includes $15 credit
   - No credit card required for trial

2. **Get Account SID and Auth Token**:
   - Go to: https://console.twilio.com
   - Find your credentials on the dashboard
   - Copy `Account SID` and `Auth Token`

3. **Create a Verify Service**:
   - Go to: https://console.twilio.com/us1/develop/verify/services
   - Click "Create new Service"
   - Give it a name (e.g., "SmartFin OTP")
   - Copy the `Service SID`

### 2. Install Dependencies

```bash
cd backend
pip install twilio==9.0.4
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and add your Twilio credentials:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_VERIFY_SERVICE_SID=VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
JWT_SECRET_KEY=your-secret-key-change-this
```

### 4. Load Environment Variables

Install python-dotenv:
```bash
pip install python-dotenv
```

Add to the top of `backend/app.py`:
```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file
```

### 5. Restart Backend Server

```bash
cd backend
python app.py
```

## 📱 API Endpoints

### 1. Send OTP

**Endpoint**: `POST /send-otp`

**Request Body**:
```json
{
  "to": "+1234567890",
  "channel": "sms"
}
```

**Channels**: `sms`, `email`, `whatsapp`

**Phone Format**: E.164 format (e.g., `+1234567890` for US)

**Response**:
```json
{
  "message": "OTP sent successfully via sms",
  "status": "pending",
  "to": "+1234567890",
  "channel": "sms"
}
```

### 2. Verify OTP

**Endpoint**: `POST /verify-otp`

**Request Body**:
```json
{
  "to": "+1234567890",
  "code": "123456"
}
```

**Response**:
```json
{
  "message": "OTP verified successfully",
  "status": "approved",
  "valid": true
}
```

### 3. Register with OTP

**Endpoint**: `POST /register-with-otp`

**Two-Step Process**:

**Step 1**: Send OTP to phone
```bash
curl -X POST http://localhost:5000/send-otp \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "channel": "sms"}'
```

**Step 2**: Register with OTP code
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "phone": "+1234567890",
  "otp_code": "123456"
}
```

**Response**:
```json
{
  "message": "Registration successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "phone_verified": true
  }
}
```

### 4. Password Reset with OTP

**Endpoint**: `POST /forgot-password-otp`

**Two-Step Process**:

**Step 1**: Send OTP
```json
{
  "email": "user@example.com",
  "phone": "+1234567890"
}
```

**Step 2**: Reset password with OTP
```json
{
  "email": "user@example.com",
  "phone": "+1234567890",
  "otp_code": "123456",
  "new_password": "newpassword123"
}
```

## 🎨 Frontend Integration

### Update API Service

Add to `frontend/src/services/api.js`:

```javascript
// Send OTP
sendOTP: async (to, channel = 'sms') => {
  const response = await fetch(`${API_BASE_URL}/send-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ to, channel })
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to send OTP');
  }
  return response.json();
},

// Verify OTP
verifyOTP: async (to, code) => {
  const response = await fetch(`${API_BASE_URL}/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ to, code })
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Invalid OTP');
  }
  return response.json();
},

// Register with OTP
registerWithOTP: async (email, password, phone, otpCode) => {
  const response = await fetch(`${API_BASE_URL}/register-with-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      password,
      phone,
      otp_code: otpCode
    })
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Registration failed');
  }
  return response.json();
}
```

### Example: OTP Verification Component

```jsx
import { useState } from 'react';
import api from '../services/api';

function OTPVerification({ phone, onVerified }) {
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSendOTP = async () => {
    try {
      setLoading(true);
      await api.sendOTP(phone, 'sms');
      alert('OTP sent to your phone!');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    try {
      setLoading(true);
      const result = await api.verifyOTP(phone, otp);
      if (result.valid) {
        onVerified();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleSendOTP} disabled={loading}>
        Send OTP
      </button>
      <input
        type="text"
        value={otp}
        onChange={(e) => setOtp(e.target.value)}
        placeholder="Enter 6-digit code"
        maxLength={6}
      />
      <button onClick={handleVerifyOTP} disabled={loading}>
        Verify
      </button>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
```

## 🧪 Testing

### Test with cURL

**Send OTP**:
```bash
curl -X POST http://localhost:5000/send-otp \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "channel": "sms"}'
```

**Verify OTP**:
```bash
curl -X POST http://localhost:5000/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "code": "123456"}'
```

### Test with Postman

1. Import the endpoints
2. Set `Content-Type: application/json`
3. Test each endpoint with sample data

## 💰 Pricing

**Twilio Verify Pricing** (as of 2024):
- SMS: $0.05 per verification
- Email: $0.05 per verification
- WhatsApp: $0.005 per verification
- Voice: $0.05 per verification

**Free Trial**:
- $15 credit (300 SMS verifications)
- Test with verified phone numbers

## 🔒 Security Best Practices

1. **Never expose credentials**: Use environment variables
2. **Rate limiting**: Implement rate limits on OTP endpoints
3. **Attempt limits**: Limit verification attempts (Twilio does this automatically)
4. **Expiration**: OTPs expire after 10 minutes (Twilio default)
5. **HTTPS only**: Use HTTPS in production
6. **Validate phone format**: Use E.164 format validation

## 🐛 Troubleshooting

### Error: "Twilio not configured"
- Check `.env` file exists in `backend/` directory
- Verify environment variables are loaded
- Restart the backend server

### Error: "Invalid phone number"
- Use E.164 format: `+[country code][number]`
- Example: `+12025551234` (US), `+919876543210` (India)

### Error: "Unable to create record"
- Check Verify Service SID is correct
- Verify Twilio account is active
- Check trial account phone number is verified

### OTP not received
- Check phone number format
- Verify phone is verified in Twilio console (trial accounts)
- Check Twilio logs: https://console.twilio.com/us1/monitor/logs/

## 📚 Additional Resources

- [Twilio Verify Documentation](https://www.twilio.com/docs/verify/api)
- [Twilio Python SDK](https://www.twilio.com/docs/libraries/python)
- [E.164 Phone Format](https://www.twilio.com/docs/glossary/what-e164)
- [Twilio Console](https://console.twilio.com)

## 🎯 Use Cases

1. **Two-Factor Authentication (2FA)**: Add extra security layer
2. **Phone Verification**: Verify user phone numbers during registration
3. **Password Reset**: Secure password reset via SMS
4. **Transaction Verification**: Confirm sensitive operations
5. **Account Recovery**: Help users regain access

## 🔄 Migration from Current System

To migrate from the current email-based reset to Twilio OTP:

1. Keep existing `/forgot-password` endpoint for backward compatibility
2. Add new `/forgot-password-otp` endpoint for OTP-based reset
3. Update frontend to offer both options
4. Gradually migrate users to OTP system
5. Eventually deprecate email-based system

## ✅ Next Steps

1. ✅ Install Twilio SDK
2. ✅ Create Twilio account and get credentials
3. ✅ Configure environment variables
4. ✅ Test OTP sending
5. ✅ Test OTP verification
6. ⬜ Update frontend components
7. ⬜ Add phone number field to user registration
8. ⬜ Implement rate limiting
9. ⬜ Add analytics/monitoring
10. ⬜ Deploy to production
