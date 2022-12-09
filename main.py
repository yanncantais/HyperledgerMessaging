import asyncio
import time
import re

from indy import crypto, did, wallet
from multiprocessing import Process
import threading



async def write(wallet_handle, my_vk, their_vk, msg):
    msg = bytes(msg, "utf-8")
    encrypted = await crypto.auth_crypt(wallet_handle, my_vk, their_vk, msg)
    # encrypted = await crypto.anon_crypt(their_vk, msg)
    print('encrypted = %s' % repr(encrypted))
    with open('message.dat', 'wb') as f:
        f.write(encrypted)
    print('writing %s' % msg)

async def init():
    new = input("Are you new ? [Y/n]").lower()
    while new not in ["y", "n", ""]:
        new = input("Incorrect command.\nAre you new ? [Y/n] ").lower()
    me = input('Who are you? ').strip()
    wallet_config = '{"id": "%s-wallet"}' % me
    wallet_credentials = '{"key": "%s-wallet-key"}' % me
    # 1. Create Wallet and Get Wallet Handle
    try:
        await wallet.create_wallet(wallet_config, wallet_credentials)
        print("yes")
    except:
        pass
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)   
    if re.match(new, "y") or re.match(new, ""):       
        print('wallet = %s' % wallet_handle)    
        (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, "{}")
        print('my_did and verkey = %s %s' % (my_did, my_vk))
    else:
        did_vk = input("Your DID and verkey? ").strip().split(' ')
        my_did = did_vk[0]
        my_vk = did_vk[1]   
    their = input("Other party's DID and verkey? ").strip().split(' ')
    return wallet_handle, my_did, my_vk, their[0], their[1]


    
async def run_read(wallet_handle, my_vk, interval=1):
    while True:
        await read(wallet_handle, my_vk)
        time.sleep(interval)
        
        
    thread = threading.Thread(target=run2, args=(wallet_handle, my_vk, interval))
    thread.daemon = True
    thread.start()
async def run_demo(wallet_handle, my_did, my_vk, their_did, their_vk):
    while True:
        argv = input('> ').strip().split(' ')
        cmd = argv[0].lower()
        rest = ' '.join(argv[1:])
        if re.match(cmd, 'write'):
            await write(wallet_handle, my_vk, their_vk, rest)
        elif re.match(cmd, 'read'):
            await read(wallet_handle, my_vk)
        elif re.match(cmd, 'quit'):
            break
        else:
            print('Huh?')

async def read(wallet_handle, my_vk):
    with open('message.dat', 'rb') as f:
        encrypted = f.read()
    decrypted = await crypto.auth_decrypt(wallet_handle, my_vk, encrypted)
    # decrypted = await crypto.anon_decrypt(wallet_handle, my_vk, encrypted)
    print(decrypted)
    
    
async def read_infinite(wallet_handle, my_vk):
    while True:
        print("try")
        try:
            await read(wallet_handle, my_vk)
        except:
            pass
            time.sleep(1)
        
async def demo_infinite(wallet_handle, my_did, my_vk, their_did, their_vk):
    while True:
        argv = input('> ').strip().split(' ')
        cmd = argv[0].lower()
        rest = ' '.join(argv[1:])
        if re.match(cmd, 'prep'):
            await prep(wallet_handle, my_vk, their_vk, rest)
        elif re.match(cmd, 'read'):
            await read(wallet_handle, my_vk)
        elif re.match(cmd, 'quit'):
            break
        else:
            print('Huh?')

async def demo():
    wallet_handle, my_did, my_vk, their_did, their_vk = await init()
    # task1 = asyncio.create_task(read_infinite(wallet_handle, my_vk))
    # task2 = asyncio.create_task(demo_infinite(wallet_handle, my_did, my_vk, their_did, their_vk))
    # await task1
    # await task2
    await asyncio.gather(read_infinite(wallet_handle, my_vk), demo_infinite(wallet_handle, my_did, my_vk, their_did, their_vk))  

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(demo())
        time.sleep(1)  # waiting for libindy thread complete
    except KeyboardInterrupt:
        print('')
