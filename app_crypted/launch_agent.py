import subprocess
import sys
import threading
from flask import Flask, request
import os
import requests
import asyncio
import json
from indy import did, crypto, wallet


user = sys.argv[1]
pwd = sys.argv[2]



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


def flask_app():
    app_flask = Flask(__name__)        
    @app_flask.route('/webhooks/topic/basicmessages/', methods=['POST'])
    def webhook():
        data = request.get_json()
        connection_id = data["connection_id"]
        print(data["content"])
        if data["content"] == ask_verkey_label:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, wallet_handle = loop.run_until_complete(login(user, pwd))
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            DID,Verkey = loop.run_until_complete(create_did(wallet_handle))
            print("message", DID, Verkey, "will be sent")
            Keys = 'name:'+user+'/did:'+DID+'/verkey:'+Verkey
            url = "http://0.0.0.0:"+str(second_port)+"/connections/"+connection_id+"/send-message"
            response = requests.post(url, json = {"content": Keys})
            message_content = {'connection_id': connection_id, 'content': Keys, 'state': 'sent'}
            print(response.text)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(close_w(wallet_handle))
        elif "did:" in data["content"] and "verkey:" in data["content"] and "name:" in data["content"]:
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
        else:
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