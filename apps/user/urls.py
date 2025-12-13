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
    
]
