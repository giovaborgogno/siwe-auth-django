"""
Siwe Authentication Settings.

This module defines the Siwe Authentication settings and provides a mechanism for lazy loading and reloading settings.

Settings:
- `CSRF_EXEMPT`: Flag indicating whether CSRF protection is exempted for Siwe Authentication views.
- `PROVIDER`: Ethereum provider URL.
- `CREATE_GROUPS_ON_AUTH`: Flag indicating whether to create groups on user authentication.
- `CREATE_ENS_PROFILE_ON_AUTH`: Flag indicating whether to create ENS profiles on user authentication.
- `CUSTOM_GROUPS`: List of custom groups to be created on user authentication.

Note: These settings can be configured in Django project settings using the `SIWE_AUTH` namespace.

Example Configuration:
```python
# Django project settings.py
from siwe_auth import groups

SIWE_AUTH = {
    "CSRF_EXEMPT": True, # default False
    "PROVIDER": "https://mainnet.infura.io/v3/...", # required
    "CREATE_GROUPS_ON_AUTH": True, # default False
    "CREATE_ENS_PROFILE_ON_AUTH": True, # default True
    "CUSTOM_GROUPS": [
        ("usdt_owners", groups.ERC20OwnerManager(config={'contract': '0x82E...550'})),
        ("nft_owners", groups.ERC721OwnerManager(config={'contract': '0x785...3A5'})),
        # ...
    ], # default []
}
```
"""

from django.conf import settings as django_settings
from django.test.signals import setting_changed
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string

SIWE_AUTH_SETTINGS_NAMESPACE = "SIWE_AUTH"

default_settings = {
    "CSRF_EXEMPT": False,
    "PROVIDER": None,
    "CREATE_GROUPS_ON_AUTH": False,
    "CREATE_ENS_PROFILE_ON_AUTH": True,
    "CUSTOM_GROUPS": []
}

SETTINGS_TO_IMPORT = []

class Settings:
    def __init__(self, default_settings, explicit_overriden_settings: dict = None):
        if explicit_overriden_settings is None:
            explicit_overriden_settings = {}

        overriden_settings = (
            getattr(django_settings, SIWE_AUTH_SETTINGS_NAMESPACE, {})
            or explicit_overriden_settings
        )

        self._load_default_settings(default_settings)
        self._override_settings(overriden_settings)
        self._init_settings_to_import()

    def _load_default_settings(self, default_settings):
        for setting_name, setting_value in default_settings.items():
            if setting_name.isupper():
                setattr(self, setting_name, setting_value)

    def _override_settings(self, overriden_settings: dict):
        for setting_name, setting_value in overriden_settings.items():
            value = setting_value
            setattr(self, setting_name, value)
            
    def _init_settings_to_import(self):
        for setting_name in SETTINGS_TO_IMPORT:
            value = getattr(self, setting_name)
            if isinstance(value, str):
                setattr(self, setting_name, import_string(value))

                
class LazySettings(LazyObject):
    def _setup(self, explicit_overriden_settings=None):
        self._wrapped = Settings(default_settings, explicit_overriden_settings)
        
settings = LazySettings()


def reload_siwe_auth_settings(*args, **kwargs):
    global settings
    setting, value = kwargs["setting"], kwargs["value"]
    if setting == SIWE_AUTH_SETTINGS_NAMESPACE:
        settings._setup(explicit_overriden_settings=value)


setting_changed.connect(reload_siwe_auth_settings)
        