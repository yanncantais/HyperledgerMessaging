from aries_cloudagent.wallet.indy import IndySdkWallet, IndyOpenWallet
import asyncio
from indy import crypto, did, wallet

import time

import json


# async def test():
#     me="tanguy"
#     wallet_config = '{"id": "%s-wallet"}' % me
#     wallet_credentials = '{"key": "%s"}' % me
#     wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
#     key_json = '{}'
#     key = await crypto.create_key(wallet_handle, key_json)
#     print(key)
#     await wallet.close_wallet(wallet_handle)

#     me="yann"
#     wallet_config = '{"id": "%s-wallet"}' % me
#     wallet_credentials = '{"key": "%s"}' % me
#     wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)  
#     MyWallet = IndyOpenWallet(handle = wallet_handle, config = {}, created = "", master_secret_id="")
#     Wallet = IndySdkWallet(MyWallet)
#     await wallet.close_wallet(wallet_handle)
#     a = await Wallet.pack_message(message = "message", to_verkeys = [key])
    
#     print(a)
#     me="tanguy"
#     wallet_config = '{"id": "%s-wallet"}' % me
#     wallet_credentials = '{"key": "%s"}' % me
#     wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
#     decrypted = await crypto.unpack_message(wallet_handle, a)
#     await wallet.close_wallet(wallet_handle)
#     print(decrypted)
    
    
    
# loop = asyncio.get_event_loop()
# loop.run_until_complete(test())

async def test2():
    me="tanguy"
    wallet_config = '{"id": "%s-wallet"}' % me
    wallet_credentials = '{"key": "%s"}' % me
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
    # key = await crypto.create_key(wallet_handle, "{}")
    did_json = "{}"
    (mydid, verkey) = await did.create_and_store_my_did(wallet_handle = wallet_handle, did_json = did_json)
    await wallet.close_wallet(wallet_handle)
    print("My DID: ",mydid)
    print("My verkey: ",verkey)


    me="yann"
    wallet_config = '{"id": "%s-wallet"}' % me
    wallet_credentials = '{"key": "%s"}' % me
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)  
    

    identity_json = '{"did": "'+mydid+'", "verkey": "'+verkey+'"}'
    res = await did.store_their_did(wallet_handle, identity_json)
    print(res)
    
    
    await wallet.close_wallet(wallet_handle)
    me="yann"
    wallet_config = '{"id": "%s-wallet"}' % me
    wallet_credentials = '{"key": "%s"}' % me
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)  
    
    DIDs = await did.list_my_dids_with_meta(wallet_handle)
    DIDs = json.loads(DIDs)
    for DID in DIDs:
        print(DID)
    
    
       
    #time.sleep(1)
    await did.set_did_metadata(wallet_handle, did = mydid, metadata = "tanguy")
    
    
    
    metadata = await did.get_did_metadata(wallet_handle, mydid)
    print(metadata)
    
    DIDs = await did.list_my_dids_with_meta(wallet_handle)
    DIDs = json.loads(DIDs)
    for DID in DIDs:
        # print(DID)

        if DID["metadata"] == "tanguy":
            verkey = await did.key_for_local_did(wallet_handle, DID["did"])
            break
    
    
    a = await crypto.pack_message(wallet_handle = wallet_handle, message = "message", recipient_verkeys = [verkey], sender_verkey=None)    
    await wallet.close_wallet(wallet_handle)
    
    
    # DID = await did.list_my_dids_with_meta(wallet_handle)
    # print(DID)
    
    
    # identity_json = '{"did": "Ei143Ar21UaPtpkGdqdVte", "verkey": "8UJYf4DCXbTjQ2GQQsvYmYyWquQ9NC1Fx5v4RuqgApzs"}'
    # await did.store_their_did(wallet_handle, identity_json)
    
    # print(DID)
    me="tanguy"
    wallet_config = '{"id": "%s-wallet"}' % me
    wallet_credentials = '{"key": "%s"}' % me
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
    time.sleep(2)
    decrypted = await crypto.unpack_message(wallet_handle, a)
    DID = await did.list_my_dids_with_meta(wallet_handle)
    # print(DID)
    await wallet.close_wallet(wallet_handle)
    print(decrypted)
    
    
    
    # {
    #    "did": string, (required)
    #    "verkey": string (optional, if only pk is provided),
    #    "crypto_type": string, (optional; if not set then ed25519 curve is used;
    #           currently only 'ed25519' value is supported for this field)
    # }
    
    
 
    
    
loop = asyncio.get_event_loop()
loop.run_until_complete(test2())

