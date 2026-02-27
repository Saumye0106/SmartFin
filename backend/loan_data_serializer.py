"""
Loan_Data_Parser & Serializer - JSON parsing and serialization for loan data
Handles conversion between JSON and Python objects for API requests/responses
"""

import json
import copy
from datetime import datetime
from typing import Dict, Any, Optional


class ParseError(Exception):
    """Custom exception for parsing errors"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class LoanDataSerializer:
    """Handles parsing and serialization of loan data"""
    
    @staticmethod
    def parseLoanJSON(json_string: str) -> Dict[str, Any]:
        """
        Parse JSON string into Loan object
        
        Args:
            json_string: JSON string containing loan data
        
        Returns:
            Dictionary containing parsed loan data
        
        Raises:
            ParseError: If JSON is malformed or validation fails
        
        Validates:
            - All required fields present
            - Date strings in ISO 8601 format
            - Numeric values are valid numbers
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON: {str(e)}")
        
        # Required fields for loan
        required_fields = [
            'loan_type', 'loan_amount', 'loan_tenure', 'monthly_emi',
            'interest_rate', 'loan_start_date', 'loan_maturity_date'
        ]
        
        # Check for missing required fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ParseError(
                f"Missing required fields: {', '.join(missing_fields)}",
                field=missing_fields[0]
            )
        
        # Parse and validate loan_type
        if not isinstance(data['loan_type'], str):
            raise ParseError("loan_type must be a string", field='loan_type')
        
        # Parse and validate numeric fields
        try:
            loan_amount = float(data['loan_amount'])
            data['loan_amount'] = loan_amount
        except (ValueError, TypeError):
            raise ParseError("loan_amount must be a valid number", field='loan_amount')
        
        try:
            loan_tenure = int(data['loan_tenure'])
            data['loan_tenure'] = loan_tenure
        except (ValueError, TypeError):
            raise ParseError("loan_tenure must be a valid integer", field='loan_tenure')
        
        try:
            monthly_emi = float(data['monthly_emi'])
            data['monthly_emi'] = monthly_emi
        except (ValueError, TypeError):
            raise ParseError("monthly_emi must be a valid number", field='monthly_emi')
        
        try:
            interest_rate = float(data['interest_rate'])
            data['interest_rate'] = interest_rate
        except (ValueError, TypeError):
            raise ParseError("interest_rate must be a valid number", field='interest_rate')
        
        # Parse and validate date fields
        try:
            # Convert ISO 8601 date strings to datetime objects, then back to ISO format
            start_date = datetime.fromisoformat(data['loan_start_date'].replace('Z', '+00:00'))
            data['loan_start_date'] = start_date.isoformat()
        except (ValueError, AttributeError, TypeError):
            raise ParseError(
                "loan_start_date must be in ISO 8601 format",
                field='loan_start_date'
            )
        
        try:
            maturity_date = datetime.fromisoformat(data['loan_maturity_date'].replace('Z', '+00:00'))
            data['loan_maturity_date'] = maturity_date.isoformat()
        except (ValueError, AttributeError, TypeError):
            raise ParseError(
                "loan_maturity_date must be in ISO 8601 format",
                field='loan_maturity_date'
            )
        
        # Parse optional fields if present
        if 'default_status' in data:
            if isinstance(data['default_status'], bool):
                pass  # Already boolean
            elif isinstance(data['default_status'], int):
                data['default_status'] = bool(data['default_status'])
            else:
                raise ParseError("default_status must be a boolean", field='default_status')
        
        return data
    
    @staticmethod
    def parsePaymentJSON(json_string: str) -> Dict[str, Any]:
        """
        Parse JSON string into Payment object
        
        Args:
            json_string: JSON string containing payment data
        
        Returns:
            Dictionary containing parsed payment data
        
        Raises:
            ParseError: If JSON is malformed or validation fails
        
        Validates:
            - All required fields present
            - Date strings in ISO 8601 format
            - Numeric values are valid numbers
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON: {str(e)}")
        
        # Required fields for payment
        required_fields = ['payment_date', 'payment_amount']
        
        # Check for missing required fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ParseError(
                f"Missing required fields: {', '.join(missing_fields)}",
                field=missing_fields[0]
            )
        
        # Parse and validate payment_date
        try:
            payment_date = datetime.fromisoformat(data['payment_date'].replace('Z', '+00:00'))
            data['payment_date'] = payment_date.isoformat()
        except (ValueError, AttributeError, TypeError):
            raise ParseError(
                "payment_date must be in ISO 8601 format",
                field='payment_date'
            )
        
        # Parse and validate payment_amount
        try:
            payment_amount = float(data['payment_amount'])
            data['payment_amount'] = payment_amount
        except (ValueError, TypeError):
            raise ParseError("payment_amount must be a valid number", field='payment_amount')
        
        return data
    
    @staticmethod
    def serializeLoan(loan: Dict[str, Any]) -> str:
        """
        Serialize Loan object to JSON string
        
        Args:
            loan: Dictionary containing loan data
        
        Returns:
            JSON string representation of loan
        
        Formats:
            - Dates as ISO 8601 strings
            - Numeric values with appropriate precision
            - Includes calculated fields if present
        """
        # Create a copy to avoid modifying the original
        loan_data = loan.copy()
        
        # Format dates as ISO 8601 strings (if they're datetime objects)
        for date_field in ['loan_start_date', 'loan_maturity_date', 'created_at', 'updated_at', 'deleted_at']:
            if date_field in loan_data and loan_data[date_field] is not None:
                if isinstance(loan_data[date_field], datetime):
                    loan_data[date_field] = loan_data[date_field].isoformat()
        
        # Format numeric values with appropriate precision
        if 'loan_amount' in loan_data:
            loan_data['loan_amount'] = round(float(loan_data['loan_amount']), 2)
        
        if 'monthly_emi' in loan_data:
            loan_data['monthly_emi'] = round(float(loan_data['monthly_emi']), 2)
        
        if 'interest_rate' in loan_data:
            loan_data['interest_rate'] = round(float(loan_data['interest_rate']), 2)
        
        # Calculate and include months_remaining if maturity_date is present
        if 'loan_maturity_date' in loan_data and loan_data['loan_maturity_date'] is not None:
            try:
                maturity_date = datetime.fromisoformat(
                    loan_data['loan_maturity_date'].replace('Z', '+00:00')
                )
                current_date = datetime.utcnow()
                months_remaining = (
                    (maturity_date.year - current_date.year) * 12 +
                    (maturity_date.month - current_date.month)
                )
                loan_data['months_remaining'] = max(0, months_remaining)
            except (ValueError, AttributeError):
                # If date parsing fails, skip calculated field
                pass
        
        return json.dumps(loan_data, indent=2)
    
    @staticmethod
    def serializePayment(payment: Dict[str, Any]) -> str:
        """
        Serialize Payment object to JSON string
        
        Args:
            payment: Dictionary containing payment data
        
        Returns:
            JSON string representation of payment
        
        Formats:
            - Dates as ISO 8601 strings
            - Numeric values with appropriate precision
        """
        # Create a copy to avoid modifying the original
        payment_data = payment.copy()
        
        # Format dates as ISO 8601 strings (if they're datetime objects)
        for date_field in ['payment_date', 'created_at', 'updated_at']:
            if date_field in payment_data and payment_data[date_field] is not None:
                if isinstance(payment_data[date_field], datetime):
                    payment_data[date_field] = payment_data[date_field].isoformat()
        
        # Format numeric values with appropriate precision
        if 'payment_amount' in payment_data:
            payment_data['payment_amount'] = round(float(payment_data['payment_amount']), 2)
        
        return json.dumps(payment_data, indent=2)
    
    @staticmethod
    def serializeLoanMetrics(metrics: Dict[str, Any]) -> str:
        """
        Serialize LoanMetrics object to JSON string
        
        Args:
            metrics: Dictionary containing loan metrics data
        
        Returns:
            JSON string representation of metrics
        
        Formats:
            - Numeric values with 2 decimal places
            - Nested statistics objects
        """
        # Create a deep copy to avoid modifying the original (including nested dicts)
        metrics_data = copy.deepcopy(metrics)
        
        # Format score values with 2 decimal places
        for score_field in ['loan_diversity_score', 'payment_history_score', 'loan_maturity_score']:
            if score_field in metrics_data and metrics_data[score_field] is not None:
                metrics_data[score_field] = round(float(metrics_data[score_field]), 2)
        
        # Format payment statistics if present
        if 'payment_statistics' in metrics_data:
            stats = metrics_data['payment_statistics']
            if 'on_time_payment_percentage' in stats:
                stats['on_time_payment_percentage'] = round(float(stats['on_time_payment_percentage']), 2)
        
        # Format loan statistics if present
        if 'loan_statistics' in metrics_data:
            stats = metrics_data['loan_statistics']
            if 'total_loan_amount' in stats:
                stats['total_loan_amount'] = round(float(stats['total_loan_amount']), 2)
            if 'average_loan_tenure' in stats:
                stats['average_loan_tenure'] = round(float(stats['average_loan_tenure']), 2)
            if 'weighted_average_tenure' in stats:
                stats['weighted_average_tenure'] = round(float(stats['weighted_average_tenure']), 2)
            if 'loan_type_distribution' in stats:
                for loan_type in stats['loan_type_distribution']:
                    stats['loan_type_distribution'][loan_type] = round(
                        float(stats['loan_type_distribution'][loan_type]), 2
                    )
        
        # Format calculated_at timestamp if present
        if 'calculated_at' in metrics_data and metrics_data['calculated_at'] is not None:
            if isinstance(metrics_data['calculated_at'], datetime):
                metrics_data['calculated_at'] = metrics_data['calculated_at'].isoformat()
        
        return json.dumps(metrics_data, indent=2)
