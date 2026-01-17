from django.urls import path
from .views import (
    ProductCreateAPIView,
    ProductListAPIView,
    OrderListCreateAPIView,
    OrderDetailAPIView,
    ProductDetailAPIView
)

urlpatterns = [
    # product
    path('products/create/', ProductCreateAPIView.as_view()),
    path('list/products/', ProductListAPIView.as_view()),
    path('products/<int:product_id>/', ProductDetailAPIView.as_view()),

    # product Purchase
    path('Purchase/orders/create/', OrderListCreateAPIView.as_view()),
    path('Purchase/orders/list', OrderDetailAPIView.as_view()),
]