from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from requests.auth import HTTPBasicAuth
from .models import PaperflyMerchant, PaperflyOrder,PaperflyOrderTracking,PaperflyOrderCancel

# Merchant Registration 
PAPERFLY_URL = "https://api.paperfly.com.bd/MerchantRegistration"
PAPERFLY_KEY = "Paperfly_~La?Rj73FcLm"
USERNAME = "c174391"
PASSWORD = "6263"

class PaperflyRegistrationAPIView(APIView):

    def post(self, request):
        data = request.data

        mandatory_fields = [
            "merchant_name","product_nature","address","thana","district",
            "contact_number","bank_name","bank_branch","payment_mode"
        ]
        missing_fields = [field for field in mandatory_fields if not data.get(field)]
        if missing_fields:
            return Response({"success": False,"message": "Mandatory field missing","missing_fields": missing_fields}, status=status.HTTP_400_BAD_REQUEST)

        # Validate payment mode
        allowed_payment_modes = ["beftn", "cash", "bkash", "rocket", "nagad"]
        if data.get("payment_mode") not in allowed_payment_modes:
            return Response({"success": False,"message": "Invalid payment_mode","allowed_values": allowed_payment_modes}, status=status.HTTP_400_BAD_REQUEST)

        payload = {field: data.get(field) for field in data.keys()}

        headers = {"Content-Type":"application/json","Paperflykey":PAPERFLY_KEY}

        try:
            response = requests.post(PAPERFLY_URL, json=payload, headers=headers, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=30)
        except requests.exceptions.RequestException as e:
            return Response({"success": False,"message": "Paperfly API not reachable","error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save to DB
        PaperflyMerchant.objects.create(
            merchant_name=data.get("merchant_name"),
            product_nature=data.get("product_nature"),
            address=data.get("address"),
            thana=data.get("thana"),
            district=data.get("district"),
            website=data.get("website"),
            facebook=data.get("facebook_page"),
            company_phone=data.get("company_phone"),
            contact_name=data.get("contact_name"),
            designation=data.get("designation"),
            contact_number=data.get("contact_number"),
            email=data.get("email"),
            account_name=data.get("account_name"),
            account_number=data.get("account_number"),
            bank_name=data.get("bank_name"),
            bank_branch=data.get("bank_branch"),
            routing_number=data.get("routing_number"),
            payment_mode=data.get("payment_mode"),
        )

        try:
            return Response(response.json(), status=response.status_code)
        except ValueError:
            return Response({"success": False,"message": "Invalid response from Paperfly"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# order submission integration 
PAPERFLY_ORDER_URL = "https://api.paperfly.com.bd/NewOrderUpload"

class PaperflyOrderCreateAPIView(APIView):

    def post(self, request):
        data = request.data

        mandatory_fields = [
            "merchantCode","merOrderRef","productSizeWeight","packagePrice",
            "deliveryOption","custname","custaddress","customerDistrict","custPhone"
        ]
        missing_fields = [f for f in mandatory_fields if not data.get(f)]
        if missing_fields:
            return Response({
                "success": False,
                "message": "Mandatory field missing",
                "missing_fields": missing_fields
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate productSizeWeight & deliveryOption
        if data.get("productSizeWeight") not in ["standard","large","special"]:
            return Response({
                "success": False,
                "message": "Invalid productSizeWeight",
                "allowed_values": ["standard","large","special"]
            }, status=status.HTTP_400_BAD_REQUEST)

        if data.get("deliveryOption") not in ["regular","express"]:
            return Response({
                "success": False,
                "message": "Invalid deliveryOption",
                "allowed_values": ["regular","express"]
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = {field: data.get(field, "") for field in data.keys()}

        headers = {
            "Content-Type": "application/json",
            "Paperflykey": PAPERFLY_KEY
        }

        # CALL PAPERFLY ORDER CREATE API
        try:
            response = requests.post(
                PAPERFLY_ORDER_URL,
                json=payload,
                headers=headers,
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Paperfly API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # THIS PART YOU ASKED FOR (tracking_number extract)
        try:
            result = response.json()

            tracking_number = None
            if result.get("success"):
                tracking_number = result["success"].get("tracking_number")

            # SAVE ORDER WITH tracking_number
            PaperflyOrder.objects.create(
                merchantCode=data.get("merchantCode"),
                merOrderRef=data.get("merOrderRef"),
                tracking_number=tracking_number,

                pickMerchantName=data.get("pickMerchantName",""),
                pickMerchantAddress=data.get("pickMerchantAddress",""),
                pickMerchantThana=data.get("pickMerchantThana",""),
                pickMerchantDistrict=data.get("pickMerchantDistrict",""),
                pickupMerchantPhone=data.get("pickupMerchantPhone",""),

                productSizeWeight=data.get("productSizeWeight"),
                productBrief=data.get("productBrief",""),

                packagePrice=data.get("packagePrice"),
                deliveryOption=data.get("deliveryOption"),

                custname=data.get("custname"),
                custaddress=data.get("custaddress"),
                customerThana=data.get("customerThana",""),
                customerDistrict=data.get("customerDistrict"),
                custPhone=data.get("custPhone"),

                max_weight=data.get("max_weight",""),
            )

            return Response(result, status=response.status_code)

        except ValueError:
            return Response({
                "success": False,
                "message": "Invalid response from Paperfly"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Order Tracking
PAPERFLY_TRACK_URL = "https://api.paperfly.com.bd/API-Order-Tracking"

class PaperflyOrderTrackingAPIView(APIView):

    def post(self, request):
        data = request.data

        # Mandatory fields check
        mandatory_fields = ["ReferenceNumber", "merchantCode"]
        missing_fields = [f for f in mandatory_fields if not data.get(f)]
        if missing_fields:
            return Response({
                "success": False,
                "message": "Mandatory field missing",
                "missing_fields": missing_fields
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "ReferenceNumber": data.get("ReferenceNumber"),
            "merchantCode": data.get("merchantCode")
        }

        headers = {
            "Content-Type": "application/json",
            "Paperflykey": PAPERFLY_KEY
        }

        try:
            response = requests.post(
                PAPERFLY_TRACK_URL,
                json=payload,
                headers=headers,
                auth=HTTPBasicAuth(USERNAME, ""),  # Password blank if not required
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Paperfly API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            result = response.json()

            if result.get("success") and "trackingStatus" in result["success"]:
                tracking = result["success"]["trackingStatus"][0]  # Assuming first tracking object

                # Save to DB
                PaperflyOrderTracking.objects.create(
                    ReferenceNumber=data.get("ReferenceNumber"),
                    merchantCode=data.get("merchantCode"),
                    Pick=tracking.get("Pick", ""),
                    PickTime=tracking.get("PickTime", ""),
                    inTransit=tracking.get("inTransit", ""),
                    inTransitTime=tracking.get("inTransitTime", ""),
                    ReceivedAtPoint=tracking.get("ReceivedAtPoint", ""),
                    ReceivedAtPointTime=tracking.get("ReceivedAtPointTime", ""),
                    PickedForDelivery=tracking.get("PickedForDelivery", ""),
                    PickedForDeliveryTime=tracking.get("PickedForDeliveryTime", ""),
                    Delivered=tracking.get("Delivered", ""),
                    DeliveredTime=tracking.get("DeliveredTime", ""),
                    Returned=tracking.get("Returned", ""),
                    ReturnedTime=tracking.get("ReturnedTime", ""),
                    Partial=tracking.get("Partial", ""),
                    PartialTime=tracking.get("PartialTime", ""),
                    onHoldSchedule=tracking.get("onHoldSchedule", ""),
                    close=tracking.get("close", ""),
                    closeTime=tracking.get("closeTime", "")
                )

            return Response(result, status=response.status_code)
        except ValueError:
            return Response({
                "success": False,
                "message": "Invalid response from Paperfly"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# order cancellation integration
PAPERFLY_CANCEL_URL = "https://api.paperfly.com.bd/api/v1/cancel-order"

class PaperflyOrderCancelAPIView(APIView):

    def post(self, request):
        data = request.data

        # Mandatory fields
        mandatory_fields = ["order_id", "merchantCode"]
        missing_fields = [f for f in mandatory_fields if not data.get(f)]

        if missing_fields:
            return Response({
                "success": False,
                "message": "Mandatory field missing",
                "missing_fields": missing_fields
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "order_id": data.get("order_id"),
            "merchantCode": data.get("merchantCode")
        }

        headers = {
            "Content-Type": "application/json",
            "Paperflykey": PAPERFLY_KEY
        }

        try:
            response = requests.post(
                PAPERFLY_CANCEL_URL,
                json=payload,
                headers=headers,
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Paperfly API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            result = response.json()

            # Save cancel log to DB
            PaperflyOrderCancel.objects.create(
                order_id=data.get("order_id"),
                merchantCode=data.get("merchantCode"),
                cancel_message=result.get("success", {}).get("message"),
                response_code=result.get("success", {}).get("response_code")
            )

            return Response(result, status=response.status_code)

        except ValueError:
            return Response({
                "success": False,
                "message": "Invalid response from Paperfly"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
