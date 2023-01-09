import subprocess
import sys




user = sys.argv[1]
pwd = sys.argv[2]
first_port = int(sys.argv[3])

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