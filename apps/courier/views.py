from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import requests
from requests.auth import HTTPBasicAuth
from .models import (
    Courierlist,
    PaperflyMerchant,
    PaperflyOrder,
    PaperflyOrderTracking,
    PaperflyOrderCancel,
    SteadfastOrder, 
    SteadfastTracking, 
    SteadfastReturnRequest,
    PathaoToken, PathaoStore, PathaoOrder,
)
from .serializers import CourierCompanySerializer
# courier list section
class CourierCompanyListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = Courierlist.objects.all()
        serializer = CourierCompanySerializer(companies, many=True)
        return Response(serializer.data) 


class ToggleCourierStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        company = Courierlist.objects.get(pk=pk)
        company.toggle_status()
        serializer = CourierCompanySerializer(company)
        return Response([serializer.data], status=status.HTTP_200_OK) 




# ===============================
#  PAPERFLY CONFIG
# ===============================
PAPERFLY_URL = "https://api.paperfly.com.bd/MerchantRegistration"
PAPERFLY_KEY = "Paperfly_~La?Rj73FcLm"
USERNAME = "c174391"
PASSWORD = "6263"

# Merchant Registration for Paperfly
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


# ===============================
# STEADFAST CONFIG
# ===============================

STEADFAST_BASE_URL = "https://portal.packzy.com/api/v1"
STEADFAST_API_KEY = "hqmvdgsdbe6n3jsnhqzqkvzx5ggdxxvu"
STEADFAST_SECRET_KEY = "rw476ldjejh3m7zvfbjnnkp7"

HEADERS = {
    "Api-Key": STEADFAST_API_KEY,
    "Secret-Key": STEADFAST_SECRET_KEY,
    "Authorization": f"Bearer {STEADFAST_API_KEY}",
    "Content-Type": "application/json"
}


