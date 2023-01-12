import json



connection_id = "b823f8d1-8c18-47b8-98bf-3ff99fd9bb7f"
username = "yann"
contact = "tanguy"
f = open(username+"/"+connection_id+".dat", "r")
Messages = f.readlines()
for message in Messages:
    message = message.replace("'",'"')
    message = json.loads(message)
    message_to_print = ""
    content = message["content"]
    state = message["state"]
    if state == "sent":
        message_to_print = username+" : "+content
    else:
        message_to_print = contact+" : "+content
    print(message_to_print)