import indy
from indy import wallet
import asyncio

async def login(me, key):
    wallet_config = '{"id": "%s-wallet"}' % me
    wallet_credentials = '{"key": "%s"}' % key
    print(wallet_config, wallet_credentials)
    wallet_handle = None
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
    
    return wallet_handle

loginText = "eva"
passwordText = "eva1"

loop = asyncio.get_event_loop()
wallet_handle = loop.run_until_complete(login(loginText, passwordText))

print(wallet_handle)