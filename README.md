# Siwe Authentication - Django
[![GitHub Stars](https://img.shields.io/github/stars/giovaborgogno/siwe-auth-django.svg?style=flat&label=Stars)](https://github.com/giovaborgogno/siwe-auth-django/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/giovaborgogno/siwe-auth-django.svg?style=flat&label=Forks)](https://github.com/giovaborgogno/siwe-auth-django/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/giovaborgogno/siwe-auth-django.svg?style=flat&label=Issues)](https://github.com/giovaborgogno/siwe-auth-django/issues)
[![PyPI Version](https://img.shields.io/pypi/v/siwe-auth-django.svg?style=flat&label=PyPI%20Version)](https://pypi.org/project/siwe-auth-django/)
[![GitHub Release Date](https://img.shields.io/github/release-date/giovaborgogno/siwe-auth-django.svg?style=flat&label=Released)](https://github.com/giovaborgogno/siwe-auth-django/releases)

Siwe Authentication is a Django app designed for Ethereum-based authentication using the Sign-In with Ethereum (EIP-4361) standard. It allows users to sign in using their Ethereum wallets, and provides flexible settings for customization.

## Table Of Contents

1. [Get Started](#get-started)
    1. [Installation](#installation)
    2. [Configuration](#configuration)
        - [Add 'siwe_auth' to your INSTALLED_APPS in settings.py](#add-siwe_auth-to-your-installed_apps-in-settingspy)
        - [Add authentication configs in settings.py](#add-authentication-configs-in-settingspy)
        - [Add 'SIWE_AUTH' config in settings.py](#add-siwe_auth-config-in-settingspy)
        - [Include the Siwe Authentication URLs in your project's urls.py](#include-the-siwe-authentication-urls-in-your-projects-urlspy)
    3. [Run migrations](#run-migrations)
2. [Usage](#usage)
3. [Custom Groups](#custom-groups)
4. [Django User Model](#django-user-model)
5. [Contrubuting](#contributing)
6. [License](#license)

## Get Started

### Installation

Install the package using pip:

```bash
pip install siwe-auth-django
```

### Configuration


#### Add `'siwe_auth'` to your INSTALLED_APPS in settings.py:

```python
# settings.py

INSTALLED_APPS = [
    # ...
    'siwe_auth',
    # ...
]
```

#### Add authentication configs in settings.py:

```python
# settings.py

AUTH_USER_MODEL = "siwe_auth.Wallet"
AUTHENTICATION_BACKENDS = [
    "siwe_auth.backends.SiweBackend", 
    "django.contrib.auth.backends.ModelBackend" # this is necessary if you want to use superusers in django admin authentication
    ]
SESSION_COOKIE_AGE = 3 * 60 * 60 
```

If you need to create a different auth user model refer to [Django User Model](#django-user-model) section.

#### Add `SIWE_AUTH` config in settings.py:

Available settings:

`"CSRF_EXEMPT"`: Flag indicating whether CSRF protection is exempted for Siwe Authentication views (if you are creating an REST API must be `True`).  
`"PROVIDER"`: Ethereum provider URL (it is required).  
`"CREATE_GROUPS_ON_AUTH"`: Flag indicating whether to create groups on user authentication.  
`"CREATE_ENS_PROFILE_ON_AUTH"`: Flag indicating whether to create ENS profiles on user authentication.  
`"CUSTOM_GROUPS"`: List of custom groups to be created on user authentication. If you need to create more group manager refer to [Custom Groups](#custom-groups) section.

```python
# settings.py

from siwe_auth import group # needed if you want to set custom groups

# ...

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

#### Include the Siwe Authentication URLs in your project's urls.py:

```python
# urls.py

from django.urls import include, path

urlpatterns = [
    # ...
    path('api/auth', include('siwe_auth.urls', namespace='siwe_auth')),
    # ...
]
```

- ### Run migrations:

```bash
python manage.py migrate
```

## Usage

You need to follow this steps to successful authentication using SIWE protocol (EIP-4361):

1. Get nonce: GET Method `/api/auth/nonce`.
2. Use that nonce to create a SIWE message in frontend and sign the message with your metamask or another wallet.
3. Login: POST Method `/api/auth/login`, using the message and signature. Body of request example:
```json
# body:
{
    "message": {
        "domain": "your_domain.com",
        "address": "0xA8f1...61905",
        "statement": "This is a test statement.",
        "uri": "https://your_domain.com",
        "version": "1",
        "chainId": 1,
        "nonce": "2483e73dedffbd2616773506",
        "issuedAt": "2024-01-27T18:43:48.011Z"
    },
    "signature": "0xf5b4ea...7bda4e177276dd1c"
}
```
4. Now you have the sessionid in cookies so you can use it for authenticated required views.
5. Refresh the sessionid: POST Method `api/auth/refresh`.
6. Verify if you are authenticated: GET Method `api/auth/verify`.
7. Logout: POST Method `api/auth/logout`

## [Custom Groups](/src/siwe_auth/groups.py)

There are 3 custom group managers by default:  
`ERC20OwnerManager`  
`ERC721OwnerManager`  
`ERC1155OwnerManager`  

You can create more groups managers by extending the `GroupManager` class:
```python
from web3 import HTTPProvider
from siwe_auth.groups import GroupManager

class MyCustomGroup(GroupManager):
    def __init__(self, config: dict):
        # Your custom logic
        pass

    def is_member(self, wallet: object, provider: HTTPProvider) -> bool:
        # Your custom logic to determine membership
        pass
```

You can create custom groups in your settings.py:
```python
# settings.py

from siwe_auth import group # needed if you want to set custom groups

# ...

SIWE_AUTH = {
    # ...
    "CUSTOM_GROUPS": [
        ("usdt_owners", groups.ERC20OwnerManager(config={'contract': '0x82E...550'})),
        ("nft_owners", groups.ERC721OwnerManager(config={'contract': '0x785...3A5'})),
        ("token_owners", groups.ERC1154OwnerManager(config={'contract': '0x872...5F5'})),
        # ...
    ], # default []
}
``` 
Then you can manage these groups with the django GroupManager, example:
```python
from django.contrib.auth.models import Group
# ...

usdt_owners_group = Group.objects.get(name='usdt_owners')
all_usdt_owners = usdt_owners_group.user_set.all()
# ...
```

## [Django User Model](/src/siwe_auth/models.py)

By default, Siwe Authentication uses the `Wallet` model as the user model. If you prefer to use a specific user model, you can either use the provided `AbstractWallet` model or create your own user model. For more details, refer to the [Configuration](#configuration) section.

```python
# Django project models.py

from siwe_auth.models import AbstractWallet

class MyUserModel(AbstractWallet):
    # Add your custom fields here
    pass
```

## Contributing
Contributions are welcome! Please create issues for bugs or feature requests. Pull requests are encouraged.

## [License](/LICENSE)
This project is licensed under the MIT License - see the LICENSE file for details.