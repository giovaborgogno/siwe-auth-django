"""
Group Managers for SIWE Authentication.

This module provides abstract classes and implementations for managing membership in groups based on Ethereum token standards such as ERC-20, ERC-1155, and ERC-721.

Classes:
- `GroupManager`: Abstract base class defining the interface for group managers.
- `ERC1155Manager`: Abstract base class for managing membership based on ERC-1155 token standard.
- `ERC1155OwnerManager`: Implementation of `ERC1155Manager` for checking ownership in ERC-1155 token standard.
- `ERC20Manager`: Abstract base class for managing membership based on ERC-20 token standard.
- `ERC20OwnerManager`: Implementation of `ERC20Manager` for checking ownership in ERC-20 token standard.
- `ERC721Manager`: Abstract base class for managing membership based on ERC-721 token standard.
- `ERC721OwnerManager`: Implementation of `ERC721Manager` for checking ownership in ERC-721 token standard.

Note: All classes extend the `GroupManager` abstract class and implement the `is_member` method to determine group membership.
"""

from abc import ABC, abstractmethod
import logging
from typing import Callable

from web3 import Web3, HTTPProvider

from siwe_auth import constants


class GroupManager(ABC):
    @abstractmethod
    def __init__(self, config: dict):
        """
        GroupManager initialization function.
        :param config: Dictionary for passing in any dependencies such as contract address or list of valid addresses.
        """
        pass

    @abstractmethod
    def is_member(self, wallet: object, provider: HTTPProvider) -> bool:
        """
        Membership function to identify if a given ethereum address is part of this class' group.
        :param provider: Web3 provider to use for membership check.
        :param wallet: Object with ethereum_address attribute to check membership of.
        :return: True if address is a member else False
        """
        pass

    def _valid_wallet(self, wallet: object):
        return wallet.__getattribute__('ethereum_address') is not None
    

class ERC1155Manager(GroupManager):

    contract: str
    token_id: int
    abi = constants.ERC1155_ABI

    def __init__(self, config: dict):
        if "contract" not in config:
            raise ValueError(constants.ERROR_CONFIG("ERC1155", "contract"))
        if "token_id" not in config:
            raise ValueError(constants.ERROR_CONFIG("ERC1155", "token_id"))
        self.contract = config["contract"]
        self.token_id = int(config["token_id"])

    def _is_member(
        self,
        ethereum_address: str,
        provider: HTTPProvider,
        expression: Callable[[str], bool],
    ):
        w3 = Web3(provider)
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(self.contract.lower()), abi=self.abi
        )
        balance = contract.functions.balanceOf(
            _owner=Web3.to_checksum_address(ethereum_address.lower()),
            _id=self.token_id,
        ).call()
        return expression(balance)

    @abstractmethod
    def is_member(self, wallet: object, provider: HTTPProvider) -> bool:
        pass


class ERC1155OwnerManager(ERC1155Manager):
    def is_member(self, wallet: object, provider: HTTPProvider) -> bool:
        if not self._valid_wallet(wallet=wallet):
            return False
        try:
            return self._is_member(
                ethereum_address=wallet.ethereum_address,
                provider=provider,
                expression=lambda x: x > 0,
            )
        except ValueError:
            logging.error(constants.ERROR_UNABLE_TO_VERIFY_MEMBERSHIP(wallet.ethereum_address))
        return False
    
    
class ERC20Manager(GroupManager):
    contract: str
    abi = constants.ERC20_ABI

    def __init__(self, config: dict):
        if "contract" not in config:
            raise ValueError(constants.ERROR_CONFIG("ERC20", "contract"))
        self.contract = config["contract"]

    def _is_member(
        self,
        ethereum_address: str,
        provider: HTTPProvider,
        expression: Callable[[str], bool],
    ):
        w3 = Web3(provider)
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(self.contract.lower()), abi=self.abi
        )
        balance = contract.functions.balanceOf(
            _owner=Web3.to_checksum_address(ethereum_address.lower())
        ).call()
        return expression(balance)

    @abstractmethod
    def is_member(self, wallet: object, provider: HTTPProvider) -> bool:
        pass


class ERC20OwnerManager(ERC20Manager):
    def is_member(self, wallet: object, provider: HTTPProvider) -> bool:
        if not self._valid_wallet(wallet=wallet):
            return False
        try:
            return self._is_member(
                ethereum_address=wallet.ethereum_address,
                provider=provider,
                expression=lambda x: x > 0,
            )
        except ValueError:
            logging.error(constants.ERROR_UNABLE_TO_VERIFY_MEMBERSHIP(wallet.ethereum_address))
        return False
    

class ERC721Manager(GroupManager):
    contract: str
    abi = constants.ERC721_ABI

    def __init__(self, config: dict):
        if "contract" not in config:
            raise ValueError(constants.ERROR_CONFIG("ERC721", "contract"))
        self.contract = config["contract"]

    def _is_member(
        self,
        ethereum_address: str,
        provider: HTTPProvider,
        expression: Callable[[str], bool],
    ):
        w3 = Web3(provider)
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(self.contract.lower()), abi=self.abi
        )
        balance = contract.functions.balanceOf(
            _owner=Web3.to_checksum_address(ethereum_address.lower())
        ).call()
        return expression(balance)

    @abstractmethod
    def is_member(self, wallet: object, provider: HTTPProvider) -> bool:
        pass


class ERC721OwnerManager(ERC721Manager):
    def is_member(self, wallet: object, provider: HTTPProvider) -> bool:
        if not self._valid_wallet(wallet=wallet):
            return False
        try:
            return self._is_member(
                ethereum_address=wallet.ethereum_address,
                provider=provider,
                expression=lambda x: x > 0,
            )
        except ValueError:
            logging.error(constants.ERROR_UNABLE_TO_VERIFY_MEMBERSHIP(wallet.ethereum_address))
        return False