# PLACE SINGLE ORDER
class PlaceOrderAPIView(APIView):
    def post(self, request):
        data = request.data
        required_fields = ["invoice","recipient_name","recipient_phone","recipient_address","cod_amount"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return Response({"success":False,"message":"Missing fields","fields":missing},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            resp = requests.post(f"{STEADFAST_BASE_URL}/create_order", json=data, headers=HEADERS, timeout=30)
            result = resp.json()
            if resp.status_code == 200 and "consignment" in result:
                cons = result["consignment"]
                SteadfastOrder.objects.create(
                    consignment_id=cons.get("consignment_id"),
                    invoice=cons.get("invoice"),
                    tracking_code=cons.get("tracking_code"),
                    recipient_name=cons.get("recipient_name"),
                    recipient_phone=cons.get("recipient_phone"),
                    recipient_address=cons.get("recipient_address"),
                    cod_amount=cons.get("cod_amount",0),
                    status=cons.get("status","in_review"),
                    note=cons.get("note"),
                    api_response=result
                )
            return Response(result, status=resp.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"success":False,"message":"API not reachable","error":str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError:
            return Response({"success":False,"message":"Invalid JSON response from API"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# BULK ORDER CREATE
class BulkOrderAPIView(APIView):
    def post(self, request):
        orders = request.data.get("data")

        if not orders or not isinstance(orders, list):
            return Response(
                {"success": False, "message": "data must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(orders) > 500:
            return Response(
                {"success": False, "message": "Max 500 orders allowed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            resp = requests.post(
                f"{STEADFAST_BASE_URL}/create_order/bulk-order",
                json={"data": orders},
                headers=HEADERS,
                timeout=60
            )

            result = resp.json()

            # SAFETY CHECK
            if resp.status_code != 200 or result.get("status") != "success":
                return Response(result, status=resp.status_code)

            # ACTUAL LIST HERE
            for cons in result.get("data", []):
                if isinstance(cons, dict) and cons.get("status") == "success":
                    SteadfastOrder.objects.update_or_create(
                        consignment_id=cons.get("consignment_id"),
                        defaults={
                            "invoice": cons.get("invoice"),
                            "tracking_code": cons.get("tracking_code"),
                            "recipient_name": cons.get("recipient_name"),
                            "recipient_phone": cons.get("recipient_phone"),
                            "recipient_address": cons.get("recipient_address"),
                            "cod_amount": cons.get("cod_amount", 0),
                            "status": cons.get("status"),
                            "api_response": cons
                        }
                    )

            return Response(result, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response(
                {"success": False, "message": "API not reachable", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except ValueError:
            return Response(
                {"success": False, "message": "Invalid JSON response from API"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# DELIVERY STATUS
class DeliveryStatusByCIDAPIView(APIView):
    def get(self, request, consignment_id):
        try:
            resp = requests.get(
                f"{STEADFAST_BASE_URL}/status_by_cid/{consignment_id}",
                headers=HEADERS,
                timeout=30
            )

            try:
                result = resp.json()
            except ValueError:
                return Response({
                    "success": False,
                    "message": "Invalid response from Steadfast",
                    "status_code": resp.status_code,
                    "raw_response": resp.text
                }, status=status.HTTP_502_BAD_GATEWAY)

            if resp.status_code == 200 and result.get("delivery_status"):
                SteadfastTracking.objects.update_or_create(
                    consignment_id=consignment_id,
                    defaults={
                        "delivery_status": result.get("delivery_status"),
                        "api_response": result
                    }
                )

            return Response(result, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Steadfast API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeliveryStatusByInvoiceAPIView(APIView):
    def get(self, request, invoice):
        try:
            resp = requests.get(
                f"{STEADFAST_BASE_URL}/status_by_invoice/{invoice}",
                headers=HEADERS,
                timeout=30
            )

            try:
                result = resp.json()
            except ValueError:
                return Response({
                    "success": False,
                    "message": "Invalid response from Steadfast",
                    "status_code": resp.status_code,
                    "raw_response": resp.text
                }, status=status.HTTP_502_BAD_GATEWAY)

            if resp.status_code == 200 and result.get("delivery_status"):
                SteadfastTracking.objects.update_or_create(
                    invoice=invoice,
                    defaults={
                        "delivery_status": result.get("delivery_status"),
                        "api_response": result
                    }
                )

            return Response(result, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Steadfast API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeliveryStatusByTrackingCodeAPIView(APIView):
    def get(self, request, tracking_code):
        try:
            resp = requests.get(
                f"{STEADFAST_BASE_URL}/status_by_trackingcode/{tracking_code}",
                headers=HEADERS,
                timeout=30
            )

            try:
                result = resp.json()
            except ValueError:
                return Response({
                    "success": False,
                    "message": "Invalid response from Steadfast",
                    "status_code": resp.status_code,
                    "raw_response": resp.text
                }, status=status.HTTP_502_BAD_GATEWAY)

            if resp.status_code == 200 and result.get("delivery_status"):
                SteadfastTracking.objects.update_or_create(
                    tracking_code=tracking_code,
                    defaults={
                        "delivery_status": result.get("delivery_status"),
                        "api_response": result
                    }
                )

            return Response(result, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Steadfast API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# CURRENT BALANCE
class CurrentBalanceAPIView(APIView):
    def get(self, request):
        try:
            resp = requests.get(f"{STEADFAST_BASE_URL}/get_balance", headers=HEADERS, timeout=30)
            result = resp.json()
            return Response(result, status=resp.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"success":False,"message":"API not reachable","error":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError:
            return Response({"success":False,"message":"Invalid JSON response from API"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# RETURN REQUESTS
class ReturnRequestAPIView(APIView):
    def post(self, request):
        data = request.data

        if not any([
            data.get("consignment_id"),
            data.get("invoice"),
            data.get("tracking_code")
        ]):
            return Response(
                {
                    "success": False,
                    "message": "consignment_id or invoice or tracking_code required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            resp = requests.post(
                f"{STEADFAST_BASE_URL}/create_return_request",
                json=data,
                headers=HEADERS,
                timeout=30
            )

            try:
                result = resp.json()
            except ValueError:
                return Response({
                    "success": False,
                    "message": "Invalid response from Steadfast",
                    "status_code": resp.status_code,
                    "raw_response": resp.text
                }, status=status.HTTP_502_BAD_GATEWAY)

            if resp.status_code == 200 and result.get("id"):
                SteadfastReturnRequest.objects.update_or_create(
                    return_id=result.get("id"),
                    defaults={
                        "consignment_id": data.get("consignment_id"),
                        "invoice": data.get("invoice"),
                        "tracking_code": data.get("tracking_code"),
                        "reason": data.get("reason"),
                        "status": result.get("status", "pending"),
                        "api_response": result
                    }
                )

            return Response(result, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "success": False,
                    "message": "Steadfast API not reachable",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetReturnRequestsAPIView(APIView):
    def get(self, request):
        try:
            resp = requests.get(
                f"{STEADFAST_BASE_URL}/get_return_requests",
                headers=HEADERS,
                timeout=30
            )

            try:
                result = resp.json()
            except ValueError:
                return Response({
                    "success": False,
                    "message": "Invalid response from Steadfast",
                    "status_code": resp.status_code,
                    "raw_response": resp.text
                }, status=status.HTTP_502_BAD_GATEWAY)

            return Response(result, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "success": False,
                    "message": "Steadfast API not reachable",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# PAYMENTS
class GetPaymentsAPIView(APIView):
    def get(self, request):
        try:
            resp = requests.get(f"{STEADFAST_BASE_URL}/payments", headers=HEADERS, timeout=30)
            result = resp.json()
            return Response(result, status=resp.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"success":False,"message":"API not reachable","error":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError:
            return Response({"success":False,"message":"Invalid JSON response from API"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetSinglePaymentAPIView(APIView):
    def get(self, request, payment_id):
        try:
            resp = requests.get(f"{STEADFAST_BASE_URL}/payments/{payment_id}", headers=HEADERS, timeout=30)
            result = resp.json()
            return Response(result, status=resp.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"success":False,"message":"API not reachable","error":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError:
            return Response({"success":False,"message":"Invalid JSON response from API"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# POLICE STATIONS
class GetPoliceStationsAPIView(APIView):
    def get(self, request):
        try:
            resp = requests.get(f"{STEADFAST_BASE_URL}/police_stations", headers=HEADERS, timeout=30)
            result = resp.json()
            return Response(result, status=resp.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"success":False,"message":"API not reachable","error":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError:
            return Response({"success":False,"message":"Invalid JSON response from API"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


# ===============================
# PATHAO CONFIG (SANDBOX)
# ===============================
PATHAO_BASE_URL = "https://courier-api-sandbox.pathao.com"

CLIENT_ID = "7N1aMJQbWm"
CLIENT_SECRET = "wRcaibZkUdSNz2EI9ZyuXLlNrnAv0TdPUPXMnD39"
USERNAME = "test@pathao.com"
PASSWORD = "lovePathao"


# ISSUE ACCESS TOKEN
class PathaoIssueTokenAPIView(APIView):

    def post(self, request):
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "password",
            "username": USERNAME,
            "password": PASSWORD
        }

        try:
            resp = requests.post(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/issue-token",
                json=payload,
                timeout=30
            )
            data = resp.json()

            if resp.status_code == 200:
                # Save token to DB
                PathaoToken.objects.create(
                    access_token=data.get("access_token"),
                    refresh_token=data.get("refresh_token"),
                    expires_in=data.get("expires_in")
                )

            return Response(data, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Pathao API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REFRESH ACCESS TOKEN
class PathaoRefreshTokenAPIView(APIView):
    """
    Generate new access token using refresh token
    """

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response({
                "success": False,
                "message": "refresh_token is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }

        try:
            resp = requests.post(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/issue-token",
                json=payload,
                timeout=30
            )
            data = resp.json()

            if resp.status_code == 200:
                # Save new token to DB
                PathaoToken.objects.create(
                    access_token=data.get("access_token"),
                    refresh_token=data.get("refresh_token"),
                    expires_in=data.get("expires_in")
                )

            return Response(data, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Pathao API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# CREATE STORE
class PathaoCreateStoreAPIView(APIView):
    """
    Create merchant store in Pathao
    """

    def post(self, request):
        data = request.data
        access_token = request.headers.get("Authorization")

        mandatory_fields = [
            "name", "contact_name", "contact_number",
            "address", "city_id", "zone_id", "area_id"
        ]

        missing = [f for f in mandatory_fields if not data.get(f)]
        if missing:
            return Response({
                "success": False,
                "message": "Mandatory field missing",
                "missing_fields": missing
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Content-Type": "application/json",
            "Authorization": access_token
        }

        try:
            resp = requests.post(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/stores",
                json=data,
                headers=headers,
                timeout=30
            )
            result = resp.json()

            # Save store to DB if created successfully
            if resp.status_code == 200 and result.get("data"):
                store_data = result.get("data")
                PathaoStore.objects.update_or_create(
                    store_id=store_data.get("store_id"),
                    defaults={
                        "store_name": store_data.get("store_name"),
                        "store_address": data.get("address"),
                        "city_id": data.get("city_id"),
                        "zone_id": data.get("zone_id"),
                        "is_active": True
                    }
                )

            return Response(result, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Pathao API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# CREATE SINGLE ORDER
class PathaoCreateOrderAPIView(APIView):
    """
    Create single order in Pathao
    """

    def post(self, request):
        data = request.data
        access_token = request.headers.get("Authorization")

        mandatory_fields = [
            "store_id", "recipient_name", "recipient_phone",
            "recipient_address", "delivery_type",
            "item_type", "item_quantity", "item_weight",
            "amount_to_collect"
        ]

        missing = [f for f in mandatory_fields if not data.get(f)]
        if missing:
            return Response({
                "success": False,
                "message": "Mandatory field missing",
                "missing_fields": missing
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Content-Type": "application/json",
            "Authorization": access_token
        }

        try:
            resp = requests.post(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/orders",
                json=data,
                headers=headers,
                timeout=30
            )
            result = resp.json()

            # Save order to DB if success
            if resp.status_code == 200 and result.get("data"):
                store_instance = PathaoStore.objects.get(store_id=data.get("store_id"))
                order_data = result.get("data")
                PathaoOrder.objects.update_or_create(
                    consignment_id=order_data.get("consignment_id"),
                    defaults={
                        "merchant_order_id": order_data.get("merchant_order_id"),
                        "store": store_instance,
                        "order_status": order_data.get("order_status"),
                        "delivery_fee": order_data.get("delivery_fee")
                    }
                )

            return Response(result, status=resp.status_code)

        except PathaoStore.DoesNotExist:
            return Response({
                "success": False,
                "message": "Store not found in DB"
            }, status=status.HTTP_400_BAD_REQUEST)
        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Pathao API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# BULK ORDER CREATE
class PathaoBulkOrderAPIView(APIView):
    """
    Create bulk orders (max multiple)
    """

    def post(self, request):
        orders = request.data.get("orders")
        access_token = request.headers.get("Authorization")

        if not orders or not isinstance(orders, list):
            return Response({
                "success": False,
                "message": "orders must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Content-Type": "application/json",
            "Authorization": access_token
        }

        try:
            resp = requests.post(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/orders/bulk",
                json={"orders": orders},
                headers=headers,
                timeout=60
            )
            result = resp.json()

            # Optionally, you can save bulk orders individually
            if resp.status_code in [200, 202] and result.get("data"):
                for order in orders:
                    try:
                        store_instance = PathaoStore.objects.get(store_id=order.get("store_id"))
                        PathaoOrder.objects.update_or_create(
                            merchant_order_id=order.get("merchant_order_id"),
                            store=store_instance,
                            defaults={
                                "order_status": "Pending"  # bulk orders initially pending
                            }
                        )
                    except PathaoStore.DoesNotExist:
                        continue

            return Response(result, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Pathao API not reachable",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ORDER SHORT INFO / TRACKING
class PathaoOrderInfoAPIView(APIView):

    def get(self, request, consignment_id):
        access_token = request.headers.get("Authorization")

        headers = {
            "Authorization": access_token
        }

        try:
            resp = requests.get(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/orders/{consignment_id}/info",
                headers=headers,
                timeout=30
            )
            result = resp.json()

            # Optionally, update order status in DB
            if resp.status_code == 200 and result.get("data"):
                order_data = result.get("data")
                PathaoOrder.objects.filter(consignment_id=consignment_id).update(
                    order_status=order_data.get("order_status")
                )

            return Response(result, status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "Pathao API not reachable",
                "error": str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# LOCATION APIs
class PathaoCityListAPIView(APIView):
    def get(self, request):
        access_token = request.headers.get("Authorization")
        try:
            resp = requests.get(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/city-list",
                headers={"Authorization": access_token},
                timeout=30
            )
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PathaoZoneListAPIView(APIView):
    def get(self, request, city_id):
        access_token = request.headers.get("Authorization")
        try:
            resp = requests.get(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/cities/{city_id}/zone-list",
                headers={"Authorization": access_token},
                timeout=30
            )
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PathaoAreaListAPIView(APIView):
    def get(self, request, zone_id):
        access_token = request.headers.get("Authorization")
        try:
            resp = requests.get(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/zones/{zone_id}/area-list",
                headers={"Authorization": access_token},
                timeout=30
            )
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# PRICE CALCULATION
class PathaoPricePlanAPIView(APIView):
    """
    Calculate delivery price
    """

    def post(self, request):
        data = request.data
        access_token = request.headers.get("Authorization")

        mandatory_fields = [
            "store_id", "item_type", "delivery_type",
            "item_weight", "recipient_city", "recipient_zone"
        ]

        missing = [f for f in mandatory_fields if not data.get(f)]
        if missing:
            return Response({
                "success": False,
                "message": "Mandatory field missing",
                "missing_fields": missing
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            resp = requests.post(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/merchant/price-plan",
                json=data,
                headers={"Authorization": access_token},
                timeout=30
            )
            return Response(resp.json(), status=resp.status_code)

        except requests.exceptions.RequestException as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# GET STORES
class PathaoStoreListAPIView(APIView):
    def get(self, request):
        access_token = request.headers.get("Authorization")
        try:
            resp = requests.get(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/stores",
                headers={"Authorization": access_token},
                timeout=30
            )
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
