from utils.base_view import BaseAPIView as APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import VendorSerializer

# Create your views here.


class VendorRegistrationAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VendorSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(owner=request.user)

            return self.success(
                message="Vendor registered successfully",
                status_code=status.HTTP_201_CREATED,
                data=serializer.data,
                meta={"model": "Vendor"},
            )

        return self.error(
            message="Vendor registration failed",
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=serializer.errors,
        )
