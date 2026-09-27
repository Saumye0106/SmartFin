"""
Auth Blueprint
Registration, login, tokens, email verification, password reset, and
Twilio-backed OTP flows (phone update, OTP registration, OTP password reset).
"""

import re
import random
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash

from db_core import get_db
from twilio_service import twilio_verify

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


# ==================== REGISTRATION / LOGIN / TOKENS ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user and send email verification"""
    try:
        data = request.get_json()
        print(f"Register request data: {data}")  # Debug logging
        username = data.get('email')  # Frontend sends 'email' field
        password = data.get('password')

        if not username or not password:
            print(f"Missing fields - username: {username}, password: {password}")  # Debug
            return jsonify({'error': 'Username and password required'}), 400

        if not re.match(EMAIL_REGEX, username):
            return jsonify({'error': 'Invalid email address format'}), 400

        if len(password) < 6:
            print(f"Password too short: {len(password)} chars")  # Debug
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        db = get_db()
        cur = db.cursor()

        # Check if user exists
        cur.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cur.fetchone():
            return jsonify({'error': 'User already exists'}), 409

        # Create user (email_verified defaults to 0)
        password_hash = generate_password_hash(password)
        cur.execute(
            'INSERT INTO users (username, password_hash, created_at, email_verified) VALUES (?, ?, ?, 0)',
            (username, password_hash, datetime.utcnow().isoformat())
        )
        db.commit()

        # Get the new user's ID
        user_id = cur.lastrowid

        # Send email verification OTP
        verification_result = twilio_verify.send_otp(username, 'email')

        if verification_result['success']:
            # Store verification expiry
            expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            cur.execute(
                'UPDATE users SET email_verification_expires = ? WHERE id = ?',
                (expires_at, user_id)
            )
            db.commit()

        # Create tokens (user can login but will be prompted to verify email)
        access_token = create_access_token(identity=str(user_id))
        refresh_token = create_refresh_token(identity=str(user_id))

        return jsonify({
            'message': 'User registered successfully. Please verify your email.',
            'token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_id,
                'username': username,
                'email_verified': False
            },
            'verification_sent': verification_result['success']
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT tokens"""
    try:
        data = request.get_json()
        username = data.get('email')  # Frontend sends 'email' field
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        if not re.match(EMAIL_REGEX, username):
            return jsonify({'error': 'Invalid email address format'}), 400

        db = get_db()
        cur = db.cursor()

        # Get user
        cur.execute('SELECT id, username, password_hash, email_verified FROM users WHERE username = ?', (username,))
        user = cur.fetchone()

        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Create tokens
        access_token = create_access_token(identity=str(user['id']))
        refresh_token = create_refresh_token(identity=str(user['id']))

        return jsonify({
            'token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email_verified': bool(user['email_verified'])
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """Protected endpoint - requires valid JWT"""
    current_user_id = get_jwt_identity()
    return jsonify({'message': 'Access granted', 'user_id': current_user_id}), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify({'token': new_access_token}), 200


@auth_bp.route('/update-phone', methods=['POST'])
@jwt_required()
def update_phone():
    """
    Update user's phone number with OTP verification
    Step 1: Send OTP to new phone number
    Step 2: Verify OTP and update phone in database
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        phone = data.get('phone')
        otp_code = data.get('otp_code')

        if not phone:
            return jsonify({'error': 'Phone number is required'}), 400

        # If OTP code provided, verify and update phone
        if otp_code:
            # Verify OTP
            verify_result = twilio_verify.verify_otp(phone, otp_code)
            if not verify_result['success']:
                return jsonify({'error': 'Invalid or expired OTP'}), 400

            # Update phone in database
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'UPDATE users SET phone = ? WHERE id = ?',
                (phone, current_user_id)
            )
            db.commit()

            return jsonify({
                'message': 'Phone number updated successfully',
                'phone': phone
            }), 200

        # Otherwise, send OTP to new phone number
        else:
            send_result = twilio_verify.send_otp(phone, 'sms')
            if send_result['success']:
                return jsonify({
                    'message': 'OTP sent to your phone',
                    'status': send_result['status']
                }), 200
            else:
                return jsonify({'error': send_result.get('error', 'Failed to send OTP')}), 400

    except Exception as e:
        return jsonify({'error': f'Failed to update phone: {str(e)}'}), 500


