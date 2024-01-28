"""
URL patterns for SIWE Authentication API.

This module defines the URL patterns for Siwe Authentication, including endpoints for login, verification, session refresh, logout, nonce generation, and retrieving user wallet information.

URL Patterns:
- `/login/`: Endpoint for user login.
- `/verify/`: Endpoint for verifying user session.
- `/refresh/`: Endpoint for refreshing user session.
- `/logout/`: Endpoint for user logout.
- `/nonce/`: Endpoint for generating nonce values.
- `/wallet/me/`: Endpoint for retrieving user wallet information.

Note: These patterns are designed to work with Django's URL routing system.
"""

from django.urls import re_path

from siwe_auth import views

app_name = "siwe_auth"
urlpatterns = [
    re_path(r"^login/?$", views.login, name="login"),
    re_path(r"^verify/?$", views.verify, name="verify"),
    re_path(r"^refresh/?$", views.refresh, name="refresh"),
    re_path(r"^logout/?$", views.logout, name="logout"),
    re_path(r"^nonce/?$", views.nonce, name="nonce"),
    re_path(r"^wallet/me/?$", views.me, name="me"),
]
