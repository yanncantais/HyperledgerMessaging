import cv2
import requests
import json
import qrcode

def create_qr(port, user):
    r = requests.post("http://localhost:11000/out-of-band/create-invitation", json={"@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/out-of-band/1.0/invitation",
                       "handshake_protocols": [
                       "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"
                        ],
                        "label": user,                  
                        })
    json_response = json.loads(r.text)
    json_invite = json_response["invitation"]     
    
    
    img = qrcode.make(json_invite)
    
    img.save('QRCode'+user+'.png')


def read_qr(user):
    img=cv2.imread("QRCode"+user+".png")
    det=cv2.QRCodeDetector()
    val, pts, st_code=det.detectAndDecode(img)
    print(val)
    return val.replace("'",'"')


invitation = read_qr("yann")




# p = json.loads(read_qr("tanguy"))





second_port = 11000
Invitations = []
r = requests.get("http://0.0.0.0:"+str(second_port)+"/connections").text
r_json = json.loads(r)
r_json = r_json["results"]
for item in r_json:
    print(item)



second_port = 11000
Invitations = []
r = requests.get("http://0.0.0.0:"+str(second_port)+"/ce6ebe5e-f668-48b2-ad49-ac73f701de3f/endpoints").text
print(r)




# second_port = 11001

# invitation = invitation.replace("'",'"')
# invitation = json.loads(invitation)
# r = requests.post("http://0.0.0.0:"+str(second_port)+"/out-of-band/receive-invitation", json = invitation)
# print(r.text)  
# response = json.loads(r.text)
# connection_id = response["connection_id"]
# print(connection_id)
# r = requests.post("http://0.0.0.0:"+str(second_port)+"/didexchange/"+connection_id+"/accept-invitation")
# print(r.text)


# # print(p)