@auth_bp.route('/get-phone', methods=['GET'])
@jwt_required()
def get_phone():
    """Get user's current phone number"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        cur = db.cursor()

        cur.execute('SELECT phone FROM users WHERE id = ?', (current_user_id,))
        user = cur.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'phone': user['phone']
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get phone: {str(e)}'}), 500


# ==================== EMAIL VERIFICATION ENDPOINTS ====================

@auth_bp.route('/send-email-verification', methods=['POST'])
def send_email_verification():
    """
    Send email verification OTP to user's email
    Can be called during registration or to resend verification
    """
    try:
        data = request.get_json()
        email = data.get('email')
        user_id = data.get('user_id')  # Optional: for resend after registration

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        db = get_db()
        cur = db.cursor()

        # If user_id provided, verify it matches the email
        if user_id:
            cur.execute('SELECT username, email_verified FROM users WHERE id = ?', (user_id,))
            user = cur.fetchone()
            if not user or user['username'] != email:
                return jsonify({'error': 'Invalid user'}), 400
            if user['email_verified']:
                return jsonify({'error': 'Email already verified'}), 400
        else:
            # Check if email exists
            cur.execute('SELECT id, email_verified FROM users WHERE username = ?', (email,))
            user = cur.fetchone()
            if not user:
                return jsonify({'error': 'Email not found'}), 404
            if user['email_verified']:
                return jsonify({'error': 'Email already verified'}), 400
            user_id = user['id']

        # Send OTP via Twilio Verify (email channel)
        result = twilio_verify.send_otp(email, 'email')

        if result['success']:
            # Store verification attempt timestamp
            expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            cur.execute(
                'UPDATE users SET email_verification_expires = ? WHERE id = ?',
                (expires_at, user_id)
            )
            db.commit()

            return jsonify({
                'message': 'Verification code sent to your email',
                'status': result['status'],
                'user_id': user_id
            }), 200
        else:
            return jsonify({'error': result.get('error', 'Failed to send verification code')}), 400

    except Exception as e:
        return jsonify({'error': f'Failed to send verification: {str(e)}'}), 500


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """
    Verify email using OTP code
    """
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        user_id = data.get('user_id')  # Optional

        if not email or not code:
            return jsonify({'error': 'Email and verification code are required'}), 400

        db = get_db()
        cur = db.cursor()

        # Get user
        if user_id:
            cur.execute('SELECT id, username, email_verified, email_verification_expires FROM users WHERE id = ?', (user_id,))
        else:
            cur.execute('SELECT id, username, email_verified, email_verification_expires FROM users WHERE username = ?', (email,))

        user = cur.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        if user['email_verified']:
            return jsonify({'message': 'Email already verified', 'already_verified': True}), 200

        # Check if verification expired
        if user['email_verification_expires']:
            expires_at = datetime.fromisoformat(user['email_verification_expires'])
            if datetime.utcnow() > expires_at:
                return jsonify({'error': 'Verification code expired. Please request a new one.'}), 400

        # Verify OTP via Twilio
        result = twilio_verify.verify_otp(email, code)

        if result['success']:
            # Mark email as verified
            cur.execute(
                'UPDATE users SET email_verified = 1, email_verification_token = NULL, email_verification_expires = NULL WHERE id = ?',
                (user['id'],)
            )
            db.commit()

            return jsonify({
                'message': 'Email verified successfully',
                'verified': True
            }), 200
        else:
            return jsonify({'error': result.get('error', 'Invalid or expired verification code')}), 400

    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500


@auth_bp.route('/check-email-verification', methods=['GET'])
@jwt_required()
def check_email_verification():
    """Check if current user's email is verified"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        cur = db.cursor()

        cur.execute('SELECT email_verified, username FROM users WHERE id = ?', (current_user_id,))
        user = cur.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'email': user['username'],
            'verified': bool(user['email_verified'])
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to check verification: {str(e)}'}), 500


