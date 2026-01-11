from utils.base_view import BaseAPIView as APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import requests
from requests.auth import HTTPBasicAuth
from .serializers import CourierCompanySerializer, CourierOrderSerializer, CourierOrderListSerializer
from .models import (
    PaperflyMerchant,
    PaperflyOrder,
    PaperflyOrderTracking,
    PaperflyOrderCancel,
    SteadfastOrder, 
    SteadfastTracking, 
    SteadfastReturnRequest,
    PathaoToken, PathaoStore, PathaoOrder,OrderCourierMap,
    CourierOrder
)
from django.shortcuts import get_object_or_404
from .models import CourierList, UserCourier
from .track_orders import track_order


class CourierListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        couriers = CourierList.objects.all()
        user_couriers = list(UserCourier.objects.filter(user=request.user))
        serializer = CourierCompanySerializer(
            couriers,
            many=True,
            context={'request': request, 'user_couriers': user_couriers}
        )
        return self.success(
            data=serializer.data,
            message="Courier list fetched successfully" if serializer.data else "No couriers assigned to this user",
            meta={"action": "user-courier-list"}
        )
    

class ToggleCourierStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            courier = get_object_or_404(CourierList, id=pk)
            user_courier = UserCourier.objects.get_or_create(user=request.user, courier=courier)[0]
            if user_courier.is_active:
                user_courier.is_active = False
                user_courier.save()
                return self.success(
                    data=user_courier,
                    message="Courier deactivated",
                    meta={"action": "toggle-courier-status"}
                )
            else:
                user_courier.is_active = True
                user_courier.save()
                return self.success(
                    message="Courier activated",
                    meta={"action": "toggle-courier-status"}
                )

        except Exception as e:
            return self.error(message=str(e), status_code=500, meta={"action": "toggle-courier-status"})
        
class CourierOrderListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, status=None):
        if status == 'booking':
            orders = CourierOrder.objects.filter(
            order__user=request.user
            ).exclude(
                status__in=["reject", "cancel", "collected"]
            )
        elif status == 'reject':
            orders = CourierOrder.objects.filter(
                order__user=request.user,
                status="reject"
            )
        elif status == 'collected':
            orders = CourierOrder.objects.filter(
                order__user=request.user,
                status="collected"
            )
        else:
            orders = None
        data = CourierOrderListSerializer(orders, many=True).data
        return self.success(
            data=data,
            message="Courier order list fetched successfully" if data else "No couriers assigned to this user",
            meta={"action": "user-courier-list"}
        )
        
        
    

        
class TrackOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            response = track_order(order_id)
            data = CourierOrderSerializer(response).data
            return self.success(
                data=data,
                message="Order tracking fetched successfully" if data['courier_status'] else "No Courier Order found on this order id",
                status_code=status.HTTP_200_OK
            )
        
        except Exception as e:
            return self.error(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



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
            return self.error(
                message="Mandatory field missing",
                data={"missing_fields": missing_fields},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "paperfly-registration"}
            )

        # Validate payment mode
        allowed_payment_modes = ["beftn", "cash", "bkash", "rocket", "nagad"]
        if data.get("payment_mode") not in allowed_payment_modes:
            return self.error(
                message="Invalid payment_mode",
                data={"allowed_values": allowed_payment_modes},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "paperfly-registration"}
            )

        payload = {field: data.get(field) for field in data.keys()}

        headers = {"Content-Type":"application/json","Paperflykey":PAPERFLY_KEY}

        try:
            response = requests.post(
                PAPERFLY_URL,
                json=payload,
                headers=headers,
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="Paperfly API not reachable",
                data={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "paperfly-registration"}
            )

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
            return self.success(
                data=response.json(),
                message="Paperfly merchant registered successfully",
                meta={"action": "paperfly-registration"}
            )
        except ValueError:
            return self.error(
                message="Invalid response from Paperfly",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "paperfly-registration"}
            )

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
            return self.error(
                message="Mandatory field missing",
                errors={"missing_fields": missing_fields},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "paperfly-order-create"}
            )

        # Validate productSizeWeight & deliveryOption
        if data.get("productSizeWeight") not in ["standard","large","special"]:
            return self.error(
                message="Invalid productSizeWeight",
                errors={"allowed_values": ["standard","large","special"]},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "paperfly-order-create"}
            )

        if data.get("deliveryOption") not in ["regular","express"]:
            return self.error(
                message="Invalid deliveryOption",
                errors={"allowed_values": ["regular","express"]},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "paperfly-order-create"}
            )

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
            return self.error(
                message="Paperfly API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "paperfly-order-create"}
            )

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

            return self.success(
                data=result,
                message="Paperfly order response",
                status_code=response.status_code,
                meta={"action": "paperfly-order-create"}
            )

        except ValueError:
            return self.error(
                message="Invalid response from Paperfly",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "paperfly-order-create"}
            )

