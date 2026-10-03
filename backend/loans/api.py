"""
Loans Blueprint
Loan CRUD, payment recording/history, and cached loan metrics.
"""

import json
import sqlite3
import logging
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from db_core import DB_PATH, get_db, row_to_dict
from loan_history_service import LoanHistoryService, ValidationError as LoanValidationError
from loan_metrics_engine import LoanMetricsEngine
from loan_data_serializer import LoanDataSerializer, ParseError

logger = logging.getLogger(__name__)

loans_bp = Blueprint('loans', __name__)

loan_service = LoanHistoryService(DB_PATH)
loan_metrics = LoanMetricsEngine(DB_PATH)
loan_serializer = LoanDataSerializer()


@loans_bp.route('/api/loans', methods=['POST'])
@jwt_required()
def create_loan():
    """
    Create a new loan record
    Requires: JWT authentication
    Body: loan_type, loan_amount, loan_tenure, monthly_emi, interest_rate,
          loan_start_date, loan_maturity_date
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        # Log request
        logger.info(f"Create loan request from user {user_id}")

        # Validate request body exists
        if not data:
            logger.warning(f"Empty request body from user {user_id}")
            return jsonify({
                'error': 'Request body is required',
                'message': 'Please provide loan data in JSON format'
            }), 400

        # Validate and create loan
        loan = loan_service.createLoan(user_id, data)

        logger.info(f"Loan created successfully: {loan['loan_id']} for user {user_id}")
        return jsonify({
            'message': 'Loan created successfully',
            'loan': loan
        }), 201

    except LoanValidationError as e:
        logger.warning(f"Loan validation failed for user {user_id}: {e.message}")
        return jsonify({
            'error': 'Validation failed',
            'field': e.field,
            'message': e.message,
            'code': e.code
        }), 400
    except sqlite3.Error as e:
        logger.error(f"Database error creating loan for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to create loan. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error creating loan for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@loans_bp.route('/api/loans/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_loans(user_id):
    """
    Get all loans for a specific user
    Requires: JWT authentication + ownership check
    """
    try:
        current_user_id = int(get_jwt_identity())

        # Check ownership - users can only access their own loans
        if current_user_id != user_id:
            logger.warning(f"User {current_user_id} attempted to access loans for user {user_id}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to access this user\'s loans'
            }), 403

        # Get loans
        loans = loan_service.getLoansByUser(user_id)

        logger.info(f"Retrieved {len(loans)} loans for user {user_id}")
        return jsonify({
            'loans': loans,
            'count': len(loans)
        }), 200

    except sqlite3.Error as e:
        logger.error(f"Database error retrieving loans for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to retrieve loans. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving loans for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@loans_bp.route('/api/loans/<loan_id>', methods=['GET'])
@jwt_required()
def get_loan(loan_id):
    """
    Get specific loan details with payment history
    Requires: JWT authentication + ownership check
    """
    try:
        current_user_id = int(get_jwt_identity())

        # Get loan
        loan = loan_service.getLoan(loan_id)

        if loan is None:
            logger.warning(f"Loan not found: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Loan not found'
            }), 404

        # Check ownership
        if loan['user_id'] != current_user_id:
            logger.warning(f"User {current_user_id} attempted to access loan {loan_id} owned by user {loan['user_id']}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to access this loan'
            }), 403

        # Get payment history
        payments = loan_service.getPaymentHistory(loan_id)

        # Add payments to loan data
        loan['payments'] = payments

        logger.info(f"Retrieved loan {loan_id} for user {current_user_id}")
        return jsonify({
            'loan': loan
        }), 200

    except sqlite3.Error as e:
        logger.error(f"Database error retrieving loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to retrieve loan. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@loans_bp.route('/api/loans/<loan_id>', methods=['PUT'])
@jwt_required()
def update_loan(loan_id):
    """
    Update loan information
    Requires: JWT authentication + ownership check
    Body: Fields to update (loan_type, loan_amount, etc.)
    """
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        # Validate request body exists
        if not data:
            logger.warning(f"Empty request body for loan update: {loan_id}")
            return jsonify({
                'error': 'Request body is required',
                'message': 'Please provide fields to update in JSON format'
            }), 400

        # Update loan (includes ownership check)
        loan = loan_service.updateLoan(loan_id, current_user_id, data)

        logger.info(f"Loan updated successfully: {loan_id} by user {current_user_id}")
        return jsonify({
            'message': 'Loan updated successfully',
            'loan': loan
        }), 200

    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            logger.warning(f"Loan not found for update: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': error_msg
            }), 404
        elif 'does not own' in error_msg.lower():
            logger.warning(f"User {current_user_id} attempted to update loan {loan_id} without ownership")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to update this loan'
            }), 403
        elif 'deleted' in error_msg.lower() or 'default' in error_msg.lower():
            logger.warning(f"Attempted to update deleted/defaulted loan: {loan_id}")
            return jsonify({
                'error': 'Bad request',
                'message': error_msg
            }), 400
        return jsonify({
            'error': 'Bad request',
            'message': error_msg
        }), 400
    except LoanValidationError as e:
        logger.warning(f"Loan update validation failed for {loan_id}: {e.message}")
        return jsonify({
            'error': 'Validation failed',
            'field': e.field,
            'message': e.message,
            'code': e.code
        }), 400
    except sqlite3.Error as e:
        logger.error(f"Database error updating loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to update loan. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error updating loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@loans_bp.route('/api/loans/<loan_id>', methods=['DELETE'])
@jwt_required()
def delete_loan(loan_id):
    """
    Soft delete a loan
    Requires: JWT authentication + ownership check
    """
    try:
        current_user_id = int(get_jwt_identity())

        # Delete loan (includes ownership check)
        success = loan_service.deleteLoan(loan_id, current_user_id)

        if success:
            logger.info(f"Loan deleted successfully: {loan_id} by user {current_user_id}")
            return jsonify({
                'message': 'Loan deleted successfully',
                'success': True
            }), 200
        else:
            logger.warning(f"Loan not found for deletion: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Loan not found'
            }), 404

    except ValueError as e:
        error_msg = str(e)
        if 'does not own' in error_msg.lower():
            logger.warning(f"User {current_user_id} attempted to delete loan {loan_id} without ownership")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to delete this loan'
            }), 403
        return jsonify({
            'error': 'Bad request',
            'message': error_msg
        }), 400
    except sqlite3.Error as e:
        logger.error(f"Database error deleting loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to delete loan. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error deleting loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@loans_bp.route('/api/loans/<loan_id>/payments', methods=['POST'])
@jwt_required()
def record_payment(loan_id):
    """
    Record a loan payment
    Requires: JWT authentication + loan ownership check
    Body: payment_date, payment_amount
    """
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        logger.info(f"Recording payment - loan_id: {loan_id}, data: {data}")

        # Validate request body exists
        if not data:
            logger.warning(f"Empty request body for payment recording: {loan_id}")
            return jsonify({
                'error': 'Request body is required',
                'message': 'Please provide payment data in JSON format'
            }), 400

        # Check loan exists and user owns it
        loan = loan_service.getLoan(loan_id)
        if loan is None:
            logger.warning(f"Loan not found for payment: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Loan not found'
            }), 404

        if loan['user_id'] != current_user_id:
            logger.warning(f"User {current_user_id} attempted to record payment for loan {loan_id} owned by user {loan['user_id']}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to record payment for this loan'
            }), 403

        # Record payment
        payment = loan_service.recordPayment(loan_id, data)

        logger.info(f"Payment recorded successfully: {payment['payment_id']} for loan {loan_id}")
        return jsonify({
            'message': 'Payment recorded successfully',
            'payment': payment
        }), 201

    except LoanValidationError as e:
        logger.warning(f"Payment validation failed for loan {loan_id}: {e.message}")
        return jsonify({
            'error': 'Validation failed',
            'field': e.field,
            'message': e.message,
            'code': e.code
        }), 400
    except ValueError as e:
        logger.error(f"Value error recording payment for loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Not found',
            'message': str(e)
        }), 404
    except sqlite3.Error as e:
        logger.error(f"Database error recording payment for loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to record payment. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error recording payment for loan {loan_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@loans_bp.route('/api/loans/<loan_id>/payments', methods=['GET'])
@jwt_required()
def get_payment_history(loan_id):
    """
    Get payment history for a loan
    Requires: JWT authentication + loan ownership check
    """
    try:
        current_user_id = int(get_jwt_identity())

        # Check loan exists and user owns it
        loan = loan_service.getLoan(loan_id)
        if loan is None:
            logger.warning(f"Loan not found for payment history: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Loan not found'
            }), 404

        if loan['user_id'] != current_user_id:
            logger.warning(f"User {current_user_id} attempted to access payment history for loan {loan_id} owned by user {loan['user_id']}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to access payment history for this loan'
            }), 403

        # Get payment history
        payments = loan_service.getPaymentHistory(loan_id)

        logger.info(f"Retrieved {len(payments)} payments for loan {loan_id}")
        return jsonify({
            'payments': payments,
            'count': len(payments)
        }), 200

    except sqlite3.Error as e:
        logger.error(f"Database error retrieving payment history for loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to retrieve payment history. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving payment history for loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@loans_bp.route('/api/loans/<loan_id>/payments/<payment_id>', methods=['DELETE'])
@jwt_required()
def delete_payment(loan_id, payment_id):
    """
    Delete a payment record
    Requires: JWT authentication + loan ownership check
    """
    try:
        current_user_id = int(get_jwt_identity())

        # Check loan exists and user owns it
        loan = loan_service.getLoan(loan_id)
        if loan is None:
            logger.warning(f"Loan not found for payment deletion: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Loan not found'
            }), 404

        if loan['user_id'] != current_user_id:
            logger.warning(f"User {current_user_id} attempted to delete payment for loan {loan_id} owned by user {loan['user_id']}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to delete payment for this loan'
            }), 403

        # Delete the payment
        deleted = loan_service.deletePayment(payment_id, loan_id)

        if not deleted:
            logger.warning(f"Payment not found for deletion: {payment_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Payment not found'
            }), 404

        logger.info(f"Payment deleted successfully: {payment_id} for loan {loan_id}")
        return jsonify({
            'message': 'Payment deleted successfully',
            'payment_id': payment_id
        }), 200

    except ValueError as e:
        logger.warning(f"Validation error deleting payment {payment_id}: {str(e)}")
        return jsonify({
            'error': 'Validation error',
            'message': str(e)
        }), 400
    except sqlite3.Error as e:
        logger.error(f"Database error deleting payment {payment_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to delete payment. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error deleting payment {payment_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@loans_bp.route('/api/loans/metrics/<int:user_id>', methods=['GET'])
@jwt_required()
def get_loan_metrics(user_id):
    """
    Get calculated loan metrics for a user
    Uses cached metrics if available and recent (within 5 minutes)
    Requires: JWT authentication + ownership check
    Returns: loan_diversity_score, payment_history_score, loan_maturity_score,
             payment_statistics, loan_statistics
    """
    try:
        current_user_id = int(get_jwt_identity())

        # Check ownership - users can only access their own metrics
        if current_user_id != user_id:
            logger.warning(f"User {current_user_id} attempted to access metrics for user {user_id}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to access this user\'s metrics'
            }), 403

        # Check if cached metrics exist and are recent (within 5 minutes)
        db = get_db()
        cur = db.cursor()

        cur.execute('''
            SELECT loan_diversity_score, payment_history_score, loan_maturity_score,
                   payment_statistics, loan_statistics, calculated_at
            FROM loan_metrics
            WHERE user_id = ?
        ''', (user_id,))

        cached_row = cur.fetchone()

        if cached_row:
            cached_data = row_to_dict(cached_row)
            calculated_at = datetime.fromisoformat(cached_data['calculated_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)

            # If cache is less than 5 minutes old, use it
            if (now - calculated_at).total_seconds() < 300:
                logger.info(f"Using cached metrics for user {user_id}")

                # Parse JSON fields
                payment_stats = json.loads(cached_data['payment_statistics']) if cached_data['payment_statistics'] else {}
                loan_stats = json.loads(cached_data['loan_statistics']) if cached_data['loan_statistics'] else {}

                metrics = {
                    'loan_diversity_score': cached_data['loan_diversity_score'],
                    'payment_history_score': cached_data['payment_history_score'],
                    'loan_maturity_score': cached_data['loan_maturity_score'],
                    'payment_statistics': payment_stats,
                    'loan_statistics': loan_stats,
                    'calculated_at': cached_data['calculated_at'],
                    'cached': True
                }

                return jsonify({
                    'metrics': metrics
                }), 200

        # Cache is stale or doesn't exist, recalculate
        logger.info(f"Recalculating metrics for user {user_id}")

        loan_diversity_score = loan_metrics.calculateLoanDiversityScore(user_id)
        payment_history_score = loan_metrics.calculatePaymentHistoryScore(user_id)
        loan_maturity_score = loan_metrics.calculateLoanMaturityScore(user_id)

        # Get statistics
        payment_statistics = loan_metrics.getPaymentStatistics(user_id)
        loan_statistics = loan_metrics.getLoanStatistics(user_id)

        # Store in cache
        now = datetime.now(timezone.utc).isoformat()
        payment_stats_json = json.dumps(payment_statistics)
        loan_stats_json = json.dumps(loan_statistics)

        try:
            cur.execute('''
                INSERT INTO loan_metrics
                (user_id, loan_diversity_score, payment_history_score, loan_maturity_score,
                 payment_statistics, loan_statistics, calculated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (user_id) DO UPDATE SET
                    loan_diversity_score = excluded.loan_diversity_score,
                    payment_history_score = excluded.payment_history_score,
                    loan_maturity_score = excluded.loan_maturity_score,
                    payment_statistics = excluded.payment_statistics,
                    loan_statistics = excluded.loan_statistics,
                    calculated_at = excluded.calculated_at
            ''', (
                user_id,
                loan_diversity_score,
                payment_history_score,
                loan_maturity_score,
                payment_stats_json,
                loan_stats_json,
                now
            ))
            db.commit()
            logger.info(f"Cached metrics for user {user_id}")
        except sqlite3.Error as e:
            logger.warning(f"Failed to cache metrics for user {user_id}: {str(e)}")
            # Continue anyway, just don't cache

        metrics = {
            'loan_diversity_score': loan_diversity_score,
            'payment_history_score': payment_history_score,
            'loan_maturity_score': loan_maturity_score,
            'payment_statistics': payment_statistics,
            'loan_statistics': loan_statistics,
            'calculated_at': now,
            'cached': False
        }

        logger.info(f"Retrieved loan metrics for user {user_id}")
        return jsonify({
            'metrics': metrics
        }), 200

    except sqlite3.Error as e:
        logger.error(f"Database error retrieving metrics for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to retrieve loan metrics. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving metrics for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500
