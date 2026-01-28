from utils.base_view import BaseAPIView as APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from twilio.rest import Client
from django.core.cache import cache

from apps.notification.utils import create_notification
from .serializers import PhoneNumberSerializer
from apps.transaction.utils import create_transaction
from .models import PhoneNumber
import os

# TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_SID")
# TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH")
TWILIO_ACCOUNT_SID = "AC5084a51e3437c76a212d7fabdce4c083"
TWILIO_AUTH_TOKEN ="61d9afd16451886ebb624bd05351bb7e"
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

class AvailbePhoneNumberView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        country = request.query_params.get('country', 'US')
        area_code = request.query_params.get('area_code', None)
        sms_enabled = request.query_params.get('sms_enabled', 'true').lower() == 'true'
        voice_enabled = request.query_params.get('voice_enabled', 'true').lower() == 'true'
        limit = int(request.query_params.get('limit', 100))

        
        numbers = client.available_phone_numbers(country).local.list(
        area_code=area_code,
        sms_enabled=sms_enabled,
        voice_enabled=voice_enabled,
        limit=limit
    )
        try:
            numbers = client.available_phone_numbers(country).local.list(
                area_code=area_code,
                sms_enabled=sms_enabled,
                voice_enabled=voice_enabled,
                limit=limit
            )
            data = [{
                "phone_number": num.phone_number,
                "lata": num.lata,
                "rate_center": num.rate_center,
                "region": num.region,
                "postal_code": num.postal_code,
                "iso_country": num.iso_country,
                "capabilities": num.capabilities,
                "price": 9.99,
                } for num in numbers]
            return self.success(
                message="Phone numbers fetched successfully",
                data=data,
                status_code=status.HTTP_200_OK,
                meta={"action": "phone-number-list"}
            )

        except Exception as e:
            return self.error(
                message="Failed to fetch phone numbers",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "phone-number-list"}
            )
        
class PurchasePhoneNumberView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            data = request.data
            profile = user.account
            print(f"user balance: {profile.balance}")
            if profile.balance < 9.99:
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Insufficient balance.",
                    "data": None
                })
            phone_number = data.get('phone_number')
            country = data.get('country', 'US')
            
            if not phone_number:
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Phone number is required.",
                    "data": None
                })
            purchased_number = client.incoming_phone_numbers.create(
                phone_number=phone_number
            )
            obj = PhoneNumber.objects.create(
                user=user,
                phone_number=phone_number,
                number_sid=purchased_number.sid,
            )
            profile = user.profile
            profile.balance -= 9.99
            profile.cost += 9.99
            profile.save()
            create_notification(
                user_id = user.id,
                title="Phone Number Purchased",
                message=f"You have successfully purchased the phone number {phone_number}.",    
            )
            create_transaction(
                user = user,
                status = "completed",
                category = "number",
                amount = 9.99,
                description = "Phone number purchased successfully.",
                purpose = "Purchase Phone Number",
                payment_method = "balance"
            )
            return self.success(
                message="Phone number purchased successfully.",
                data=PhoneNumberSerializer(obj).data,
                status_code=status.HTTP_201_CREATED,
                meta={"action": "phone-number-purchase"}
            )
        except Exception as e:
            return self.error(
                message="Failed to purchase phone number",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                meta={"action": "phone-number-purchase"}
            )
                
            


class PhoneNumberView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = PhoneNumber.objects.filter(user=request.user).order_by("-id")
        serializer = PhoneNumberSerializer(queryset, many=True)

        return self.success(
            message="Phone numbers fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={"action": "phone-number-list"}
        )

        
        
CACHE_KEY = "available_countries"
CACHE_TIMEOUT = 60 * 60 
        
def get_available_countries():
    # First, check if the data is in cache
    countries = cache.get(CACHE_KEY)
    if countries:
        
        return countries
    data = []

    # If not in cache, fetch from API
    try:
        countries = client.available_phone_numbers.list()
        for country in countries:
            data.append({
                "country": country.country,
                "country_code": country.country_code,
            })
        
        # Save in cache
        cache.set(CACHE_KEY, data, CACHE_TIMEOUT)
    
        
        return data
    except Exception as e:
        print(f"Error fetching countries: {e}")
        return []
    
class CountryView(APIView):
    permission_classes = []
    
    def get(self, request):
        return self.success(
            message="Countries fetched successfully.",
            data=get_available_countries(),
            status_code=status.HTTP_200_OK,
            meta={"action": "country-list"}
        )
    
