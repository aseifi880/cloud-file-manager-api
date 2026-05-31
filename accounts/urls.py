from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()

router.register("admin/users", views.UserViewSet, basename="admin-users")


urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("request-otp/", views.RequestOTPView.as_view(), name="request-otp"),
    path("verify-otp/", views.VerifyOTPView.as_view(), name="verify_otp"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("myuser/", views.UserView.as_view(), name="user"),

]
urlpatterns += router.urls
