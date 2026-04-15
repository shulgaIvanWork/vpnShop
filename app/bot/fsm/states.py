"""
FSM States definition for payment flow.
"""

from enum import Enum


class PaymentStates(Enum):
    """States for payment process."""
    
    IDLE = "idle"  # No active payment
    CHOOSING_PLAN = "choosing_plan"  # User is selecting a plan
    CHOOSING_PAYMENT_METHOD = "choosing_payment_method"  # Selecting payment method
    WAITING_FOR_COUPON = "waiting_for_coupon"  # User is entering coupon code
    WAITING_FOR_RECEIPT = "waiting_for_receipt"  # Waiting for payment receipt
    PAYMENT_PENDING = "payment_pending"  # Payment submitted, waiting for admin approval
    PAYMENT_COMPLETED = "payment_completed"  # Payment approved and subscription activated
