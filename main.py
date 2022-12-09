import asyncio
import time
import re

from indy import crypto, did, wallet
from multiprocessing import Process
import threading





async def init():
    wallet_config = '{"id": "%s-wallet"}'
    wallet_credentials = '{"key": "%s-wallet-key"}'
    try:
        await wallet.create_wallet(wallet_config, wallet_credentials)
        print("wallet created")
    except:
        pass
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
    print('wallet = %s' % wallet_handle)
    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, "{}")
    print('my_did and verkey = %s %s' % (my_did, my_vk))
    #else:
        #did_vk = input("Your DID and verkey? ").strip().split(' ')
        #my_did = did_vk[0]
        #my_vk = did_vk[1]
    return wallet_handle, my_did, my_vk


    
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
    
    

        


async def demo():
    wallet_handle, my_did, my_vk = await init()
    # task1 = asyncio.create_task(read_infinite(wallet_handle, my_vk))
    # task2 = asyncio.create_task(demo_infinite(wallet_handle, my_did, my_vk, their_did, their_vk))
    # await task1
    # await task2

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(demo())
        time.sleep(1)  # waiting for libindy thread complete
    except KeyboardInterrupt:
        print('')
