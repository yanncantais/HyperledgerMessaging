import subprocess
import sys
import threading
from flask import Flask, request
import os

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


def flask_app():
    app_flask = Flask(__name__)        
    @app_flask.route('/webhooks/topic/basicmessages/', methods=['POST'])
    def webhook():
        data = request.get_json()
        connection_id = data["connection_id"]
        with open(user+"/"+connection_id+".dat", "a") as output:
            output.write(str(data)+"\n")
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