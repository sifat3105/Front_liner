from django.urls import path
from .views import (
    ProductCreateAPIView,
    ProductListAPIView,
    ProductPurchaseCreateAPIView,
    ProductPurchaseListAPIView,
    ProductDetailAPIView
)

urlpatterns = [
    # product
    path('products/create/', ProductCreateAPIView.as_view()),
    path('list/products/', ProductListAPIView.as_view()),
    path('products/<int:product_id>/', ProductDetailAPIView.as_view()),


    # product Purchase
    path("purchases/create/", ProductPurchaseCreateAPIView.as_view()),
    path("list/purchases/", ProductPurchaseListAPIView.as_view()),
]