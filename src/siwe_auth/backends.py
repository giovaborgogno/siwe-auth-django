"""
SIWE Authentication Backend

This module defines a custom authentication backend for Sign-In with Ethereum (SIWE) protocol.
The backend, `SiweBackend`, is responsible for authenticating users based on Ethereum addresses
and signatures following the EIP-4361 standard.

The backend utilizes Web3 and the SIWE library for Ethereum-related functionalities,
such as signature verification and nonce validation. Additionally, it supports the creation
of an Ethereum Name Service (ENS) profile for authenticated users.

File Structure:
- ENSProfile: Container for ENS profile information (name and avatar).
- SiweBackend: Custom authentication backend for SIWE protocol.

Authentication Workflow:
1. Validate the SIWE message signature using Web3 and SIWE library.
2. Verify the nonce to prevent replay attacks.
3. Retrieve or create a user wallet based on the Ethereum address.
4. Optionally create or update the user's ENS profile.
5. Perform any additional authentication-related tasks.

Exceptions Handled:
- ExpiredMessage: SIWE message has expired.
- InvalidSignature: Signature verification fails.
- MalformedSession: SIWE session is missing required fields.
- VerificationError: SIWE message is invalid.

Author: Giovanni Borgogno
Date: January 27th, 2024
"""

import datetime
import logging
from typing import Optional

from django.contrib.auth.backends import BaseBackend
from ens import ENS
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
import pytz
from siwe import (
    ExpiredMessage,
    InvalidSignature,
    MalformedSession,
    SiweMessage,
    VerificationError,
)

from siwe_auth import models, utils
from siwe_auth.conf import settings


class ENSProfile:
    """
    Container for ENS profile information including but not limited to primary name and avatar.
    """

    name: str = None
    avatar: str = None

    def __init__(self, ethereum_address: str, w3: Web3):
        ns = ENS.from_web3(w3)
        self.name = ns.name(address=ethereum_address)
        if self.name:
            self.avatar = ns.get_text(self.name, "avatar")
            

class SiweBackend(BaseBackend):
    """
    Authenticate an Ethereum address as per Sign-In with Ethereum (EIP-4361).
    """

    def authenticate(self, request, signature: str, siwe_message: SiweMessage):
        # Validate signature
        w3 = Web3(HTTPProvider(settings.PROVIDER))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        try:
            siwe_message.verify(signature=signature)
        except (ExpiredMessage, MalformedSession, InvalidSignature, VerificationError) as e:
            error_messages = {
                ExpiredMessage: "expired message",
                InvalidSignature: "invalid signature",
                MalformedSession: lambda er: f"missing fields: {', '.join(er.missing_fields)}",
                VerificationError: "invalid message",
                }

            error = error_messages.get(type(e), "unknown error")
            logging.debug(f"Authentication attempt rejected due to {error}.")
            return None

        # Validate nonce
        if not utils._nonce_is_valid(siwe_message.nonce):
            return None

        # Pull ENS data
        if settings.CREATE_ENS_PROFILE_ON_AUTH:
            ens_profile = ENSProfile(ethereum_address=siwe_message.address, w3=w3)
        else:
            ens_profile = ENSProfile.__new__(ENSProfile) # blank ENSProfile, skipping __init__ constructor


        # Message and nonce has been validated. Authentication complete. Continue with authorization/other.
        now = datetime.datetime.now(tz=pytz.UTC)
        try:
            wallet = models.Wallet.objects.get(ethereum_address=siwe_message.address)
            wallet.last_login = now
            wallet.ens_name = ens_profile.name
            wallet.ens_avatar = ens_profile.avatar
            wallet.save()
            logging.debug(f"Found wallet for address {siwe_message.address}")
        except models.Wallet.DoesNotExist:
            wallet = models.Wallet(
                ethereum_address=Web3.to_checksum_address(siwe_message.address),
                ens_name=ens_profile.name,
                ens_avatar=ens_profile.avatar,
                last_login=now,
                password=None,
            )
            wallet.set_unusable_password()
            wallet.save()
            logging.debug(
                f"Could not find wallet for address {siwe_message.address}. Creating new wallet object."
            )

        # Group settings
        if settings.CREATE_GROUPS_ON_AUTH and settings.CUSTOM_GROUPS:
            for custom_group in settings.CUSTOM_GROUPS:
                utils._check_group(custom_group, wallet, HTTPProvider(settings.PROVIDER))

        return wallet

    def get_user(self, ethereum_address: str) -> Optional[models.Wallet]:
        """
        Get Wallet by ethereum address if exists.
        :param ethereum_address: Ethereum address of user.
        :return: Wallet object if exists or None
        """
        try:
            return models.Wallet.objects.get(pk=ethereum_address)
        except models.Wallet.DoesNotExist:
            return None
