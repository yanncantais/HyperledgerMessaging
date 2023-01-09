import requests
import json

second_port = 11002

Contacts = []
r = requests.get("http://0.0.0.0:"+str(second_port)+"/connections").text
r_json = json.loads(r)
r_json = r_json["results"]
for item in r_json:
    if item["rfc23_state"] == "completed":
        Contacts.append(("Talk to "+item["their_label"], "http://0.0.0.0:"+str(second_port)+"/connections/"+item["connection_id"]+"/send-message"))
    
    
    