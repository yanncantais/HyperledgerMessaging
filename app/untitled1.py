#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 12:27:51 2023

@author: kali
"""

from aries_cloudagent.wallet.indy import IndySdkWallet, IndyOpenWallet
import asyncio
from indy import crypto, did, wallet

import time
import os
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

async def test2(sender, receiver):
    
    #SENDING OF THE DID/VERKEY
    wallet_config = '{"id": "%s-wallet"}' % sender
    wallet_credentials = '{"key": "%s"}' % sender
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
    did_json = "{}"
    (firstdid, firstverkey) = await did.create_and_store_my_did(wallet_handle = wallet_handle, did_json = did_json)
    await wallet.close_wallet(wallet_handle)
    print("My DID: ",firstdid)
    print("My verkey: ",firstverkey)


    #THE RECEIVER RECEIVE THE INVITATION AND STORE THE DID
    wallet_config = '{"id": "%s-wallet"}' % receiver
    wallet_credentials = '{"key": "%s"}' % receiver
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)  
    identity_json = '{"did": "'+firstdid+'", "verkey": "'+firstverkey+'"}' 
    await did.store_their_did(wallet_handle, identity_json)    
    path = receiver+"/their_dids.dat"
    if not os.path.isdir(receiver):
        os.mkdir(receiver)
    if not os.path.isfile(path):
        f = open(path, "w+")
    with open(path, "a") as output:
        output.write(sender+":"+firstdid+"\n")
    
    

    #THE RECEIVER WANTS TO SEND A MESSAGE TO THE SENDER

    path = receiver+"/their_dids.dat"
    f = open(path, "r")
    DIDs = f.read().split("\n")
    
    # DIDs = await did.list_my_dids_with_meta(wallet_handle)
    # DIDs = json.loads(DIDs)
    
    
    
    
    for DID in DIDs:
        if ":" not in DID:
            continue
        DID = DID.split(":")
        name = DID[0]
        their_did = DID[1]
        if name == sender:
            verkey = await did.key_for_local_did(wallet_handle, their_did)
            break
    encrypted_message = await crypto.pack_message(wallet_handle = wallet_handle, message = "ceci est un test", recipient_verkeys = [verkey], sender_verkey=None)    
    print(encrypted_message)
    await wallet.close_wallet(wallet_handle)
    
    
    #THE SENDER RECEIVES THE MESSAGE
    wallet_config = '{"id": "%s-wallet"}' % sender
    wallet_credentials = '{"key": "%s"}' % sender
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
    time.sleep(2)
    decrypted_message = await crypto.unpack_message(wallet_handle, encrypted_message)
    DID = await did.list_my_dids_with_meta(wallet_handle)
    await wallet.close_wallet(wallet_handle)
    print(decrypted_message)
    
    

 
    
    
loop = asyncio.get_event_loop()
loop.run_until_complete(test2("yann", "tanguy"))