# ==================== PASSWORD RESET ENDPOINTS ====================

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Generate a password reset code for the user
    In a real app, this would send an email. For this educational project,
    we'll return the code directly.
    """
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        db = get_db()
        cur = db.cursor()

        # Check if user exists
        cur.execute('SELECT id FROM users WHERE username = ?', (email,))
        user = cur.fetchone()

        if not user:
            # For security, don't reveal if email exists
            # But return success anyway
            return jsonify({
                'message': 'If this email exists, a reset code has been generated',
                'reset_code': None  # Don't send code if user doesn't exist
            }), 200

        user_id = user['id']

        # Generate a 6-digit reset code
        reset_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # Set expiration to 15 minutes from now
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(minutes=15)

        # Invalidate any existing unused tokens for this user
        cur.execute(
            'UPDATE password_reset_tokens SET used = 1 WHERE user_id = ? AND used = 0',
            (user_id,)
        )

        # Insert new reset token
        cur.execute(
            '''INSERT INTO password_reset_tokens
               (user_id, reset_code, created_at, expires_at, used)
               VALUES (?, ?, ?, ?, 0)''',
            (user_id, reset_code, created_at.isoformat(), expires_at.isoformat())
        )

        db.commit()

        # In a real app, send email here
        # For educational purposes, return the code
        return jsonify({
            'message': 'Reset code generated successfully',
            'reset_code': reset_code,  # Only for educational purposes!
            'expires_in_minutes': 15
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to generate reset code: {str(e)}'}), 500


@auth_bp.route('/verify-reset-code', methods=['POST'])
def verify_reset_code():
    """Verify if a reset code is valid"""
    try:
        data = request.get_json()
        email = data.get('email')
        reset_code = data.get('reset_code')

        if not email or not reset_code:
            return jsonify({'error': 'Email and reset code are required'}), 400

        db = get_db()
        cur = db.cursor()

        # Get user
        cur.execute('SELECT id FROM users WHERE username = ?', (email,))
        user = cur.fetchone()

        if not user:
            return jsonify({'error': 'Invalid reset code'}), 400

        user_id = user['id']

        # Check if code exists and is valid
        cur.execute(
            '''SELECT id, expires_at FROM password_reset_tokens
               WHERE user_id = ? AND reset_code = ? AND used = 0''',
            (user_id, reset_code)
        )
        token = cur.fetchone()

        if not token:
            return jsonify({'error': 'Invalid or expired reset code'}), 400

        # Check if expired
        expires_at = datetime.fromisoformat(token['expires_at'])
        if datetime.utcnow() > expires_at:
            return jsonify({'error': 'Reset code has expired'}), 400

        return jsonify({
            'message': 'Reset code is valid',
            'valid': True
        }), 200

    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using a valid reset code"""
    try:
        data = request.get_json()
        email = data.get('email')
        reset_code = data.get('reset_code')
        new_password = data.get('new_password')

        if not email or not reset_code or not new_password:
            return jsonify({'error': 'Email, reset code, and new password are required'}), 400

        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        db = get_db()
        cur = db.cursor()

        # Get user
        cur.execute('SELECT id FROM users WHERE username = ?', (email,))
        user = cur.fetchone()

        if not user:
            return jsonify({'error': 'Invalid reset code'}), 400

        user_id = user['id']

        # Check if code exists and is valid
        cur.execute(
            '''SELECT id, expires_at FROM password_reset_tokens
               WHERE user_id = ? AND reset_code = ? AND used = 0''',
            (user_id, reset_code)
        )
        token = cur.fetchone()

        if not token:
            return jsonify({'error': 'Invalid or expired reset code'}), 400

        # Check if expired
        expires_at = datetime.fromisoformat(token['expires_at'])
        if datetime.utcnow() > expires_at:
            return jsonify({'error': 'Reset code has expired'}), 400

        # Update password
        new_password_hash = generate_password_hash(new_password)
        cur.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (new_password_hash, user_id)
        )

        # Mark token as used
        cur.execute(
            'UPDATE password_reset_tokens SET used = 1 WHERE id = ?',
            (token['id'],)
        )

        db.commit()

        return jsonify({
            'message': 'Password reset successfully',
            'success': True
        }), 200

    except Exception as e:
        return jsonify({'error': f'Password reset failed: {str(e)}'}), 500


