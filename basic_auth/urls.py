from django.urls import path
from .views import AdminLoginView, SupportAdminLoginView, UserRegisterView, UserLoginView, UserVerificationEmailView, UserVerifyEmailView, TokenVerifyView, ForgotPasswordView, ResetPasswordView, ForgotPasswordVerifyView, RefreshTokenView

urlpatterns = [
    path('admin/login/', AdminLoginView.as_view(), name="admin-login"),
    path('supportadmin/login/', SupportAdminLoginView.as_view(), name="supportadmin-login"),
    path('signup/', UserRegisterView.as_view(), name="register-page"),
    path('signup/<str:referr_id>/', UserRegisterView.as_view(), name="register-page"),
    path('login/', UserLoginView.as_view(), name="login-page"),
    path('email/verify/request/', UserVerificationEmailView.as_view(), name="verify-email-page"),
    path('email/verify/', UserVerifyEmailView.as_view(), name="verify-email-page"),
    path('token/veify', TokenVerifyView.as_view(), name="user-token-verify"),
    path('password/forgot/', ForgotPasswordView.as_view(), name="user-password-forgot"),
    path('password/reset/', ResetPasswordView.as_view(), name="user-password-forgot"),
    path('password/verify/', ForgotPasswordVerifyView.as_view(), name="user-password-verify"),
    path('refresh/token/', RefreshTokenView.as_view(), name="refresh-token-verify")
]