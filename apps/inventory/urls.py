from django.urls import path
from .views import (
    ProductCreateAPIView,
    ProductListAPIView,
    ProductPurchaseAPIView,
    ProductPurchaseListAPIView,
    ProductDetailAPIView,
    StockListAPIView,
    StockDetailAPIView
)

urlpatterns = [
    # product
    path('products/create/', ProductCreateAPIView.as_view()),
    path('list/products/', ProductListAPIView.as_view()),
    path('products/<int:product_id>/', ProductDetailAPIView.as_view()),

    # product Purchase
    path("purchases/product/", ProductPurchaseAPIView.as_view()),
    path("list/purchases/", ProductPurchaseListAPIView.as_view()),
    
    # stock
    path("stock/list/", StockListAPIView.as_view()),
    path("stock/<int:stock_id>/", StockDetailAPIView.as_view()),
]