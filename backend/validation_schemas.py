"""
Validation schemas for User Profile Management
Using Marshmallow for request validation
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import date
import re


class ProfileCreateSchema(Schema):
    """Schema for creating a new user profile"""
    name = fields.Str(
        required=True,
        validate=validate.Regexp(
            r'^[A-Za-z\s]{2,100}$',
            error='Name must contain only letters and spaces (2-100 characters)'
        )
    )
    age = fields.Int(
        required=True,
        validate=validate.Range(
            min=18,
            max=120,
            error='Age must be between 18 and 120'
        )
    )
    location = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=200,
            error='Location must be between 1 and 200 characters'
        )
    )
    risk_tolerance = fields.Int(
        validate=validate.Range(
            min=1,
            max=10,
            error='Risk tolerance must be between 1 and 10'
        ),
        allow_none=True
    )
    notification_preferences = fields.Dict(allow_none=True)
    
    @validates('notification_preferences')
    def validate_notification_preferences(self, value):
        """Validate notification preferences structure"""
        if value is None:
            return
        
        valid_frequencies = ['immediate', 'daily', 'weekly']
        
        if 'frequency' in value and value['frequency'] not in valid_frequencies:
            raise ValidationError(
                f'Frequency must be one of: {", ".join(valid_frequencies)}'
            )


class ProfileUpdateSchema(Schema):
    """Schema for updating an existing user profile"""
    name = fields.Str(
        validate=validate.Regexp(
            r'^[A-Za-z\s]{2,100}$',
            error='Name must contain only letters and spaces (2-100 characters)'
        )
    )
    age = fields.Int(
        validate=validate.Range(
            min=18,
            max=120,
            error='Age must be between 18 and 120'
        )
    )
    location = fields.Str(
        validate=validate.Length(
            min=1,
            max=200,
            error='Location must be between 1 and 200 characters'
        )
    )
    risk_tolerance = fields.Int(
        validate=validate.Range(
            min=1,
            max=10,
            error='Risk tolerance must be between 1 and 10'
        )
    )
    notification_preferences = fields.Dict()
    
    @validates('notification_preferences')
    def validate_notification_preferences(self, value):
        """Validate notification preferences structure"""
        if value is None:
            return
        
        valid_frequencies = ['immediate', 'daily', 'weekly']
        
        if 'frequency' in value and value['frequency'] not in valid_frequencies:
            raise ValidationError(
                f'Frequency must be one of: {", ".join(valid_frequencies)}'
            )


class GoalCreateSchema(Schema):
    """Schema for creating a new financial goal"""
    goal_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            ['short-term', 'long-term'],
            error='Goal type must be either "short-term" or "long-term"'
        )
    )
    target_amount = fields.Float(
        required=True,
        validate=validate.Range(
            min=0.01,
            error='Target amount must be greater than 0'
        )
    )
    target_date = fields.Date(required=True)
    priority = fields.Str(
        required=True,
        validate=validate.OneOf(
            ['low', 'medium', 'high'],
            error='Priority must be one of: low, medium, high'
        )
    )
    description = fields.Str(
        validate=validate.Length(
            max=500,
            error='Description must be 500 characters or less'
        ),
        allow_none=True
    )
    
    @validates('target_date')
    def validate_future_date(self, value):
        """Ensure target date is in the future"""
        if value <= date.today():
            raise ValidationError('Target date must be in the future')


class GoalUpdateSchema(Schema):
    """Schema for updating an existing financial goal"""
    target_amount = fields.Float(
        validate=validate.Range(
            min=0.01,
            error='Target amount must be greater than 0'
        )
    )
    target_date = fields.Date()
    priority = fields.Str(
        validate=validate.OneOf(
            ['low', 'medium', 'high'],
            error='Priority must be one of: low, medium, high'
        )
    )
    status = fields.Str(
        validate=validate.OneOf(
            ['active', 'completed', 'cancelled'],
            error='Status must be one of: active, completed, cancelled'
        )
    )
    description = fields.Str(
        validate=validate.Length(
            max=500,
            error='Description must be 500 characters or less'
        )
    )
    
    @validates('target_date')
    def validate_future_date(self, value):
        """Ensure target date is in the future (if provided)"""
        if value and value <= date.today():
            raise ValidationError('Target date must be in the future')


# Create schema instances for reuse
profile_create_schema = ProfileCreateSchema()
profile_update_schema = ProfileUpdateSchema()
goal_create_schema = GoalCreateSchema()
goal_update_schema = GoalUpdateSchema()


def validate_request_data(schema, data):
    """
    Validate request data against a schema
    
    Args:
        schema: Marshmallow schema instance
        data: Dictionary of data to validate
    
    Returns:
        tuple: (validated_data, errors)
            validated_data: Cleaned and validated data (None if errors)
            errors: Dictionary of validation errors (None if valid)
    """
    try:
        validated_data = schema.load(data)
        return validated_data, None
    except ValidationError as err:
        return None, err.messages
