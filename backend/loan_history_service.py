"""
Loan_History_System - Business logic for loan history management
Handles CRUD operations, validation, and payment tracking for loans
"""

import sqlite3
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, field: str, message: str, code: str = "VALIDATION_ERROR"):
        self.field = field
        self.message = message
        self.code = code
        super().__init__(f"{field}: {message}")


class LoanHistoryService:
    """Service class for managing loan history and payments"""
    
    def __init__(self, db_path: str):
        """
        Initialize LoanHistoryService
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _row_to_dict(self, row) -> Optional[Dict[str, Any]]:
        """Convert SQLite row to dictionary"""
        if row is None:
            return None
        return dict(row)
    
    def validateLoanData(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate loan data according to business rules
        
        Args:
            loan_data: Dictionary containing loan information
        
        Returns:
            Dictionary with validation results: {'isValid': bool, 'errors': list}
        
        Validates:
            - All required fields present
            - Data types correct
            - Business logic (amounts, dates, EMI calculation)
        """
        errors = []
        
        # Required fields
        required_fields = [
            'loan_type', 'loan_amount', 'loan_tenure', 'monthly_emi',
            'interest_rate', 'loan_start_date', 'loan_maturity_date'
        ]
        
        for field in required_fields:
            if field not in loan_data or loan_data[field] is None:
                errors.append({
                    'field': field,
                    'message': f'{field} is required',
                    'code': 'REQUIRED_FIELD'
                })
        
        if errors:
            return {'isValid': False, 'errors': errors}
        
        # Validate loan_type
        valid_loan_types = ['personal', 'home', 'auto', 'education']
        if loan_data['loan_type'] not in valid_loan_types:
            errors.append({
                'field': 'loan_type',
                'message': f'Loan type must be one of: {", ".join(valid_loan_types)}',
                'code': 'INVALID_LOAN_TYPE'
            })
        
        # Validate loan_amount
        try:
            loan_amount = float(loan_data['loan_amount'])
            if loan_amount <= 0:
                errors.append({
                    'field': 'loan_amount',
                    'message': 'Loan amount must be positive',
                    'code': 'INVALID_AMOUNT'
                })
        except (ValueError, TypeError):
            errors.append({
                'field': 'loan_amount',
                'message': 'Loan amount must be a valid number',
                'code': 'INVALID_TYPE'
            })
        
        # Validate loan_tenure
        try:
            loan_tenure = int(loan_data['loan_tenure'])
            if loan_tenure <= 0:
                errors.append({
                    'field': 'loan_tenure',
                    'message': 'Loan tenure must be positive',
                    'code': 'INVALID_TENURE'
                })
        except (ValueError, TypeError):
            errors.append({
                'field': 'loan_tenure',
                'message': 'Loan tenure must be a valid integer',
                'code': 'INVALID_TYPE'
            })
        
        # Validate interest_rate
        try:
            interest_rate = float(loan_data['interest_rate'])
            if interest_rate < 0 or interest_rate > 50:
                errors.append({
                    'field': 'interest_rate',
                    'message': 'Interest rate must be between 0 and 50 percent',
                    'code': 'INVALID_INTEREST_RATE'
                })
        except (ValueError, TypeError):
            errors.append({
                'field': 'interest_rate',
                'message': 'Interest rate must be a valid number',
                'code': 'INVALID_TYPE'
            })
        
        # Validate monthly_emi
        try:
            monthly_emi = float(loan_data['monthly_emi'])
            if monthly_emi <= 0:
                errors.append({
                    'field': 'monthly_emi',
                    'message': 'Monthly EMI must be positive',
                    'code': 'INVALID_EMI'
                })
        except (ValueError, TypeError):
            errors.append({
                'field': 'monthly_emi',
                'message': 'Monthly EMI must be a valid number',
                'code': 'INVALID_TYPE'
            })
        
        # Validate dates
        try:
            start_date = datetime.fromisoformat(loan_data['loan_start_date'].replace('Z', '+00:00'))
            maturity_date = datetime.fromisoformat(loan_data['loan_maturity_date'].replace('Z', '+00:00'))
            
            # Ensure both dates are timezone-aware (if naive, assume UTC)
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if maturity_date.tzinfo is None:
                maturity_date = maturity_date.replace(tzinfo=timezone.utc)
            
            if maturity_date <= start_date:
                errors.append({
                    'field': 'loan_maturity_date',
                    'message': 'Loan maturity date must be after loan start date',
                    'code': 'INVALID_DATE_RANGE'
                })
        except (ValueError, TypeError) as e:
            errors.append({
                'field': 'loan_start_date',
                'message': 'Invalid date format. Use ISO 8601 format',
                'code': 'INVALID_DATE_FORMAT'
            })
        
        # Validate EMI calculation (if no errors so far)
        if not errors:
            try:
                loan_amount = float(loan_data['loan_amount'])
                loan_tenure = int(loan_data['loan_tenure'])
                interest_rate = float(loan_data['interest_rate'])
                monthly_emi = float(loan_data['monthly_emi'])
                
                # Calculate expected EMI using amortization formula
                # EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)
                # where P = principal, r = monthly interest rate, n = number of months
                
                if interest_rate > 0:
                    monthly_rate = interest_rate / 100 / 12
                    expected_emi = (loan_amount * monthly_rate * math.pow(1 + monthly_rate, loan_tenure)) / \
                                   (math.pow(1 + monthly_rate, loan_tenure) - 1)
                else:
                    # Zero interest rate
                    expected_emi = loan_amount / loan_tenure
                
                # Allow 1% tolerance for rounding differences
                tolerance = expected_emi * 0.01
                if abs(monthly_emi - expected_emi) > tolerance:
                    errors.append({
                        'field': 'monthly_emi',
                        'message': f'Monthly EMI does not match loan parameters (expected: {expected_emi:.2f})',
                        'code': 'EMI_MISMATCH'
                    })
            except Exception as e:
                # Skip EMI validation if calculation fails
                pass
        
        return {
            'isValid': len(errors) == 0,
            'errors': errors
        }
    
    def createLoan(self, user_id: int, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new loan record
        
        Args:
            user_id: ID of the user
            loan_data: Dictionary containing loan information
        
        Returns:
            Dictionary containing the created loan
        
        Raises:
            ValidationError: If validation fails
            sqlite3.Error: For database errors
        """
        logger.info(f"Creating loan for user {user_id}")
        
        # Validate loan data
        validation_result = self.validateLoanData(loan_data)
        if not validation_result['isValid']:
            error = validation_result['errors'][0]
            logger.warning(f"Loan validation failed for user {user_id}: {error['message']}")
            raise ValidationError(error['field'], error['message'], error['code'])
        
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Generate unique loan ID
            loan_id = str(uuid.uuid4())
            
            # Get current timestamp (timezone-aware)
            now = datetime.now(timezone.utc).isoformat()
            
            # Insert loan
            cur.execute('''
                INSERT INTO loans 
                (loan_id, user_id, loan_type, loan_amount, loan_tenure, monthly_emi,
                 interest_rate, loan_start_date, loan_maturity_date, default_status,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                loan_id,
                user_id,
                loan_data['loan_type'],
                float(loan_data['loan_amount']),
                int(loan_data['loan_tenure']),
                float(loan_data['monthly_emi']),
                float(loan_data['interest_rate']),
                loan_data['loan_start_date'],
                loan_data['loan_maturity_date'],
                0,  # default_status = False
                now,
                now
            ))
            
            conn.commit()
            logger.info(f"Loan created successfully: {loan_id} for user {user_id}")
            
            # Retrieve and return the created loan
            return self.getLoan(loan_id)
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error creating loan for user {user_id}: {str(e)}")
            raise
        finally:
            conn.close()
    
    def getLoan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific loan by ID
        
        Args:
            loan_id: ID of the loan
        
        Returns:
            Dictionary containing loan data, or None if not found
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute('''
                SELECT loan_id, user_id, loan_type, loan_amount, loan_tenure,
                       monthly_emi, interest_rate, loan_start_date, loan_maturity_date,
                       default_status, created_at, updated_at, deleted_at
                FROM loans
                WHERE loan_id = ?
            ''', (loan_id,))
            
            row = cur.fetchone()
            return self._row_to_dict(row)
            
        finally:
            conn.close()
    
    def getLoansByUser(self, user_id: int, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve all loans for a user
        
        Args:
            user_id: ID of the user
            include_deleted: Whether to include soft-deleted loans
        
        Returns:
            List of loan dictionaries
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            query = '''
                SELECT loan_id, user_id, loan_type, loan_amount, loan_tenure,
                       monthly_emi, interest_rate, loan_start_date, loan_maturity_date,
                       default_status, created_at, updated_at, deleted_at
                FROM loans
                WHERE user_id = ?
            '''
            
            if not include_deleted:
                query += ' AND deleted_at IS NULL'
            
            query += ' ORDER BY created_at DESC'
            
            cur.execute(query, (user_id,))
            rows = cur.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def updateLoan(self, loan_id: str, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing loan with ownership check
        
        Args:
            loan_id: ID of the loan
            user_id: ID of the user (for ownership verification)
            updates: Dictionary containing fields to update
        
        Returns:
            Dictionary containing the updated loan
        
        Raises:
            ValueError: If loan doesn't exist, user doesn't own it, or loan is closed/defaulted
            ValidationError: If validation fails
            sqlite3.Error: For database errors
        """
        logger.info(f"Updating loan {loan_id} for user {user_id}")
        
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Check if loan exists and belongs to user
            existing_loan = self.getLoan(loan_id)
            if existing_loan is None:
                logger.warning(f"Loan not found: {loan_id}")
                raise ValueError(f'Loan not found: {loan_id}')
            
            if existing_loan['user_id'] != user_id:
                logger.warning(f"User {user_id} attempted to update loan {loan_id} owned by user {existing_loan['user_id']}")
                raise ValueError(f'User {user_id} does not own loan {loan_id}')
            
            # Check if loan is deleted
            if existing_loan['deleted_at'] is not None:
                logger.warning(f"Attempted to update deleted loan: {loan_id}")
                raise ValueError(f'Cannot update deleted loan: {loan_id}')
            
            # Check if loan is in default
            if existing_loan['default_status']:
                logger.warning(f"Attempted to update loan in default: {loan_id}")
                raise ValueError(f'Cannot update loan in default: {loan_id}')
            
            # Validate updates if they include critical fields
            if any(field in updates for field in ['loan_amount', 'loan_tenure', 'monthly_emi', 'interest_rate']):
                # Merge updates with existing data for validation
                loan_data = {**existing_loan, **updates}
                validation_result = self.validateLoanData(loan_data)
                if not validation_result['isValid']:
                    error = validation_result['errors'][0]
                    logger.warning(f"Loan update validation failed for {loan_id}: {error['message']}")
                    raise ValidationError(error['field'], error['message'], error['code'])
            
            # Build UPDATE query dynamically
            update_fields = []
            update_values = []
            
            allowed_fields = [
                'loan_type', 'loan_amount', 'loan_tenure', 'monthly_emi',
                'interest_rate', 'loan_start_date', 'loan_maturity_date', 'default_status'
            ]
            
            for field in allowed_fields:
                if field in updates:
                    update_fields.append(f'{field} = ?')
                    update_values.append(updates[field])
            
            if not update_fields:
                # No fields to update, return existing loan
                logger.info(f"No fields to update for loan {loan_id}")
                return existing_loan
            
            # Always update the updated_at timestamp
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now(timezone.utc).isoformat())
            
            # Add loan_id to values for WHERE clause
            update_values.append(loan_id)
            
            # Execute update
            query = f'''
                UPDATE loans
                SET {', '.join(update_fields)}
                WHERE loan_id = ?
            '''
            
            cur.execute(query, update_values)
            conn.commit()
            logger.info(f"Loan updated successfully: {loan_id}")
            
            # Retrieve and return updated loan
            return self.getLoan(loan_id)
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error updating loan {loan_id}: {str(e)}")
            raise
        finally:
            conn.close()
    
    def deleteLoan(self, loan_id: str, user_id: int) -> bool:
        """
        Soft delete a loan with ownership check
        Sets deleted_at timestamp instead of removing the record
        
        Args:
            loan_id: ID of the loan
            user_id: ID of the user (for ownership verification)
        
        Returns:
            True if loan was deleted, False if not found
        
        Raises:
            ValueError: If user doesn't own the loan
        """
        logger.info(f"Deleting loan {loan_id} for user {user_id}")
        
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Check if loan exists and belongs to user
            existing_loan = self.getLoan(loan_id)
            if existing_loan is None:
                logger.warning(f"Loan not found for deletion: {loan_id}")
                return False
            
            if existing_loan['user_id'] != user_id:
                logger.warning(f"User {user_id} attempted to delete loan {loan_id} owned by user {existing_loan['user_id']}")
                raise ValueError(f'User {user_id} does not own loan {loan_id}')
            
            # Soft delete by setting deleted_at timestamp
            now = datetime.now(timezone.utc).isoformat()
            cur.execute('''
                UPDATE loans
                SET deleted_at = ?, updated_at = ?
                WHERE loan_id = ?
            ''', (now, now, loan_id))
            
            conn.commit()
            logger.info(f"Loan deleted successfully: {loan_id}")
            
            return cur.rowcount > 0
            
        except sqlite3.Error as e:
            logger.error(f"Database error deleting loan {loan_id}: {str(e)}")
            raise
        finally:
            conn.close()
    
    def recordPayment(self, loan_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a loan payment with validation and status classification
        
        Args:
            loan_id: ID of the loan
            payment_data: Dictionary containing payment information
                - payment_date: str (ISO format date)
                - payment_amount: float (> 0)
        
        Returns:
            Dictionary containing the created payment
        
        Raises:
            ValidationError: If validation fails
            ValueError: If loan doesn't exist
            sqlite3.Error: For database errors
        """
        logger.info(f"Recording payment for loan {loan_id}")
        
        # Validate payment data
        errors = []
        
        # Required fields
        if 'payment_date' not in payment_data:
            errors.append({
                'field': 'payment_date',
                'message': 'payment_date is required',
                'code': 'REQUIRED_FIELD'
            })
        
        if 'payment_amount' not in payment_data:
            errors.append({
                'field': 'payment_amount',
                'message': 'payment_amount is required',
                'code': 'REQUIRED_FIELD'
            })
        
        if errors:
            error = errors[0]
            logger.warning(f"Payment validation failed for loan {loan_id}: {error['message']}")
            raise ValidationError(error['field'], error['message'], error['code'])
        
        # Validate payment_date
        try:
            payment_date = datetime.fromisoformat(payment_data['payment_date'].replace('Z', '+00:00'))
            
            # Ensure payment_date is timezone-aware (if naive, assume UTC)
            if payment_date.tzinfo is None:
                payment_date = payment_date.replace(tzinfo=timezone.utc)
            
            # Make utcnow timezone-aware for comparison
            utc_now = datetime.now(timezone.utc)
            
            logger.info(f"Payment date: {payment_date} (tzinfo: {payment_date.tzinfo})")
            logger.info(f"UTC now: {utc_now} (tzinfo: {utc_now.tzinfo})")
            
            # Note: We don't validate against future dates because of timezone differences
            # Users in different timezones may have valid reasons to record payments with dates
            # that appear to be in the future in UTC
        except ValidationError:
            raise
        except ValueError as e:
            logger.error(f"Invalid date format for loan {loan_id}: {payment_data.get('payment_date')}")
            raise ValidationError('payment_date', 'Invalid date format. Use ISO 8601 format', 'INVALID_DATE_FORMAT')
        except TypeError as e:
            logger.error(f"TypeError comparing datetimes for loan {loan_id}: {str(e)}")
            raise ValidationError('payment_date', 'Invalid date format. Use ISO 8601 format', 'INVALID_DATE_FORMAT')
        
        # Validate payment_amount
        try:
            payment_amount = float(payment_data['payment_amount'])
            if payment_amount <= 0:
                logger.warning(f"Invalid payment amount for loan {loan_id}: {payment_amount}")
                raise ValidationError('payment_amount', 'Payment amount must be positive', 'INVALID_AMOUNT')
        except (ValueError, TypeError):
            logger.error(f"Invalid payment amount type for loan {loan_id}")
            raise ValidationError('payment_amount', 'Payment amount must be a valid number', 'INVALID_TYPE')
        
        # Check if loan exists
        loan = self.getLoan(loan_id)
        if loan is None:
            logger.error(f"Loan not found: {loan_id}")
            raise ValueError(f'Loan not found: {loan_id}')
        
        # Calculate total payments made so far
        existing_payments = self.getPaymentHistory(loan_id)
        total_paid = sum(float(p['payment_amount']) for p in existing_payments)
        
        # Calculate remaining balance
        loan_amount = float(loan['loan_amount'])
        remaining_balance = loan_amount - total_paid
        
        # Check if payment exceeds remaining balance
        if payment_amount > remaining_balance + 0.01:  # Allow small rounding tolerance
            logger.warning(f"Payment exceeds remaining balance for loan {loan_id}: {payment_amount} > {remaining_balance}")
            raise ValidationError(
                'payment_amount',
                f'Payment amount exceeds remaining balance (remaining: {remaining_balance:.2f})',
                'EXCEEDS_BALANCE'
            )
        
        # Calculate payment status (on-time, late, missed)
        # Based on expected monthly EMI due date
        loan_start = datetime.fromisoformat(loan['loan_start_date'].replace('Z', '+00:00'))
        
        # Ensure loan_start is timezone-aware (if naive, assume UTC)
        if loan_start.tzinfo is None:
            loan_start = loan_start.replace(tzinfo=timezone.utc)
        
        # Calculate the expected due date for this payment
        # Due date is the same day each month as the loan start date
        # For example, if loan starts on 15th, EMI is due on 15th of each month
        
        # Get the number of payments made so far (including this one)
        num_payments_made = len(existing_payments) + 1
        
        # Calculate expected due date: loan_start_date + (num_payments_made * 1 month)
        # We use the day of the month from loan_start_date
        loan_start_day = loan_start.day
        loan_start_month = loan_start.month
        loan_start_year = loan_start.year
        
        # Calculate the month and year for the expected due date
        due_month = loan_start_month + num_payments_made - 1
        due_year = loan_start_year
        
        # Handle month overflow
        while due_month > 12:
            due_month -= 12
            due_year += 1
        
        # Handle day overflow (e.g., Feb 31st doesn't exist)
        try:
            expected_due_date = datetime(due_year, due_month, loan_start_day, tzinfo=timezone.utc).date()
        except ValueError:
            # If day doesn't exist in that month, use last day of month
            from calendar import monthrange
            last_day = monthrange(due_year, due_month)[1]
            expected_due_date = datetime(due_year, due_month, last_day, tzinfo=timezone.utc).date()
        
        payment_date_only = payment_date.date()
        
        # Classify payment status based on days overdue
        days_overdue = (payment_date_only - expected_due_date).days
        
        if days_overdue <= 0:
            # Payment made on or before due date
            payment_status = 'on-time'
        elif days_overdue <= 30:
            # Payment made 1-30 days after due date
            payment_status = 'late'
        else:
            # Payment made more than 30 days after due date
            payment_status = 'missed'
        
        logger.info(f"Payment status calculation for loan {loan_id}: "
                   f"expected_due_date={expected_due_date}, "
                   f"payment_date={payment_date_only}, "
                   f"days_overdue={days_overdue}, "
                   f"status={payment_status}")
        
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Generate unique payment ID
            payment_id = str(uuid.uuid4())
            
            # Get current timestamp (timezone-aware)
            now = datetime.now(timezone.utc).isoformat()
            
            # Insert payment
            cur.execute('''
                INSERT INTO loan_payments
                (payment_id, loan_id, payment_date, payment_amount, payment_status,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                payment_id,
                loan_id,
                payment_data['payment_date'],
                payment_amount,
                payment_status,
                now,
                now
            ))
            
            conn.commit()
            logger.info(f"Payment recorded successfully: {payment_id} for loan {loan_id}")
            
            # Retrieve and return the created payment
            cur.execute('''
                SELECT payment_id, loan_id, payment_date, payment_amount,
                       payment_status, created_at, updated_at
                FROM loan_payments
                WHERE payment_id = ?
            ''', (payment_id,))
            
            row = cur.fetchone()
            return self._row_to_dict(row)
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error recording payment for loan {loan_id}: {str(e)}")
            raise
        finally:
            conn.close()
    
    def getPaymentHistory(self, loan_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve payment history for a loan
        
        Args:
            loan_id: ID of the loan
        
        Returns:
            List of payment dictionaries sorted by payment_date
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute('''
                SELECT payment_id, loan_id, payment_date, payment_amount,
                       payment_status, created_at, updated_at
                FROM loan_payments
                WHERE loan_id = ?
                ORDER BY payment_date ASC
            ''', (loan_id,))
            
            rows = cur.fetchall()
            return [self._row_to_dict(row) for row in rows]
            
        finally:
            conn.close()

    def deletePayment(self, payment_id: str, loan_id: str) -> bool:
        """
        Delete a payment record
        
        Args:
            payment_id: ID of the payment to delete
            loan_id: ID of the loan (for verification)
        
        Returns:
            True if payment was deleted, False if not found
        
        Raises:
            ValueError: If payment doesn't belong to the loan
            sqlite3.Error: For database errors
        """
        logger.info(f"Deleting payment {payment_id} for loan {loan_id}")
        
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Verify payment belongs to the loan
            cur.execute('''
                SELECT payment_id, loan_id FROM loan_payments
                WHERE payment_id = ?
            ''', (payment_id,))
            
            row = cur.fetchone()
            if row is None:
                logger.warning(f"Payment not found: {payment_id}")
                return False
            
            payment = self._row_to_dict(row)
            if payment['loan_id'] != loan_id:
                logger.warning(f"Payment {payment_id} does not belong to loan {loan_id}")
                raise ValueError(f'Payment does not belong to loan {loan_id}')
            
            # Delete the payment
            cur.execute('''
                DELETE FROM loan_payments
                WHERE payment_id = ?
            ''', (payment_id,))
            
            conn.commit()
            logger.info(f"Payment deleted successfully: {payment_id}")
            
            return cur.rowcount > 0
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error deleting payment {payment_id}: {str(e)}")
            raise
        finally:
            conn.close()
