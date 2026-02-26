# Phone Number Management Implementation

Complete implementation of phone number management in user profiles with OTP verification.

## ✅ What Was Implemented

### Backend Changes

1. **Database Schema** (`backend/app.py`)
   - `phone` field already added to `users` table
   - Stores phone numbers in E.164 format

2. **New API Endpoints** (`backend/app.py`)
   - `POST /update-phone` - Update phone with OTP verification
   - `GET /get-phone` - Get user's current phone number

### Frontend Changes

1. **ProfilePage Component** (`frontend/src/components/ProfilePage.jsx`)
   - Added `PhoneNumberDisplay` component
   - Shows current phone number or warning if not set
   - "Add Phone" / "Update" button to edit

2. **ProfileEditForm Component** (`frontend/src/components/ProfileEditForm.jsx`)
   - Added `PhoneUpdateSection` component
   - Two-step phone update process:
     - Step 1: Enter new phone number → Send OTP
     - Step 2: Enter OTP code → Verify and update

3. **API Service** (`frontend/src/services/api.js`)
   - Added `getUserPhone()` - Fetch current phone
   - Added `updatePhone(phone, otpCode)` - Update phone with OTP

## 🔄 User Flow

### View Phone Number (ProfilePage)
1. User navigates to `/profile`
2. Phone number section shows:
   - Current phone if set
   - Warning "Not set (required for password reset)" if not set
3. Click "Add Phone" or "Update" button → Navigate to edit form

### Add/Update Phone Number (ProfileEditForm)
1. User navigates to `/profile/edit`
2. Scroll to "Phone Number" section
3. **Step 1**: Enter phone number (E.164 format) → Click "Add/Update Phone Number"
4. System sends OTP via SMS
5. **Step 2**: Enter 6-digit OTP code → Click "Verify OTP"
6. Phone number is updated in database
7. Success message displayed

## 🔐 Security Features

1. **OTP Verification Required**: Can't update phone without verifying ownership
2. **JWT Authentication**: All endpoints require valid JWT token
3. **Phone Format Validation**: Must use E.164 format
4. **OTP Expiration**: Codes expire after 10 minutes
5. **One-Time Use**: Each OTP can only be used once

## 📱 Phone Number Format

Always use **E.164 format**:
- **India**: `+917880308989`
- **US**: `+12025551234`
- **UK**: `+447911123456`

Format: `+[country code][number]` (no spaces or dashes)

## 🧪 Testing

### Test Add Phone Number:

1. **Navigate to Profile**:
   ```
   http://localhost:5173/profile
   ```

2. **Check Phone Status**:
   - Should show "Not set (required for password reset)"

3. **Click "Add Phone"**:
   - Navigate to edit form

4. **Enter Phone Number**:
   - Format: `+917880308989`
   - Click "Add Phone Number"

5. **Check Your Phone**:
   - Receive SMS with 6-digit code

6. **Enter OTP**:
   - Type the code
   - Click "Verify OTP"

7. **Verify Update**:
   - Success message appears
   - Navigate back to profile
   - Phone number now displayed

### Test Update Phone Number:

1. Follow same steps as above
2. Button will say "Update Phone Number" instead
3. Enter different phone number
4. Verify with OTP
5. Phone number updated

## 💰 Cost

**Per Phone Update**:
- 1 SMS OTP = $0.05
- Most users update once during setup

**Estimated Monthly Cost**:
- 100 new users/month = $5
- 10 phone updates/month = $0.50
- Total: ~$5.50/month

## 🎨 UI Components

### ProfilePage - Phone Display
```jsx
<PhoneNumberDisplay />
```
- Shows current phone or warning
- Fetches phone on mount
- Loading state while fetching

### ProfileEditForm - Phone Update
```jsx
<PhoneUpdateSection />
```
- Two-step form (phone entry → OTP verification)
- Success/error messaging
- Loading states
- Cancel functionality

## 📋 API Endpoints

### Get Phone Number
```http
GET /get-phone
Authorization: Bearer <token>
```

**Response**:
```json
{
  "phone": "+917880308989"
}
```

### Update Phone - Step 1 (Send OTP)
```http
POST /update-phone
Authorization: Bearer <token>
Content-Type: application/json

{
  "phone": "+917880308989"
}
```

**Response**:
```json
{
  "message": "OTP sent to your phone",
  "status": "pending"
}
```

### Update Phone - Step 2 (Verify OTP)
```http
POST /update-phone
Authorization: Bearer <token>
Content-Type: application/json

{
  "phone": "+917880308989",
  "otp_code": "123456"
}
```

**Response**:
```json
{
  "message": "Phone number updated successfully",
  "phone": "+917880308989"
}
```

## 🐛 Troubleshooting

### Error: "Invalid parameter `To`"
**Solution**: Use E.164 format with country code: `+917880308989`

### Error: "Unable to create record"
**Solution**: Verify your phone number in Twilio console (trial accounts only)

### OTP Not Received
**Solutions**:
1. Check phone number format
2. Verify phone in Twilio console
3. Check Twilio logs
4. Ensure you have Twilio credit

### Error: "Failed to get phone number"
**Solution**: 
1. Check if user is logged in (JWT token valid)
2. Check backend server is running
3. Check database connection

## 🔗 Integration with Password Reset

The phone number management integrates seamlessly with the forgot password feature:

1. **User adds phone during profile setup**
2. **Phone is verified with OTP**
3. **Phone stored in database**
4. **During password reset**:
   - User enters email
   - System looks up registered phone
   - OTP sent to registered phone
   - User verifies and resets password

## ✅ Benefits

1. **Security**: Phone verification prevents unauthorized password resets
2. **User Control**: Users can update their phone anytime
3. **Transparency**: Clear indication if phone is not set
4. **Seamless**: Integrated into existing profile management
5. **Secure**: OTP verification for all phone updates

## 🚀 Next Steps

### Optional Enhancements:

1. **Add Phone During Registration**:
   - Update AuthPage to collect phone during signup
   - Verify phone before account creation

2. **Phone Verification Badge**:
   - Show verified badge next to phone number
   - Track verification status in database

3. **Multiple Phone Numbers**:
   - Allow users to add backup phone numbers
   - Choose primary phone for OTP

4. **Phone Change History**:
   - Log all phone number changes
   - Show change history in profile

5. **SMS Preferences**:
   - Allow users to opt-in/out of SMS notifications
   - Separate from OTP verification

## 📚 Related Documentation

- **Twilio Setup**: `docs/TWILIO_OTP_SETUP.md`
- **Forgot Password**: `docs/TWILIO_FORGOT_PASSWORD_IMPLEMENTATION.md`
- **Implementation Summary**: `docs/TWILIO_IMPLEMENTATION_SUMMARY.md`

---

**Status**: ✅ Implementation Complete - Ready for Testing!

**Test URLs**: 
- Profile: http://localhost:5173/profile
- Edit: http://localhost:5173/profile/edit
