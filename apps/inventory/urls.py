from django.urls import path
from .views import (
    ProductCreateAPIView,
    ProductListAPIView,
    ProductPurchaseAPIView,
    ProductDetailAPIView,
    StockListAPIView,
    StockDetailAPIView,
    PurchaseReturnAPIView,
    LossAndDamageAPIView,
    PurchaseProductDataAPIView,
    ProductListByPOIDAPIView
)

urlpatterns = [
    # product
    path('products/create/', ProductCreateAPIView.as_view()),
    path('list/products/', ProductListAPIView.as_view()),
    path('products/<int:pk>/', ProductDetailAPIView.as_view()),


    # product Purchase
    path("purchases/products/", ProductPurchaseAPIView.as_view()),
    
    # stock
    path("stock/list/", StockListAPIView.as_view()),
    path("stock/<int:stock_id>/", StockDetailAPIView.as_view()),
    
    # purchase return
    path("purchases/PO-id/", PurchaseProductDataAPIView.as_view()),
    path("purchases/PO-id/<int:purchase_id>/", ProductListByPOIDAPIView.as_view()),
    path("purchases/returns/", PurchaseReturnAPIView.as_view()),
    
    # loss and damage
    path("loss_and_damages/", LossAndDamageAPIView.as_view()),
]