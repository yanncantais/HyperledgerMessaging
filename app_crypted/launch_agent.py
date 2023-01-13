import subprocess
import sys
import threading
from flask import Flask, request
import os
import requests
import asyncio
import json
from indy import did, crypto, wallet
import time

user = sys.argv[1]
pwd = sys.argv[2]


verkey_sent_label = "my verkey is:"
PortFound = False
if not os.path.isfile("ports.conf"):
    print("No ports.conf file found.")
    exit(1)
p = open("ports.conf", "r")
AgentsPorts = p.read().split("\n") 
p.close()
for port_line in AgentsPorts:
    if ":" in port_line:
        port_line_separated = port_line.split(":")
        agent = port_line_separated[0]
        port = int(port_line_separated[1])
        if agent == user:
            first_port = port
            PortFound = True
            break
if not PortFound:
    print("Your agent was not found.")
    exit(1)  
    

if not os.path.isdir(user):
    os.mkdir(user)


third_port = first_port + 6000


ask_verkey_label = "test"


async def login(me, key):
    wallet_config = '{"id": "%s-wallet"}' % me
    wallet_credentials = '{"key": "%s"}' % key
    print(wallet_config, wallet_credentials)
    wallet_handle = None
    try:        
        wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
        success = True
    except:
        success = False
    return success, wallet_handle


async def create_did(wallet_handle):
    DID, Verkey = await did.create_and_store_my_did(wallet_handle, '{}')
    return DID, Verkey

async def store_did(user, wallet_handle, contact, their_did, verkey):
    identity_json = '{"did": "'+their_did+'", "verkey": "'+verkey+'"}' 
    await did.store_their_did(wallet_handle, identity_json)    
    path = user+"/their_dids.did"
    if not os.path.isdir(user):
        os.mkdir(user)
    if not os.path.isfile(path):
        open(path, "w+")
    with open(path, "a") as output:
        output.write(contact+":"+their_did+"\n")


async def close_w(wallet_handle):
    await wallet.close_wallet(wallet_handle)


async def get_key(wallet_handle, their_did):
    verkey = await did.key_for_local_did(wallet_handle, their_did) 
    return verkey

async def encrypt_message(user, wallet_handle, verkey, message):
    encrypted_message = await crypto.pack_message(wallet_handle = wallet_handle, message = message, recipient_verkeys = [verkey], sender_verkey=None)    
    return encrypted_message

async def decrypt_message(wallet_handle, encrypted_message):
    encrypted_message = json.dumps(encrypted_message)
    encrypted_message = str.encode(encrypted_message)
    print(encrypted_message)
    decrypted_message = await crypto.unpack_message(wallet_handle, encrypted_message)
    print(decrypted_message)
    time.sleep(10)
    return decrypted_message





def flask_app():
    app_flask = Flask(__name__)        
    @app_flask.route('/webhooks/topic/basicmessages/', methods=['POST'])
    def webhook():
        data = request.get_json()
        connection_id = data["connection_id"]
        print(data["content"])
        content = data["content"]
        if verkey_sent_label in data["content"]:
            data["content"] = data["content"].replace(verkey_sent_label, "")
            data["content"] = json.loads(data["content"])
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, wallet_handle = loop.run_until_complete(login(user, pwd))
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            content = "test"
            message = loop.run_until_complete(decrypt_message(wallet_handle, data["content"]))
            message = message.decode()
            data = json.loads(message)
            content = data["message"]
            print(content)
            Data = content.split("/")
            contact = Data[0].split(":")[1]
            TheirDID = Data[1].split(":")[1]
            TheirVerkey = Data[2].split(":")[1]
            loop.run_until_complete(store_did(user, wallet_handle, contact, TheirDID, TheirVerkey))
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(close_w(wallet_handle))
            return "OK"
        elif data["content"] == ask_verkey_label:
            print(5)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, wallet_handle = loop.run_until_complete(login(user, pwd))
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            DID,Verkey = loop.run_until_complete(create_did(wallet_handle))
            print("message", DID, Verkey, "will be sent")
            Keys = 'name:'+user+'/did:'+DID+'/verkey:'+Verkey
            url = "http://0.0.0.0:"+str(second_port)+"/connections/"+connection_id+"/send-message" 
            r = requests.get("http://0.0.0.0:"+str(second_port)+"/connections").text
            r_json = json.loads(r)
            r_json = r_json["results"]
            label = None
            verkey = None
            for item in r_json:
                if item["rfc23_state"] == "completed":
                    label = item["their_label"]
                    break
            path = user+"/their_dids.did"
            print("label", label)
            if label is not None and os.path.isfile(path): 
                if ":" in label:
                    label = label.split(":")[0]
                f = open(path, "r")
                DIDs = f.read().split("\n")
                f.close()
                for DID in DIDs:
                    if ":" not in DID:
                        continue
                    DID = DID.split(":")
                    name = DID[0]
                    their_did = DID[1]
                    if name == label:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        verkey = loop.run_until_complete(get_key(wallet_handle, their_did))
                        break   
            print("verkey", verkey)
            if verkey is not None:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                Encrypted_Keys = loop.run_until_complete(encrypt_message(user, wallet_handle, verkey, Keys))
                verkey_sent_label_bytes = verkey_sent_label.encode()
                Message = {"content": verkey_sent_label_bytes+Encrypted_Keys}
                response = requests.post(url, json = Message)
            else:
                response = requests.post(url, json = {"content": Keys})
            print(response.text)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(close_w(wallet_handle))
            return "OKs"
        elif "did:" in content and "verkey:" in content and "name:" in content:    
            print(6)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, wallet_handle = loop.run_until_complete(login(user, pwd))
            Data = data["content"].split("/")
            contact = Data[0].split(":")[1]
            TheirDID = Data[1].split(":")[1]
            TheirVerkey = Data[2].split(":")[1]
            loop.run_until_complete(store_did(user, wallet_handle, contact, TheirDID, TheirVerkey))
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(close_w(wallet_handle))
            return "OK"

        else:
            print(7)
            with open(user+"/"+connection_id+".dat", "a") as output:
                json.dump(data, output)
            with open(user+"/"+connection_id+".dat", "a") as output:
                output.write("\n")
        return "OK"

    app_flask.run(host='localhost', port=third_port)


thread = threading.Thread(target=flask_app)
thread.start()


second_port = first_port + 3000
third_port = second_port + 3000
seed = user.ljust(32, '0')
cmd = """aca-py start \
--label """+user+""" \
-it http 0.0.0.0 """+str(first_port)+""" \
-ot http \
--admin 0.0.0.0 """+str(second_port)+""" \
--admin-insecure-mode \
--genesis-url http://localhost:9000/genesis \
--seed """+seed+""" \
--endpoint http://localhost:"""+str(first_port)+"""/ \
--debug-connections \
--public-invites \
--auto-provision \
--webhook-url http://localhost:"""+str(third_port)+"""/webhooks \
--wallet-type indy \
--wallet-name """+user+"""-wallet \
--wallet-key """+pwd
cmd_list = []
for m in cmd.split(" "):
    cmd_list.append(m)
while '' in cmd_list:
    cmd_list.remove('')
proc = subprocess.Popen(cmd_list)  




while True:
    pass