# Order Tracking
PAPERFLY_TRACK_URL = "https://api.paperfly.com.bd/API-Order-Tracking"

class PaperflyOrderTrackingAPIView(APIView):

    def post(self, request):
        data = request.data

        # Mandatory fields check
        mandatory_fields = ["ReferenceNumber", "merchantCode"]
        missing_fields = [f for f in mandatory_fields if not data.get(f)]
        if missing_fields:
            return self.error(
                message="Mandatory field missing",
                errors={"missing_fields": missing_fields},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "paperfly-order-tracking"}
            )

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
                auth=HTTPBasicAuth(USERNAME, ""),
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="Paperfly API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "paperfly-order-tracking"}
            )

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

            return self.success(
                data=result,
                message="Paperfly tracking response",
                status_code=response.status_code,
                meta={"action": "paperfly-order-tracking"}
            )
        except ValueError:
            return self.error(
                message="Invalid response from Paperfly",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "paperfly-order-tracking"}
            )

# order cancellation integration
PAPERFLY_CANCEL_URL = "https://api.paperfly.com.bd/api/v1/cancel-order"

class PaperflyOrderCancelAPIView(APIView):

    def post(self, request):
        data = request.data

        # Mandatory fields
        mandatory_fields = ["order_id", "merchantCode"]
        missing_fields = [f for f in mandatory_fields if not data.get(f)]

        if missing_fields:
            return self.error(
                message="Mandatory field missing",
                errors={"missing_fields": missing_fields},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "paperfly-order-cancel"}
            )

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
            return self.error(
                message="Paperfly API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "paperfly-order-cancel"}
            )

        try:
            result = response.json()

            # Save cancel log to DB
            PaperflyOrderCancel.objects.create(
                order_id=data.get("order_id"),
                merchantCode=data.get("merchantCode"),
                cancel_message=result.get("success", {}).get("message"),
                response_code=result.get("success", {}).get("response_code")
            )

            return self.success(
                data=result,
                message="Paperfly cancel response",
                status_code=response.status_code,
                meta={"action": "paperfly-order-cancel"}
            )

        except ValueError:
            return self.error(
                message="Invalid response from Paperfly",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "paperfly-order-cancel"}
            )


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
            return self.error(
                message="Missing fields",
                errors={"fields": missing},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "steadfast-place-order"}
            )
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
            return self.success(
                data=result,
                message="Steadfast place order response",
                status_code=resp.status_code,
                meta={"action": "steadfast-place-order"}
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-place-order"}
            )
        except ValueError:
            return self.error(
                message="Invalid JSON response from API",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-place-order"}
            )


