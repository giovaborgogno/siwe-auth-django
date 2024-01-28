# views.py
# Rest API response messages:
MESSAGE_STATUS_200 = lambda msg: f"Successful {msg}."
MESSAGE_STATUS_400 = "One or more validation errors occurred."
MESSAGE_STATUS_401 = "Authentication credentials were missing or incorrect."
MESSAGE_STATUS_403 = "The request is understood, but it has been refused or access is not allowed."
MESSAGE_STATUS_500 = "Something went wrong."


# ValueErrors:
ERROR_CONFIG = lambda name, attribute: f"{name} Owner Manager config is missing {attribute} attribute."
ERROR_UNABLE_TO_VERIFY_MEMBERSHIP = lambda address: f"Unable to verify membership of invalid address: {address}."
ERROR_INVALID_ADDRESS = "Ethereum address is required. Please provide a valid checksum address."

# groups.py
# Contract ABIs:
ERC1155_ABI = [{
        "constant": False,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_id", "type": "uint256"},
        ],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "type": "function"
        }]

ERC721_ABI = [{
        "constant": False,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "type": "function",
        }]

ERC20_ABI = [{
        "constant": False,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "type": "function",
        }]
