from datetime import datetime
import logging
import re

from django.contrib.auth import models as auth_models
from django.forms import model_to_dict
import pytz
from web3 import HTTPProvider

from siwe_auth import groups, models, constants


# Dictionary formatters:
def _dict_camel_case_to_snake_case(data: dict) -> dict:
    """
    Converts keys in dictionary from camel case to snake case.
    """
    return {
        re.sub(r"(?<!^)(?=[A-Z])", "_", k).lower(): v
        for k, v in data.items()
    }
# ----------------------------------------------------------------- #

# Error formatters:
def _format_value_error(errors: tuple) -> list:
    formatted_errors = []
    for e in errors:
        loc = ".".join(map(str, e["loc"]))
        formatted_errors.append({"message": e['msg'], "field": f"message.{loc}"})
    return formatted_errors

def _format_key_error(args: tuple) -> list:
    formatted_errors = []
    for a in args:
        formatted_errors.append({"message": "field is required", "field": a})
    return formatted_errors

def _format_errors(e: Exception) -> list:
    """
    Format Exceptions include them on API responses.
    """
    if isinstance(e, KeyError):
        return _format_key_error(e.args)
    if isinstance(e, ValueError) and e.__cause__:
        return _format_value_error(e.__cause__.errors())
    return [{"message": msg} for msg in e.args]
# ----------------------------------------------------------------- #

# Exepction handlers:
def _handle_exception(e: Exception):
    """
    Handle exceptions and format them for API responses.
    """
    status=500
    errors = [{"message": msg} for msg in list(e.args)]
    message = constants.MESSAGE_STATUS_500  
    if isinstance(e, (KeyError, ValueError)):
        status=400
        message = constants.MESSAGE_STATUS_400
        errors = _format_errors(e)
    data = {
        "success": False, 
        "message": message, 
        "errors":errors
        }
    return data, status
# ----------------------------------------------------------------- #

# Wallet utils:
def _wallet_to_dict(wallet: models.Wallet) -> dict:
    """
    Convert a Wallet model instance to a dictionary with selected fields.
    """
    wallet_fields=["ethereum_address", "ens_name", "ens_avatar", "is_active", "is_admin", "is_superuser", "groups"]
    group_fields=["id", "name"]
    
    wallet = model_to_dict(wallet, wallet_fields)
    wallet["groups"] = [model_to_dict(group, fields=group_fields) for group in wallet["groups"]]
    
    return wallet

def _check_group(custom_group: tuple, wallet: models.Wallet, provider: HTTPProvider):
    """
    Check if the wallet is a member of a custom group and update its group membership.
    Custom group is created if it not exists.
    """
    name: str = custom_group[0]
    manager: groups.GroupManager = custom_group[1]
    
    group, created = auth_models.Group.objects.get_or_create(name=name)
    if created:
        logging.info(f"Created group '{name}'.")

    if manager.is_member(wallet=wallet, provider=provider):
        logging.info(
                    f"Adding wallet '{wallet.ethereum_address}' to group '{name}'."
                )
        wallet.groups.add(group)
    else:
        logging.info(
                    f"Removing wallet '{wallet.ethereum_address}' from group '{name}'."
                )
        wallet.groups.remove(group)
# ----------------------------------------------------------------- #
       
# Nonce utils:
def _scrub_nonce():
    """
    Delete all expired nonce's
    """
    for n in models.Nonce.objects.filter(expiration__lte=datetime.now(tz=pytz.UTC)):
        n.delete()
        
def _nonce_is_valid(nonce: str) -> bool:
    """
    Check if given nonce exists and has not yet expired.
    :param nonce: The nonce string to validate.
    :return: True if valid else False.
    """
    try:
        n = models.Nonce.objects.get(value=nonce)
        is_valid = False
        if n.expiration > datetime.now(tz=pytz.UTC):
            is_valid = True
        n.delete()
        return is_valid
    except models.Nonce.DoesNotExist:
        return False
