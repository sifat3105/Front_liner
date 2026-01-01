from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .serializers import VendorSerializer


class VendorRegistrationAPIView(BaseAPIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VendorSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(owner=request.user)

            return self.success(
                message="Vendor registered successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
                meta={"model": "Vendor"},
            )

        return self.error(
            message="Vendor registration failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
