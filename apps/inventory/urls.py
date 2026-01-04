from django.urls import path
from .views import (
    ProductCreateAPIView,
    ProductListAPIView,
    SizeListCreateAPIView,
    ColorListCreateAPIView,
    ProductPurchaseCreateAPIView,
    ProductPurchaseListAPIView
)

urlpatterns = [
    # product
    path('products/create/', ProductCreateAPIView.as_view()),
    path('list/products/', ProductListAPIView.as_view()),

    # attributes
    path('sizes/', SizeListCreateAPIView.as_view()),
    path('colors/', ColorListCreateAPIView.as_view()),

    # product Purchase
    path("purchases/create/", ProductPurchaseCreateAPIView.as_view()),
    path("list/purchases/", ProductPurchaseListAPIView.as_view()),
]