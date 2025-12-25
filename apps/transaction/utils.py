from .models import Transaction
import uuid


def generate_transaction_id():
    return str(uuid.uuid4())

def create_transaction(user, status, category,  amount,
                       description=None, purpose=None, payment_method=None):
    if status not in dict(Transaction._meta.get_field('status').choices):
        raise ValueError("Invalid status value")
    if category not in dict(Transaction._meta.get_field('category').choices):
        raise ValueError("Invalid category value")
    if payment_method not in dict(Transaction._meta.get_field('payment_method').choices):
        raise ValueError("Invalid payment method value")
    transaction = Transaction.objects.create(
        user=user,
        status=status,
        category=category,
        transaction_id=generate_transaction_id(),
        amount=amount,
        description=description,
        purpose=purpose,
        payment_method=payment_method
    )
    return transaction