from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    RefreshTokenRotationView,
    LogoutView,
    AccountView,
    CreateChildUserView,
    ViewChildUserListView,
    ViewChildUserView,
    UpdateChildUserView,
    ViewShopAPIView,
    UpdateShopAPIView,
    BusinessRetrieveAPIView,
    BusinessUpdateAPIView,
    BankingDetailAPIView,
    BankingUpdateAPIView,
    ChangePasswordAPIView
)

urlpatterns = [

    # Auth URLs
    path("auth/register/", UserRegistrationView.as_view(), name="user_register"),
    path("auth/login/", UserLoginView.as_view(), name="user_login"),
    path("auth/refresh/", RefreshTokenRotationView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="user_logout"),

    # Account
    path("account/", AccountView.as_view(), name="account"),

    # Child User CRUD
    path("child/create/", CreateChildUserView.as_view(), name="create_child_user"),
    path("child/list/", ViewChildUserListView.as_view(), name="child_user_list"),
    path("child/<int:pk>/", ViewChildUserView.as_view(), name="child_user_detail"),
    path("child/<int:pk>/update/", UpdateChildUserView.as_view(), name="update_child_user"),
    
    # Setting > Profile > Shop Info Urls
    path("shops/", ViewShopAPIView.as_view()),
    path("shops/update/", UpdateShopAPIView.as_view()),

    # Setting > Profile > business Info Urls
    path("business/", BusinessRetrieveAPIView.as_view(), name="business-get"),
    path("business/update/", BusinessUpdateAPIView.as_view(), name="business-update"),

    # Setting > Profile > business Info Urls
    path("banking/", BankingDetailAPIView.as_view(), name="banking-detail"),
    path("banking/update/", BankingUpdateAPIView.as_view(), name="banking-update"),

    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
]