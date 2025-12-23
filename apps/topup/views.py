
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.notification.utils import create_notification
from apps.transaction.utils import create_transaction
from .models import Topup
import decimal, random
import requests

class TopupView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        amount = request.data.get("amount")
        card_holder_name = request.data.get("card_holder_name")
        payment_method_id = request.data.get("stripe_payment_method")
        
        
        if not amount or not card_holder_name:
            return Response({
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Missing required fields",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
            
        transaction = create_transaction(
            user = request.user,
            status = "failed",
            category = "topup",
            amount = amount,
            description = f"Topup of {amount} from {card_holder_name}",
            purpose = "Topup",
            payment_method = "balance"
        )
        
        payment_url = "https://hsblco.com/api/top-up"

        payload = {
            "amount": amount,
            "payment_method_id": payment_method_id,  
            "user": {
                "id": str(request.user.id),
                "name": f"{request.user.profile.first_name} {request.user.profile.last_name}",
                "email": request.user.email,
                "stripe_customer_id": request.user.stripe_customer_id or None
            }
        }

        api_response = requests.post(payment_url, json=payload)
        response_data = api_response.json()

        payment_intent = response_data.get("payment_intent", {})

        payment_id = payment_intent.get("id", "")
        payment_status = payment_intent.get("status", "failed")
        client_secret = payment_intent.get("client_secret", "")
        if payment_status == "succeeded":
            status_ = "pending"
            Topup.objects.create(
            transaction=transaction,
            payment_id=payment_id,
            client_secret=client_secret,
            status=status_
        )
        else:
            status_ = "failed"
        
        transaction.status = status_
        transaction.save()
        
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": f"Your top-up of {transaction.amount} is processing. Please wait.",
            "data": None
        }, status=status.HTTP_200_OK)
        
        
        
        
class PaymentWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payment_id = request.data.get("payment_id")
        payment_status = request.data.get("status")

        if not payment_id or not payment_status:
            return Response({
                "status": "error", 
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Missing required fields",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            topup = Topup.objects.select_related(
                "transaction",
                "transaction__user",
                "transaction__user__profile"
            ).get(payment_id=payment_id)
        except Topup.DoesNotExist:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "Topup not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        # Do not re-process completed/failed transactions
        if topup.status != "pending":
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Already processed",
                "data": None
            })

        transaction = topup.transaction
        user_profile = transaction.user.profile
        amount = transaction.amount
        user_id = transaction.user.id

        # Notification messages for success
        success_messages = [
            f"Your top-up of {amount} was successful! Thanks for choosing our service.",
            f"You’ve added {amount} to your balance successfully. We appreciate having you with us!",
            f"Top-up of {amount} completed! Thank you for using our service.",
            f"Great news! Your account has been topped up with {amount}.",
            f"Your balance increased by {amount}. Thank you for staying with us!",
        ]

        # Handlers for each status
        handlers = {
            "payment_intent.succeeded": {
                "topup_status": "completed",
                "txn_status": "completed",
                "balance_add": amount,
                "notify_title": "Topup Successful",
                "notify_message": random.choice(success_messages)
            },
            "payment_intent.payment_failed": {
                "topup_status": "failed",
                "txn_status": "failed",
                "notify_title": "Topup Failed",
                "notify_message": f"Your top-up of {amount} failed. Please try again."
            },
            "payment_intent.canceled": {
                "topup_status": "cancelled",
                "txn_status": "cancelled",
                "notify_title": "Topup Cancelled",
                "notify_message": f"Your top-up of {amount} was cancelled. Please try again."
            },
            "payment_intent.processing": {
                "topup_status": "pending",
                "txn_status": "pending",
                "notify_title": "Topup Processing",
                "notify_message": f"Your top-up of {amount} is processing. Please wait."
            },
            "payment_intent.created": None  # Do nothing
        }

        action = handlers.get(payment_status)

        # Unknown status
        if action is None and payment_status != "payment_intent.created":
            action = {
                "topup_status": "failed",
                "txn_status": "failed",
                "notify_title": "Topup Failed",
                "notify_message": f"Unknown status received for top-up of {amount}. Marked as failed."
            }

        # Only update if action exists (not created)
        if action:
            topup.status = action["topup_status"]
            transaction.status = action["txn_status"]

            # Add balance only on success
            if "balance_add" in action:
                user_profile.balance += action["balance_add"]
                user_profile.save()

            transaction.save()
            topup.save()

            # Send notification
            create_notification(
                user_id=user_id,
                title=action["notify_title"],
                message=action["notify_message"],
            )

        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Webhook processed successfully",
            "data": None
        })