# ==================== TWILIO OTP ENDPOINTS ====================

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """
    Send OTP via Twilio Verify
    Supports SMS, Email, and WhatsApp channels
    """
    try:
        data = request.get_json()
        to = data.get('to')  # Phone number (E.164 format: +1234567890) or email
        channel = data.get('channel', 'sms')  # 'sms', 'email', or 'whatsapp'

        if not to:
            return jsonify({'error': 'Recipient (phone/email) is required'}), 400

        if channel not in ['sms', 'email', 'whatsapp']:
            return jsonify({'error': 'Invalid channel. Use: sms, email, or whatsapp'}), 400

        # Send OTP via Twilio
        result = twilio_verify.send_otp(to, channel)

        if result['success']:
            return jsonify({
                'message': f'OTP sent successfully via {channel}',
                'status': result['status'],
                'to': result['to'],
                'channel': result['channel']
            }), 200
        else:
            return jsonify({
                'error': result.get('error', 'Failed to send OTP'),
                'code': result.get('code')
            }), 400

    except Exception as e:
        return jsonify({'error': f'Failed to send OTP: {str(e)}'}), 500


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP code via Twilio Verify
    """
    try:
        data = request.get_json()
        to = data.get('to')  # Same phone/email used in send-otp
        code = data.get('code')  # 6-digit OTP code

        if not to or not code:
            return jsonify({'error': 'Recipient and code are required'}), 400

        # Verify OTP via Twilio
        result = twilio_verify.verify_otp(to, code)

        if result['success']:
            return jsonify({
                'message': 'OTP verified successfully',
                'status': result['status'],
                'valid': result['valid']
            }), 200
        else:
            return jsonify({
                'error': result.get('error', 'Invalid or expired OTP'),
                'code': result.get('code')
            }), 400

    except Exception as e:
        return jsonify({'error': f'Failed to verify OTP: {str(e)}'}), 500


@auth_bp.route('/register-with-otp', methods=['POST'])
def register_with_otp():
    """
    Register a new user with OTP verification
    Step 1: Send OTP to phone/email
    Step 2: Verify OTP and create account
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone')  # Optional: E.164 format
        otp_code = data.get('otp_code')  # Required if phone provided

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # If phone provided, verify OTP first
        if phone:
            if not otp_code:
                return jsonify({'error': 'OTP code required for phone verification'}), 400

            # Verify OTP
            verify_result = twilio_verify.verify_otp(phone, otp_code)
            if not verify_result['success']:
                return jsonify({'error': 'Invalid or expired OTP'}), 400

        # Proceed with registration
        db = get_db()
        cur = db.cursor()

        # Check if user exists
        cur.execute('SELECT id FROM users WHERE username = ?', (email,))
        if cur.fetchone():
            return jsonify({'error': 'User already exists'}), 400

        # Create user
        password_hash = generate_password_hash(password)
        cur.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (email, password_hash)
        )
        db.commit()

        user_id = cur.lastrowid

        # Generate tokens
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)

        return jsonify({
            'message': 'Registration successful',
            'token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_id,
                'email': email,
                'phone_verified': bool(phone and otp_code)
            }
        }), 201

    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@auth_bp.route('/forgot-password-otp', methods=['POST'])
def forgot_password_otp():
    """
    SECURE Password reset with Twilio OTP
    Step 1: User provides email → System looks up registered phone → Sends OTP
    Step 2: User verifies OTP → Resets password
    """
    try:
        data = request.get_json()
        email = data.get('email')
        otp_code = data.get('otp_code')
        new_password = data.get('new_password')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        db = get_db()
        cur = db.cursor()

        # Get user and their registered phone
        cur.execute('SELECT id, phone FROM users WHERE username = ?', (email,))
        user = cur.fetchone()

        if not user:
            # For security, don't reveal if email exists
            return jsonify({'message': 'If this email exists and has a phone number, an OTP has been sent'}), 200

        phone = user['phone']

        if not phone:
            return jsonify({'error': 'No phone number registered for this account. Please contact support.'}), 400

        # If OTP code provided, verify and reset password
        if otp_code and new_password:
            # Verify OTP
            verify_result = twilio_verify.verify_otp(phone, otp_code)
            if not verify_result['success']:
                return jsonify({'error': 'Invalid or expired OTP'}), 400

            # Reset password
            password_hash = generate_password_hash(new_password)
            cur.execute(
                'UPDATE users SET password_hash = ? WHERE id = ?',
                (password_hash, user['id'])
            )
            db.commit()

            return jsonify({'message': 'Password reset successfully'}), 200

        # Otherwise, send OTP to user's registered phone
        else:
            send_result = twilio_verify.send_otp(phone, 'sms')
            if send_result['success']:
                # Mask phone number for security (show last 4 digits)
                masked_phone = phone[:-4] + '****' if len(phone) > 4 else '****'
                return jsonify({
                    'message': f'OTP sent to your registered phone ending in {phone[-4:]}',
                    'phone_hint': masked_phone,
                    'status': send_result['status']
                }), 200
            else:
                return jsonify({'error': 'Failed to send OTP. Please try again.'}), 400

    except Exception as e:
        return jsonify({'error': f'Failed: {str(e)}'}), 500
