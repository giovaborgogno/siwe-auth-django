"""
SIWE Authentication Views

This module contains Django views for handling Sign-In with Ethereum (SIWE) authentication.
The views cover user login, logout, nonce generation, session verification, session refresh,
and user information retrieval.

Each view corresponds to a specific SIWE authentication operation, and the module provides
consistent JSON responses based on the SIWE protocol. The views handle authentication-related
exceptions and unexpected errors, ensuring a robust and secure authentication process.

The views are designed to integrate seamlessly with the SIWE authentication system, utilizing
Web3 and SIWE message verification to authenticate users based on Ethereum addresses and signatures.

File Structure:
- login: Handle user login with SIWE protocol
- logout: Handle user logout
- nonce: Generate and provide nonce for SIWE message
- verify: Verify the user's authentication status
- refresh: Refresh the user's session
- me: Retrieve information about the authenticated user

HTTP Status Codes:
- 200 OK: Successful operation
- 400 Bad Request: Validation error
- 401 Unauthorized: Authentication failure
- 403 Forbidden: Access denied
- 500 Internal Server Error: Unexpected server error

Author: Giovanni Borgogno
Date: January 27th, 2024
"""

from datetime import datetime, timedelta
import json
import secrets

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
import pytz
from siwe import SiweMessage

from siwe_auth import models, utils, constants
from siwe_auth.conf import settings

csrf_decorator = csrf_exempt if settings.CSRF_EXEMPT else csrf_protect


@csrf_decorator
@require_http_methods(["POST"])
def login(request):
    """
    Handle user login via Sign-In with Ethereum (SIWE) protocol (EIP-4361).

    Validates the SIWE message and signature, authenticates the user,
    and returns a JSON response with the authentication status.

    Possible HTTP statuses:
    - 200 OK: Successful login
    - 400 Bad Request: Validation error
    - 401 Unauthorized: Invalid login
    - 403 Forbidden: Wallet is disabled
    - 500 Internal Server Error: Unexpected error during login
    """
    try:
        body = json.loads(request.body)
        auth_kwargs = {
            "siwe_message": SiweMessage(
                message=utils._dict_camel_case_to_snake_case(body["message"])
                ),
            "signature": body["signature"]
            }
        wallet = authenticate(request, **auth_kwargs)
        if not wallet:
            return JsonResponse(data={"success": False, "message": constants.MESSAGE_STATUS_401}, status=401)
        if not wallet.is_active:
            return JsonResponse(data={"success": False, "message": constants.MESSAGE_STATUS_403}, status=403)
        auth_login(request, wallet)
        return JsonResponse(data={"success": True, "message": constants.MESSAGE_STATUS_200("login")}, status=200)
    
    except Exception as e: 
        data, status = utils._handle_exception(e)
        return JsonResponse(data=data, status=status)


@csrf_decorator
@require_http_methods(["POST"])
def logout(request):
    """
    Handle user logout.

    Logs out the authenticated user and returns a JSON response
    with the logout status.

    Possible HTTP statuses:
    - 200 OK: Successful logout
    - 500 Internal Server Error: Unexpected error during logout
    """
    try:
        auth_logout(request)
        return JsonResponse(data={"success": True, "message": constants.MESSAGE_STATUS_200("logout")})
    except Exception as e: 
        data, status = utils._handle_exception(e)
        return JsonResponse(data=data, status=status)


@csrf_decorator
@require_http_methods(["GET"])
def nonce(request):
    """
    Generate and return a nonce for use in SIWE message.

    Generates a random nonce, stores it in the database with an expiration time,
    and returns a JSON response containing the nonce.

    Possible HTTP statuses:
    - 200 OK: Successful nonce generation
    - 500 Internal Server Error: Unexpected error during nonce generation
    """
    try:
        now = datetime.now(tz=pytz.UTC)
        utils._scrub_nonce()
        n = models.Nonce.objects.create(value=secrets.token_hex(12), expiration=now + timedelta(hours=12))
        return JsonResponse(data={"success": True, "nonce": n.value})
    except Exception as e: 
        data, status = utils._handle_exception(e)
        return JsonResponse(data=data, status=status)
    

@csrf_decorator
@require_http_methods(["GET"])
def verify(request):
    """
    Verify the user's authentication status.

    Checks if the user is authenticated and returns a JSON response
    with the verification status.

    Possible HTTP statuses:
    - 200 OK: User is authenticated
    - 401 Unauthorized: User is not authenticated
    - 500 Internal Server Error: Unexpected error during verification
    """
    try:
        if not request.user.is_authenticated:
            return JsonResponse(data={"success": False, "message": constants.MESSAGE_STATUS_401}, status=401)
        return JsonResponse(data={"success": True, "message": constants.MESSAGE_STATUS_200("session verify")}, status = 200)
    except Exception as e: 
        data, status = utils._handle_exception(e)
        return JsonResponse(data=data, status=status)
    

@csrf_decorator
@require_http_methods(["POST"])
def refresh(request):
    """
    Refresh the user's session.

    Updates the session authentication hash to prevent session expiration
    and returns a JSON response with the refresh status.

    Possible HTTP statuses:
    - 200 OK: Successful session refresh
    - 401 Unauthorized: User is not authenticated
    - 500 Internal Server Error: Unexpected error during session refresh
    """
    try:
        if not request.user.is_authenticated:
            return JsonResponse(data={"success": False, "message": constants.MESSAGE_STATUS_401}, status=401)
        update_session_auth_hash(request, request.user)
        return JsonResponse(data={"success": True, "message": constants.MESSAGE_STATUS_200("session refresh")}, status = 200)
    except Exception as e: 
        data, status = utils._handle_exception(e)
        return JsonResponse(data=data, status=status)
    

@csrf_decorator
@require_http_methods(["GET"])
def me(request):
    """
    Retrieve information about the authenticated user.

    Retrieves and returns user information in a JSON response.

    Possible HTTP statuses:
    - 200 OK: Successful retrieval of user information
    - 401 Unauthorized: User is not authenticated
    - 500 Internal Server Error: Unexpected error during retrieval
    """
    try:
        if not request.user.is_authenticated:
            return JsonResponse(data={"success": False, "message": constants.MESSAGE_STATUS_401}, status=401)
        wallet = utils._wallet_to_dict(request.user)
        return JsonResponse(data={"success": True, "wallet": wallet}, status = 200)
    except Exception as e: 
        data, status = utils._handle_exception(e)
        return JsonResponse(data=data, status=status)
