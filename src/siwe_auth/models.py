"""
Django models for SIWE Authentication.

This module defines Django models for managing user authentication using Ethereum wallet addresses. It includes an abstract base class `AbstractWallet`, a concrete implementation `Wallet`, and a `Nonce` model for handling nonce values.

Classes:
- `WalletManager`: Custom manager for creating user instances with Ethereum addresses.
- `AbstractWallet`: Abstract base class for user authentication with Ethereum wallet addresses.
- `Wallet`: Concrete implementation of `AbstractWallet` for representing user wallets.
- `Nonce`: Model for storing nonce values used in the authentication process.

Note: The `AbstractWallet` class extends Django's `AbstractBaseUser` and `PermissionsMixin` to provide essential functionality for user authentication.
"""

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.db import models
from web3 import Web3

from siwe_auth import constants


def validate_ethereum_address(value):
    if not Web3.is_checksum_address(value):
        raise ValidationError(constants.ERROR_INVALID_ADDRESS)


class WalletManager(BaseUserManager):
    def create_user(self, ethereum_address: str):
        """
        Creates and saves a User with the given ethereum address.
        """
        if not ethereum_address:
            raise ValueError(constants.ERROR_INVALID_ADDRESS)

        wallet = self.model()
        wallet.ethereum_address = ethereum_address

        wallet.save(using=self._db)
        return wallet

    def create_superuser(self, ethereum_address: str,  **extra_fields):
        """
        Creates and saves a superuser with the given ethereum address and password.
        """
        user = self.create_user(
            ethereum_address=ethereum_address,
        )
        user.set_password(extra_fields.get('password'))
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class AbstractWallet(AbstractBaseUser, PermissionsMixin):
    """
    EIP-55 compliant: https://eips.ethereum.org/EIPS/eip-55
    """
    ethereum_address = models.CharField(
        unique=True,
        primary_key=True,
        max_length=42,
        validators=[validate_ethereum_address],
    )
    ens_name = models.CharField(max_length=255, blank=True, null=True)
    ens_avatar = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField("datetime created", auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = "ethereum_address"

    objects = WalletManager()
    
    class Meta:
        abstract = True

    def __str__(self):
        return self.ethereum_address

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin
    

class Wallet(AbstractWallet):
    """
    Wallet within the SIWE authentication system are represented by this
    model.
    
    Ethereum address is required. Other fields are optional.
    """
    
    class Meta(AbstractWallet.Meta):
        swappable = "AUTH_USER_MODEL"
        

class Nonce(models.Model):
    value = models.CharField(max_length=24, primary_key=True)
    expiration = models.DateTimeField()

    def __str__(self):
        return self.value