# BULK ORDER CREATE
class BulkOrderAPIView(APIView):
    def post(self, request):
        orders = request.data.get("data")

        if not orders or not isinstance(orders, list):
            return self.error(
                message="data must be a non-empty list",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "steadfast-bulk-order"}
            )

        if len(orders) > 500:
            return self.error(
                message="Max 500 orders allowed",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "steadfast-bulk-order"}
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
                return self.error(
                    message="Steadfast bulk order returned error",
                    errors=result,
                    status_code=resp.status_code,
                    meta={"action": "steadfast-bulk-order"}
                )

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

            return self.success(
                data=result,
                message="Steadfast bulk order response",
                status_code=resp.status_code,
                meta={"action": "steadfast-bulk-order"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-bulk-order"}
            )

        except ValueError:
            return self.error(
                message="Invalid JSON response from API",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-bulk-order"}
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
                return self.error(
                    message="Invalid response from Steadfast",
                    errors={"status_code": resp.status_code, "raw_response": resp.text},
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    meta={"action": "steadfast-status-by-cid"}
                )

            if resp.status_code == 200 and result.get("delivery_status"):
                SteadfastTracking.objects.update_or_create(
                    consignment_id=consignment_id,
                    defaults={
                        "delivery_status": result.get("delivery_status"),
                        "api_response": result
                    }
                )

            return self.success(
                data=result,
                message="Steadfast status by cid response",
                status_code=resp.status_code,
                meta={"action": "steadfast-status-by-cid"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Steadfast API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-status-by-cid"}
            )

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
                return self.error(
                    message="Invalid response from Steadfast",
                    errors={"status_code": resp.status_code, "raw_response": resp.text},
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    meta={"action": "steadfast-status-by-invoice"}
                )

            if resp.status_code == 200 and result.get("delivery_status"):
                SteadfastTracking.objects.update_or_create(
                    invoice=invoice,
                    defaults={
                        "delivery_status": result.get("delivery_status"),
                        "api_response": result
                    }
                )

            return self.success(
                data=result,
                message="Steadfast status by invoice response",
                status_code=resp.status_code,
                meta={"action": "steadfast-status-by-invoice"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Steadfast API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-status-by-invoice"}
            )

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
                return self.error(
                    message="Invalid response from Steadfast",
                    errors={"status_code": resp.status_code, "raw_response": resp.text},
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    meta={"action": "steadfast-status-by-trackingcode"}
                )

            if resp.status_code == 200 and result.get("delivery_status"):
                SteadfastTracking.objects.update_or_create(
                    tracking_code=tracking_code,
                    defaults={
                        "delivery_status": result.get("delivery_status"),
                        "api_response": result
                    }
                )

            return self.success(
                data=result,
                message="Steadfast status by tracking code response",
                status_code=resp.status_code,
                meta={"action": "steadfast-status-by-trackingcode"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Steadfast API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-status-by-trackingcode"}
            )


# CURRENT BALANCE
class CurrentBalanceAPIView(APIView):
    def get(self, request):
        try:
            resp = requests.get(f"{STEADFAST_BASE_URL}/get_balance", headers=HEADERS, timeout=30)
            result = resp.json()
            return self.success(
                data=result,
                message="Steadfast current balance response",
                status_code=resp.status_code,
                meta={"action": "steadfast-get-balance"}
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-get-balance"}
            )
        except ValueError:
            return self.error(
                message="Invalid JSON response from API",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-get-balance"}
            )


# RETURN REQUESTS
class ReturnRequestAPIView(APIView):
    def post(self, request):
        data = request.data

        if not any([
            data.get("consignment_id"),
            data.get("invoice"),
            data.get("tracking_code")
        ]):
            return self.error(
                message="consignment_id or invoice or tracking_code required",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "steadfast-return-request"}
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
                return self.error(
                    message="Invalid response from Steadfast",
                    errors={"status_code": resp.status_code, "raw_response": resp.text},
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    meta={"action": "steadfast-return-request"}
                )

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

            return self.success(
                data=result,
                message="Steadfast create return request response",
                status_code=resp.status_code,
                meta={"action": "steadfast-return-request"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Steadfast API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-return-request"}
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
                return self.error(
                    message="Invalid response from Steadfast",
                    errors={"status_code": resp.status_code, "raw_response": resp.text},
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    meta={"action": "steadfast-get-return-requests"}
                )

            return self.success(
                data=result,
                message="Steadfast get return requests response",
                status_code=resp.status_code,
                meta={"action": "steadfast-get-return-requests"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Steadfast API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-get-return-requests"}
            )


# PAYMENTS
class GetPaymentsAPIView(APIView):
    def get(self, request):
        try:
            resp = requests.get(f"{STEADFAST_BASE_URL}/payments", headers=HEADERS, timeout=30)
            result = resp.json()
            return self.success(
                data=result,
                message="Steadfast get payments response",
                status_code=resp.status_code,
                meta={"action": "steadfast-get-payments"}
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-get-payments"}
            )
        except ValueError:
            return self.error(
                message="Invalid JSON response from API",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-get-payments"}
            )


class GetSinglePaymentAPIView(APIView):
    def get(self, request, payment_id):
        try:
            resp = requests.get(f"{STEADFAST_BASE_URL}/payments/{payment_id}", headers=HEADERS, timeout=30)
            result = resp.json()
            return self.success(
                data=result,
                message="Steadfast get single payment response",
                status_code=resp.status_code,
                meta={"action": "steadfast-get-single-payment"}
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-get-single-payment"}
            )
        except ValueError:
            return self.error(
                message="Invalid JSON response from API",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-get-single-payment"}
            )


# POLICE STATIONS
class GetPoliceStationsAPIView(APIView):
    def get(self, request):
        try:
            resp = requests.get(f"{STEADFAST_BASE_URL}/police_stations", headers=HEADERS, timeout=30)
            result = resp.json()
            return self.success(
                data=result,
                message="Steadfast get police stations response",
                status_code=resp.status_code,
                meta={"action": "steadfast-get-police-stations"}
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-get-police-stations"}
            )
        except ValueError:
            return self.error(
                message="Invalid JSON response from API",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "steadfast-get-police-stations"}
            )
        


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

            return self.success(
                data=data,
                message="Pathao issue token response",
                status_code=resp.status_code,
                meta={"action": "pathao-issue-token"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-issue-token"}
            )

# REFRESH ACCESS TOKEN
class PathaoRefreshTokenAPIView(APIView):

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return self.error(
                message="refresh_token is required",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "pathao-refresh-token"}
            )

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

            return self.success(
                data=data,
                message="Pathao refresh token response",
                status_code=resp.status_code,
                meta={"action": "pathao-refresh-token"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-refresh-token"}
            )

# CREATE STORE
class PathaoCreateStoreAPIView(APIView):

    def post(self, request):
        data = request.data
        access_token = request.headers.get("Authorization")

        mandatory_fields = [
            "name", "contact_name", "contact_number",
            "address", "city_id", "zone_id", "area_id"
        ]

        missing = [f for f in mandatory_fields if not data.get(f)]
        if missing:
            return self.error(
                message="Mandatory field missing",
                errors={"missing_fields": missing},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "pathao-create-store"}
            )

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

            return self.success(
                data=result,
                message="Pathao create store response",
                status_code=resp.status_code,
                meta={"action": "pathao-create-store"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-create-store"}
            )

# CREATE SINGLE ORDER
class PathaoCreateOrderAPIView(APIView):
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
            return self.error(
                message="Mandatory field missing",
                errors={"missing_fields": missing},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "pathao-create-order"}
            )

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

            return self.success(
                data=result,
                message="Pathao create order response",
                status_code=resp.status_code,
                meta={"action": "pathao-create-order"}
            )

        except PathaoStore.DoesNotExist:
            return self.error(
                message="Store not found in DB",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "pathao-create-order"}
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-create-order"}
            )

# BULK ORDER CREATE
class PathaoBulkOrderAPIView(APIView):

    def post(self, request):
        orders = request.data.get("orders")
        access_token = request.headers.get("Authorization")

        if not orders or not isinstance(orders, list):
            return self.error(
                message="orders must be a list",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "pathao-bulk-order"}
            )

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

            return self.success(
                data=result,
                message="Pathao bulk order response",
                status_code=resp.status_code,
                meta={"action": "pathao-bulk-order"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-bulk-order"}
            )


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

            return self.success(
                data=result,
                message="Pathao order info response",
                status_code=resp.status_code,
                meta={"action": "pathao-order-info"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-order-info"}
            )

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
            return self.success(
                data=resp.json(),
                message="Pathao city list response",
                status_code=resp.status_code,
                meta={"action": "pathao-city-list"}
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-city-list"}
            )

class PathaoZoneListAPIView(APIView):
    def get(self, request, city_id):
        access_token = request.headers.get("Authorization")
        try:
            resp = requests.get(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/cities/{city_id}/zone-list",
                headers={"Authorization": access_token},
                timeout=30
            )
            return self.success(
                data=resp.json(),
                message="Pathao zone list response",
                status_code=resp.status_code,
                meta={"action": "pathao-zone-list"}
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-zone-list"}
            )

class PathaoAreaListAPIView(APIView):
    def get(self, request, zone_id):
        access_token = request.headers.get("Authorization")
        try:
            resp = requests.get(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/zones/{zone_id}/area-list",
                headers={"Authorization": access_token},
                timeout=30
            )
            return self.success(
                data=resp.json(),
                message="Pathao area list response",
                status_code=resp.status_code,
                meta={"action": "pathao-area-list"}
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-area-list"}
            )

# PRICE CALCULATION
class PathaoPricePlanAPIView(APIView):

    def post(self, request):
        data = request.data
        access_token = request.headers.get("Authorization")

        mandatory_fields = [
            "store_id", "item_type", "delivery_type",
            "item_weight", "recipient_city", "recipient_zone"
        ]

        missing = [f for f in mandatory_fields if not data.get(f)]
        if missing:
            return self.error(
                message="Mandatory field missing",
                errors={"missing_fields": missing},
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "pathao-price-plan"}
            )

        try:
            resp = requests.post(
                f"{PATHAO_BASE_URL}/aladdin/api/v1/merchant/price-plan",
                json=data,
                headers={"Authorization": access_token},
                timeout=30
            )
            return self.success(
                data=resp.json(),
                message="Pathao price plan response",
                status_code=resp.status_code,
                meta={"action": "pathao-price-plan"}
            )

        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-price-plan"}
            )

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
            return self.success(
                data=resp.json(),
                message="Pathao store list response",
                status_code=resp.status_code,
                meta={"action": "pathao-store-list"}
            )
        except requests.exceptions.RequestException as e:
            return self.error(
                message="Pathao API not reachable",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "pathao-store-list"}
            )


# Unified Courier Tracking API

class UnifiedOrderTrackingAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):

        try:
            order = Order.objects.get(
                id=order_id,
                vendor__owner=request.user
            )
        except Order.DoesNotExist:
            return self.success(
                message="Order not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            mapping = order.courier_map
        except OrderCourierMap.DoesNotExist:
            return self.success(
                message="Courier not assigned for this order",
                status_code=status.HTTP_404_NOT_FOUND
            )

        courier_name = mapping.courier.name.lower()
        ref = mapping.courier_order_ref

        # =======================
        # PAPERFLY
        # =======================
        if courier_name == 'paperfly':
            tracking = PaperflyOrderTracking.objects.filter(
                ReferenceNumber=ref
            ).last()

            if not tracking:
                return self.success(
                    message="Paperfly tracking not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            data = {
                "courier": "Paperfly",
                "reference": ref,
                "status": {
                    "picked": tracking.Pick,
                    "in_transit": tracking.inTransit,
                    "delivered": tracking.Delivered,
                    "returned": tracking.Returned
                },
                "timeline": {
                    "pick_time": tracking.PickTime,
                    "in_transit_time": tracking.inTransitTime,
                    "delivered_time": tracking.DeliveredTime,
                    "returned_time": tracking.ReturnedTime
                }
            }

        # =======================
        # STEADFAST
        # =======================
        elif courier_name == 'steadfast':
            tracking = SteadfastTracking.objects.filter(
                invoice=ref
            ).last() or SteadfastTracking.objects.filter(
                consignment_id=ref
            ).last()

            if not tracking:
                return self.success(
                    message="Steadfast tracking not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            data = {
                "courier": "Steadfast",
                "reference": ref,
                "current_status": tracking.delivery_status,
                "raw_response": tracking.api_response
            }

        # =======================
        # PATHAO
        # =======================
        elif courier_name == 'pathao':
            pathao_order = PathaoOrder.objects.filter(
                merchant_order_id=ref
            ).first()

            if not pathao_order:
                return self.success(
                    message="Pathao order not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            data = {
                "courier": "Pathao",
                "reference": ref,
                "current_status": pathao_order.order_status
            }

        else:
            return self.success(
                message="Unsupported courier",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.success(
            message="Order tracking fetched successfully",
            data=data,
            status_code=status.HTTP_200_OK
        )
