from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import CustomerInfo
from .serializers import CustomerInfoSerializer

class CustomerInfoAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        # Get query parameters
        customer_id = request.query_params.get('id')
        owner_username = request.query_params.get('owner')
        location = request.query_params.get('location')

        # Start with all objects for this user
        queryset = CustomerInfo.objects.filter(owner=request.user)

        # Apply filters if provided
        if customer_id:
            queryset = queryset.filter(id=customer_id)
        if owner_username:
            queryset = queryset.filter(owner__username__icontains=owner_username)
        if location:
            queryset = queryset.filter(location__icontains=location)

        if not queryset.exists():
            return Response(
                {"detail": "No customers found matching your criteria."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CustomerInfoSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
