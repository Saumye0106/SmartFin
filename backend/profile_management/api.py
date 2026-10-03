"""
Profile + Goals Blueprint
User profile CRUD, profile picture upload/delete, and financial goals CRUD.
"""

import os
import uuid

from flask import Blueprint, request, jsonify, current_app, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

import file_storage
from db_core import DB_PATH
from profile_service import ProfileService
from goals_service import GoalsService
from validation_schemas import (
    profile_create_schema,
    profile_update_schema,
    goal_create_schema,
    goal_update_schema,
    validate_request_data,
)

profile_bp = Blueprint('profile', __name__)

profile_service = ProfileService(DB_PATH)
goals_service = GoalsService(DB_PATH)


MAX_PICTURE_BYTES = 5 * 1024 * 1024


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


# ==================== PROFILE ENDPOINTS ====================

@profile_bp.route('/api/profile/create', methods=['POST'])
@jwt_required()
def create_profile():
    """
    Create a new user profile
    Requires: JWT authentication
    Body: name, age, location, risk_tolerance (optional), notification_preferences (optional)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        # Validate request data
        validated_data, errors = validate_request_data(profile_create_schema, data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400

        # Check if profile already exists
        if profile_service.profile_exists(user_id):
            return jsonify({'error': 'Profile already exists for this user'}), 409

        # Create profile
        profile = profile_service.create_profile(user_id, validated_data)

        return jsonify({
            'message': 'Profile created successfully',
            'profile': profile
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@profile_bp.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get the authenticated user's profile
    Requires: JWT authentication
    """
    try:
        user_id = int(get_jwt_identity())

        # Get profile
        profile = profile_service.get_profile(user_id)

        if profile is None:
            return jsonify({'error': 'Profile not found'}), 404

        return jsonify({
            'profile': profile
        }), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@profile_bp.route('/api/profile/update', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update the authenticated user's profile
    Requires: JWT authentication
    Body: name, age, location, risk_tolerance, notification_preferences (all optional)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        # Validate request data
        validated_data, errors = validate_request_data(profile_update_schema, data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400

        # Update profile
        profile = profile_service.update_profile(user_id, validated_data)

        return jsonify({
            'message': 'Profile updated successfully',
            'profile': profile
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


# ==================== PROFILE PICTURE UPLOAD ENDPOINTS ====================

@profile_bp.route('/api/profile/upload-picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    """
    Upload profile picture
    Requires: JWT authentication
    Body: multipart/form-data with 'file' field
    """
    try:
        user_id = int(get_jwt_identity())

        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format. Allowed: JPEG, PNG, WebP'}), 400

        # Pictures are capped at 5 MB (the app-wide request limit is higher, for statement uploads)
        file.stream.seek(0, os.SEEK_END)
        if file.stream.tell() > MAX_PICTURE_BYTES:
            return jsonify({'error': 'Picture is larger than 5 MB'}), 413
        file.stream.seek(0)

        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"user_{user_id}_{uuid.uuid4().hex}.{file_extension}"
        storage = file_storage.get_storage()   # a folder locally, S3 when SMARTFIN_UPLOADS_BUCKET is set

        # Delete old profile picture if exists
        profile = profile_service.get_profile(user_id)
        if profile and profile.get('profile_picture_url'):
            old_filename = profile['profile_picture_url'].split('/')[-1]
            if file_storage.is_valid_name(old_filename):
                storage.delete(old_filename)

        # Save file
        storage.save(filename, file.stream)

        # Generate URL for the file
        picture_url = f"/uploads/profile_pictures/{filename}"

        # Update profile with picture URL
        profile_service.update_profile(user_id, {'profile_picture_url': picture_url})

        return jsonify({
            'message': 'Profile picture uploaded successfully',
            'profile_picture_url': picture_url
        }), 200

    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@profile_bp.route('/api/profile/delete-picture', methods=['DELETE'])
@jwt_required()
def delete_profile_picture():
    """
    Delete profile picture
    Requires: JWT authentication
    """
    try:
        user_id = int(get_jwt_identity())

        # Get current profile
        profile = profile_service.get_profile(user_id)

        if not profile or not profile.get('profile_picture_url'):
            return jsonify({'error': 'No profile picture to delete'}), 404

        # Delete the stored file
        filename = profile['profile_picture_url'].split('/')[-1]
        if file_storage.is_valid_name(filename):
            file_storage.get_storage().delete(filename)

        # Update profile to remove picture URL
        profile_service.update_profile(user_id, {'profile_picture_url': None})

        return jsonify({
            'message': 'Profile picture deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500


@profile_bp.route('/uploads/profile_pictures/<filename>')
def serve_profile_picture(filename):
    """Serve profile picture files"""
    if not file_storage.is_valid_name(filename):
        abort(404)
    return file_storage.get_storage().response(filename)


# ==================== GOALS ENDPOINTS ====================

@profile_bp.route('/api/profile/goals', methods=['POST'])
@jwt_required()
def create_goal():
    """
    Create a new financial goal
    Requires: JWT authentication
    Body: goal_type, target_amount, target_date, priority, description (optional)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        # Validate request data
        validated_data, errors = validate_request_data(goal_create_schema, data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400

        # Create goal
        goal = goals_service.create_goal(user_id, validated_data)

        return jsonify({
            'message': 'Goal created successfully',
            'goal': goal
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@profile_bp.route('/api/profile/goals', methods=['GET'])
@jwt_required()
def get_goals():
    """
    Get all financial goals for the authenticated user
    Requires: JWT authentication
    Query params: status (optional filter)
    """
    try:
        user_id = int(get_jwt_identity())

        # Get optional status filter
        status = request.args.get('status')
        filters = {'status': status} if status else None

        # Get goals
        goals = goals_service.get_goals(user_id, filters)

        return jsonify({
            'goals': goals,
            'count': len(goals)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@profile_bp.route('/api/profile/goals/<goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    """
    Update a financial goal
    Requires: JWT authentication + ownership
    Body: goal_type, target_amount, target_date, priority, status, description (all optional)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        # Validate request data
        validated_data, errors = validate_request_data(goal_update_schema, data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400

        # Update goal (includes ownership check)
        goal = goals_service.update_goal(goal_id, user_id, validated_data)

        return jsonify({
            'message': 'Goal updated successfully',
            'goal': goal
        }), 200

    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return jsonify({'error': error_msg}), 404
        elif 'not authorized' in error_msg.lower() or 'does not belong' in error_msg.lower():
            return jsonify({'error': 'Not authorized to update this goal'}), 403
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@profile_bp.route('/api/profile/goals/<goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    """
    Delete a financial goal
    Requires: JWT authentication + ownership
    """
    try:
        user_id = int(get_jwt_identity())

        # Delete goal (includes ownership check)
        success = goals_service.delete_goal(goal_id, user_id)

        if success:
            return jsonify({
                'message': 'Goal deleted successfully'
            }), 204
        else:
            return jsonify({'error': 'Goal not found'}), 404

    except ValueError as e:
        error_msg = str(e)
        if 'not authorized' in error_msg.lower() or 'does not belong' in error_msg.lower():
            return jsonify({'error': 'Not authorized to delete this goal'}), 403
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
