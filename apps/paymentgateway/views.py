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
from . utils import create_shurjopay_payment
from django.contrib.auth import get_user_model
User = get_user_model() 


# Default merchant info from settings
merchantId = settings.PAYSTATION_MERCHANT_ID
password = settings.PAYSTATION_PASSWORD
callback_url = settings.PAYSTATION_CALLBACK_URL

def initiate_payment(amount, invoice_number, customer_name, customer_email, customer_phone, reference=None, checkout_items=None):
    payload = {
        "merchantId": merchantId,
        "password": password,
        "invoice_number": invoice_number,
        "currency": "BDT",
        "payment_amount": int(amount),
        "cust_name": customer_name,
        "cust_phone": customer_phone,
        "cust_email": customer_email,
        "callback_url": callback_url,
    }
    if reference:
        payload["reference"] = reference
    if checkout_items:
        payload["checkout_items"] = json.dumps(checkout_items)

    try:
        response = requests.post(
            f"{settings.PAYSTATION_BASE_URL}/initiate-payment",
                headers={"Content-Type": "application/json", "merchantId": settings.PAYSTATION_MERCHANT_ID},
                json=payload,
                timeout=30
        )
        
        if not response.text:
            return {"status": "error", "message": "Empty response from PayStation API"}
        return response.json()
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Connection timed out"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}
    except ValueError:
        return {"status": "error", "message": "Invalid JSON response", "content": response.text}

# --------------------------
# Initiate Payment
# --------------------------
class InitiatePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        first_name = getattr(user, "first_name", "")
        last_name = getattr(user, "last_name", "")
        email = getattr(user, "email", "")
        phone = getattr(user.profile, "phone", "") if hasattr(user, "profile") else ""

        invoice_number = str(uuid.uuid4()).replace("-", "")[:20]
        amount = 500  # Example, can be dynamic
        reference = f"ORDER-{invoice_number}"
        checkout_items = {"product": "Auto Payment Item"}

        payment = Payment.objects.create(
            user=user,
            invoice_number=invoice_number,
            amount=amount,
            customer_name=f"{first_name} {last_name}".strip(),
            customer_phone=phone,
            customer_email=email
        )

        gateway_response = initiate_payment(
            amount=payment.amount,
            invoice_number=payment.invoice_number,
            customer_name=payment.customer_name,
            customer_email=payment.customer_email,
            customer_phone=payment.customer_phone,
            reference=reference,
            checkout_items=checkout_items
        )

        if gateway_response.get("status") == "success":
            return Response(gateway_response, status=status.HTTP_200_OK)
        else:
            return Response(gateway_response, status=status.HTTP_400_BAD_REQUEST)

# Payment Callback
class PaymentCallbackAPIView(APIView):

    def get(self, request):
        status_param = request.GET.get("status")
        invoice_number = request.GET.get("invoice_number")
        trx_id = request.GET.get("trx_id")

        if not invoice_number:
            return Response({"error": "invoice_number missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(invoice_number=invoice_number)
        except Payment.DoesNotExist:
            return Response({"error": "Invalid invoice number"}, status=status.HTTP_400_BAD_REQUEST)

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
        return Response({"message": "Payment callback processed"}, status=status.HTTP_200_OK)

# Transaction Status by Invoice
class TransactionStatusAPIView(APIView):

    def post(self, request):
        invoice_number = request.data.get("invoice_number")
        if not invoice_number:
            return Response({"error": "invoice_number is required"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {"merchantId": settings.PAYSTATION_MERCHANT_ID}
        payload = {"invoice_number": invoice_number}

        response = requests.post(
            headers={"Content-Type": "application/json", "merchantId": settings.PAYSTATION_MERCHANT_ID},
            json=payload,
            timeout=30
        )

        return Response(response.json(), status=response.status_code)

# Transaction Status by Trx ID
class TransactionStatusByTrxAPIView(APIView):

    def post(self, request):
        trx_id = request.data.get("trxId")
        if not trx_id:
            return Response({"error": "trxId is required"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "merchantId": settings.PAYSTATION_MERCHANT_ID,
            "Content-Type": "application/json"
        }
        payload = {"trxId": trx_id}

        response = requests.post(
            f"{settings.PAYSTATION_BASE_URL}/v2/transaction-status",
                headers={"Content-Type": "application/json", "merchantId": settings.PAYSTATION_MERCHANT_ID},
                json=payload,
                timeout=30
        )

        return Response(response.json(), status=response.status_code)



#---------------=================-----------
#Shurjopay
#---------------=================-----------

class ShurjopayPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        invoice = f"ORD-{uuid.uuid4().hex[:10]}"

        payment = Payment.objects.create(
            user=user,
            invoice_number=invoice,
            amount=1000.00,
            customer_name=f"{user.account.first_name} {user.account.last_name}",
            customer_phone="01830232488",
            customer_email=user.email,
            status="pending"
        )

        response = create_shurjopay_payment(
            amount=payment.amount,
            order_id=payment.invoice_number,
            customer_name=payment.customer_name,
            customer_address="Mirpur, Dhaka",
            customer_email=payment.customer_email,
            customer_phone=payment.customer_phone,
            customer_city="Dhaka",
        )

        return Response(response)
    
class ShurjopayReturnAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or request.query_params

        order_id = data.get("order_id")
        sp_code = data.get("sp_code")

        if not order_id:
            return Response(
                {"error": "order_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.objects.get(invoice_number=order_id)
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update payment status directly (no verification)
        if sp_code == "1000":
            payment.status = "success"
        elif sp_code == "1002":
            payment.status = "canceled"
        else:
            payment.status = "failed"

        payment.trx_id = data.get("bank_trx_id")
        payment.save()

        # Return response in ShurjoPay-like format
        return Response(
            [
                {
                    "id": data.get("id"),
                    "order_id": data.get("order_id"),
                    "currency": data.get("currency"),
                    "amount": data.get("amount"),
                    "payable_amount": data.get("payable_amount"),
                    "discount_amount": data.get("discount_amount"),
                    "disc_percent": data.get("disc_percent"),
                    "recived_amount": data.get("recived_amount"),
                    "usd_amt": data.get("usd_amt"),
                    "usd_rate": data.get("usd_rate"),
                    "card_holder_name": data.get("card_holder_name"),
                    "card_number": data.get("card_number"),
                    "phone_no": data.get("phone_no"),
                    "bank_trx_id": data.get("bank_trx_id"),
                    "invoice_no": data.get("invoice_no"),
                    "bank_status": data.get("bank_status"),
                    "customer_order_id": data.get("customer_order_id"),
                    "sp_code": data.get("sp_code"),
                    "sp_massage": data.get("sp_massage"),
                    "sp_message": data.get("sp_message"),
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "address": data.get("address"),
                    "city": data.get("city"),
                    "value1": data.get("value1"),
                    "value2": data.get("value2"),
                    "value3": data.get("value3"),
                    "value4": data.get("value4"),
                    "transaction_status": data.get("transaction_status"),
                    "method": data.get("method"),
                    "date_time": data.get("date_time"),
                }
            ],
            status=status.HTTP_200_OK
        )

    def get(self, request):
        return self.post(request)

class ShurjopayCancelAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or request.query_params
        order_id = data.get("order_id")

        if order_id:
            Payment.objects.filter(
                invoice_number=order_id
            ).update(status="canceled")

        return Response(
            {
                "message": "Payment cancelled",
                "order_id": order_id,
                "currency": "BDT",
                "transaction_status": "Cancelled"
            },
            status=status.HTTP_200_OK
        )

    def get(self, request):
        return self.post(request)

