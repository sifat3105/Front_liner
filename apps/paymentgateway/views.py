import requests
import uuid
from django.conf import settings
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import response, status
from rest_framework.permissions import AllowAny
from .models import Payment
from .serializers import PaymentSerializer
import json
from django.contrib.auth import get_user_model
User = get_user_model() 


# Default merchant info from settings
merchantId = settings.PAYSTATION_MERCHANT_ID
password = settings.PAYSTATION_PASSWORD
callback_url = settings.PAYSTATION_CALLBACK_URL

# function for Pay Station
def initiate_payment(amount, invoice_number, customer_name, customer_email, customer_phone, reference=None, checkout_items=None):

    payment_amount = int(amount)

    payload = {
        "merchantId": merchantId,
        "password": password,
        "invoice_number": invoice_number,
        "currency": "BDT",
        "payment_amount": payment_amount,
        "cust_name": customer_name,
        "cust_phone": customer_phone,
        "cust_email": customer_email,
        "callback_url": callback_url,
    }

    if reference:
        payload["reference"] = reference

    if checkout_items:
        payload["checkout_items"] = json.dumps(checkout_items)

    response = requests.post(
        f"{settings.PAYSTATION_BASE_URL}/initiate-payment",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    try:
        return response.json()
    except Exception:
        return {"status": "error", "message": "Invalid response", "content": response.text}

# ============================
# Initiate Payment for registered user
# ============================

class InitiatePaymentAPIView(APIView):

    def post(self, request):
        user_id = request.data.get("user_id")
        User = get_user_model()
        try:
            user = request.user
        except User.DoesNotExist:
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)
        invoice_number = str(uuid.uuid4()).replace('-', '')[:20]
        amount = 500 
        reference = f"ORDER-{invoice_number}"
        checkout_items = {"product": "Auto Payment Item"}

        payment = Payment.objects.create(
            user=user,
            invoice_number=invoice_number,
            amount=amount,
            customer_name=f"{user.account.first_name} {user.account.last_name}",
            customer_phone=user.profile.phone if hasattr(user, 'profile') else "",
            customer_email=user.email
        )

        # Call reusable initiate_payment function
        gateway_response = initiate_payment(
            amount=payment.amount,
            invoice_number=payment.invoice_number,
            customer_name=payment.customer_name,
            customer_email=payment.customer_email,
            customer_phone=payment.customer_phone,
            reference=reference,
            checkout_items=checkout_items
        )

        # Return PayStation response directly
        if gateway_response.get("status") == "success":
            return Response(gateway_response, status=status.HTTP_200_OK)
        else:
            return Response(gateway_response, status=status.HTTP_400_BAD_REQUEST)


# PayStation Callback
class PaymentCallbackAPIView(APIView):

    def get(self, request):
        status_param = request.GET.get("status")
        invoice_number = request.GET.get("invoice_number")
        trx_id = request.GET.get("trx_id")

        if not invoice_number:
            return Response(
                {"error": "invoice_number missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.objects.get(invoice_number=invoice_number)
        except Payment.DoesNotExist:
            return Response(
                {"error": "Invalid invoice number"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Status mapping as per PayStation doc
        if status_param == "Successful":
            payment.status = "success"
            payment.trx_id = trx_id
        elif status_param == "Failed":
            payment.status = "failed"
        elif status_param == "Canceled":
            payment.status = "canceled"
        else:
            payment.status = "unknown"

        payment.save()

        return Response(
            {"message": "Payment callback processed"},
            status=status.HTTP_200_OK
        )



# Transaction Status (Invoice)
class TransactionStatusAPIView(APIView):

    def post(self, request):
        invoice_number = request.data.get("invoice_number")

        if not invoice_number:
            return Response(
                {"error": "invoice_number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        headers = {
            "merchantId": merchantId
        }

        payload = {
            "invoice_number": invoice_number
        }

        response = requests.post(
            f"{settings.PAYSTATION_BASE_URL}/transaction-status",
            headers=headers,
            data=payload,
            timeout=30
        )

        return Response(response.json(), status=response.status_code)


# Transaction Status (Trx ID)
class TransactionStatusByTrxAPIView(APIView):

    def post(self, request):
        trx_id = request.data.get("trxId")

        if not trx_id:
            return Response(
                {"error": "trxId is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        headers = {
            "merchantId": merchantId,
            "Content-Type": "application/json"
        }

        payload = {
            "trxId": trx_id
        }

        response = requests.post(
            f"{settings.PAYSTATION_BASE_URL}/v2/transaction-status",
            headers=headers,
            json=payload,
            timeout=30
        )

        return Response(response.json(), status=response.status_code)



#---------------=================----------
#Shurjopay
#---------------=================----------



from . utils import create_shurjopay_payment


class ShurjopayPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get("user_id")
        User = get_user_model()
        try:
            user = request.user
        except User.DoesNotExist:
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)
        
        response = create_shurjopay_payment(
                amount =1000.00,
                order_id= "ORD-1001",
                customer_name= "Rahim Uddin",
                customer_address="Mirpur, Dhaka",
                customer_email="rahim@example.com",
                customer_phone= "01830232488",
                customer_city="Dhaka",

        )

        return Response(response)
    

class ShurjopayReturnAPIView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        """
        This API will be called by ShurjoPay after successful payment
        """
        data = request.data or request.query_params

        # Example data you may receive:
        # order_id, transaction_id, status, amount, etc.

        return Response(
            {
                "message": "Payment successful",
                "payment_data": data,
            },
            status=status.HTTP_200_OK
        )

    def get(self, request):
        # Some gateways send GET request
        return self.post(request)


class ShurjopayCancelAPIView(APIView):
    permission_classes = [AllowAny]  # ShurjoPay will hit this URL

    def post(self, request):
        """
        This API will be called by ShurjoPay if payment is cancelled
        """
        data = request.data or request.query_params

        return Response(
            {
                "message": "Payment cancelled",
                "payment_data": data,
            },
            status=status.HTTP_200_OK
        )

    def get(self, request):
        return self.post(request)
