from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
import os
import asyncio
#indy
from indy import crypto, did, wallet
import json
from kivy.clock import Clock
import requests
import qrcode
import os
import subprocess
import signal
import cv2
import time

async def close_wallet(wallet_handle):
    await wallet.close_wallet(wallet_handle)


def allocated_port(first_port):
    port = first_port
    FoundPort = False
    while FoundPort == False:
        try:
            requests.get("http://localhost:"+str(port))
            port+=1
        except:
            FoundPort = True
    return port


proc = None

class Connected(Screen):    
        
    # def create_agent(self):
    #     global proc
    #     app = App.get_running_app()
    #     user = app.username
    #     pwd = app.password
    #     first_port = allocated_port(app.first_port)
    #     app.first_port = first_port
    #     second_port = allocated_port(app.second_port)
    #     app.second_port = second_port
    #     seed = user.ljust(32, '0')
    #     cmd = """aca-py start \
    #     --label """+user+""" \
    #     -it http 0.0.0.0 """+str(first_port)+""" \
    #     -ot http \
    #     --admin 0.0.0.0 """+str(second_port)+""" \
    #     --admin-insecure-mode \
    #     --genesis-url http://localhost:9000/genesis \
    #     --seed """+seed+""" \
    #     --endpoint http://localhost:"""+str(first_port)+"""/ \
    #     --debug-connections \
    #     --public-invites \
    #     --auto-provision \
    #     --webhook-url http://localhost:10000/webhooks
    #     --wallet-type indy \
    #     --wallet-name """+user+"""-wallet \
    #     --wallet-key """+pwd
        
        # cmd_list = []
        # for m in cmd.split(" "):
        #     cmd_list.append(m)
        # while '' in cmd_list:
        #     cmd_list.remove('')
        # proc = subprocess.Popen(cmd_list)  
        
        
    def on_enter(self):
        app = App.get_running_app()
        if not app.Registered:
            self.ids.welcome_label.text = "Welcome "+str(app.username)
            json_register = {'role': 'ENDORSER', 'alias': app.username, 'did':0, 'seed': app.username}
            r = requests.post("http://localhost:9000/register", json=json_register)
            print(r.status_code, r.reason)
            print(r.text[:300] + '...')
            app.Registered = True
        # if not app.AgentCreated:
        #     self.create_agent()
        #     app.AgentCreated = True
        
    def see_invitations(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'invitations'
        
    def send_messages(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'send_messages'
    
    def contact(self, contact):
        app = App.get_running_app()
        app.contact = contact
        img=cv2.imread("QRCode"+contact+".png")
        det=cv2.QRCodeDetector()
        invitation, pts, st_code=det.detectAndDecode(img)
        invitation = invitation.replace("'",'"')
        invitation = json.loads(invitation)
        r = requests.post("http://0.0.0.0:"+str(app.second_port)+"/out-of-band/receive-invitation", json = invitation)
        print(r.text)  
        response = json.loads(r.text)
        connection_id = response["connection_id"]
        print(connection_id)
        r = requests.post("http://0.0.0.0:"+str(app.second_port)+"/didexchange/"+connection_id+"/accept-invitation")
        print(r.text)
        self.manager.get_screen('chat_page').load()
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'chat_page'
        print(contact)
        print(app.login)
    def invite(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'invite'
    def disconnect(self):
        global proc
        app = App.get_running_app()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(close_wallet(app.login))
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        self.manager.get_screen('login').resetForm()
        self.manager.get_screen('sign_up').resetForm()
        # print(proc)
        # if proc is not None:
        #     os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            # proc.terminate()


async def login(me, key):
    wallet_config = '{"id": "%s-wallet"}' % me
    wallet_credentials = '{"key": "%s"}' % key
    wallet_handle = None
    
    try:        
        wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
        success = True
    except:
        success = False
    return success, wallet_handle


async def sign(me, key):
    wallet_config = '{"id": "%s-wallet"}' % me
    wallet_credentials = '{"key": "%s"}' % key
    wallet_handle = None
    try:        
        await wallet.create_wallet(wallet_config, wallet_credentials)
        wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
        success = True
    except:
        success = False
    if not success:
        success, wallet_handle = await login(me, key)
    return success, wallet_handle



class ChatPage(Screen):
    def load(self, **kwargs):
        app = App.get_running_app()
        self.ids.contact_label.text = "Message with "+str(app.contact)       
        
        
    def send(self, message):
        print("message", message, " will be sent")

    def do_account(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'connected'


class Home(Screen):
    def login(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'login'
    def sign_up(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'sign_up'

    

class Invitations(Screen):
    def on_enter(self):
        counter = 1
        for widget in self.ids.invitation_layout.walk():
            if counter > 3:
                self.ids.invitation_layout.remove_widget(widget)
            counter+=1
        app = App.get_running_app()
        Invitations = []
        r = requests.get("http://0.0.0.0:"+str(app.second_port)+"/connections").text
        r_json = json.loads(r)
        r_json = r_json["results"]
        for item in r_json:
            if item["rfc23_state"] == "request-received":
                Invitations.append(("Click to accept "+item["their_label"], "http://0.0.0.0:"+str(app.second_port)+"/didexchange/"+item["connection_id"]+"/accept-request"))
        print(Invitations)        
        for item in Invitations:
            text, url = item
            button = Button(text=text, on_press=lambda btn: self.button_pressed(item), size_hint=(1, 0.3))
            self.ids.invitation_layout.add_widget(button)

    def button_pressed(self, item):
        # This function will be called when the button is pressed
        text, url = item
        response = requests.post(url)
        print(response.text)
        
        
    def profile(self):
        
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'connected'
        
        
class SendMessages(Screen):
    def on_enter(self):
        counter = 1
        for widget in self.ids.send_messages_layout.walk():
            if counter > 3:
                self.ids.send_messages_layout.remove_widget(widget)
            counter+=1
        app = App.get_running_app()
        
        Contacts = []
        r = requests.get("http://0.0.0.0:"+str(app.second_port)+"/connections").text
        r_json = json.loads(r)
        r_json = r_json["results"]
        for item in r_json:
            if item["rfc23_state"] == "completed":
                Contacts.append(("Talk to "+item["their_label"], "http://0.0.0.0:"+str(app.second_port)+"/connections/"+item["connection_id"]+"/send-message"))
        print(Contacts)
    
        for item in Contacts:
            text, url = item
            button = Button(text=text, on_press=lambda btn: self.button_pressed(item), size_hint=(1, 0.3))
            self.ids.send_messages_layout.add_widget(button)

    def button_pressed(self, item):
        # This function will be called when the button is pressed
        text, url = item
        response = requests.post(url, json = {"content": "test"})
        print(response.text)
        
        
    def profile(self):
        
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'connected'

class Invite(Screen):
    def on_enter(self):  
        for widget in self.ids.qr_layout.walk():
            if isinstance(widget, Image):
                self.ids.qr_layout.remove_widget(widget)                
        app = App.get_running_app()            
        GoodQR = False
        while not GoodQR:        
            print('creating invitation link')   
            r = requests.post("http://localhost:"+str(app.second_port)+"/out-of-band/create-invitation", json={"@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/out-of-band/1.0/invitation",
                               "handshake_protocols": [
                               "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"
                                ],
                                "label": app.username,                  
                                })
            json_response = json.loads(r.text)
            json_invite = json_response["invitation"] 
            img = qrcode.make(json_invite)
            # Saving as an image file
            img.save('QRCode'+app.username+'.png')
            wimg = Image(source='QRCode'+app.username+'.png')            
            time.sleep(2)            
            img=cv2.imread("QRCode"+app.username+".png")
            det=cv2.QRCodeDetector()
            invitation, pts, st_code=det.detectAndDecode(img)
            if len(invitation) > 10:
                GoodQR = True
            print(invitation)
        self.ids.qr_layout.remove_widget(self.ids.loading_label)
        self.ids.qr_layout.add_widget(wimg)
        
        
                     
    def profile(self):
        
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'connected'


# class CreateAgent(Screen):
    


class Login(Screen):
    
    def do_login(self, loginText, passwordText, portText):
        app = App.get_running_app()
        app.first_port = portText
        app.second_port = int(portText) + 3000
        if loginText == "" or passwordText == "":
            self.ids.success_label.text = "Please, enter your login and password."
            return ""
            
        app = App.get_running_app()

        app.username = loginText
        app.password = passwordText

        loop = asyncio.get_event_loop()
        success, wallet_handle = loop.run_until_complete(login(loginText, passwordText))
        if not success:
            self.ids.success_label.text = "Wrong username/password combination. Try again."
        else:
            app.login = wallet_handle
            self.manager.transition = SlideTransition(direction="left")
            self.manager.current = 'connected'
        
    def do_home(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'home'
    
    
    def resetForm(self):
        self.ids['login'].text = ""
        self.ids['password'].text = ""
        self.ids.success_label.text = ""
        
    def fillForm(self, login, password):
        self.ids['login'].text = login
        self.ids['password'].text = password
        self.ids.success_label.text = ""
        
        
class SignUp(Screen):
    
    def do_sign(self, loginText, passwordText):
        app = App.get_running_app()

        app.username = loginText
        app.password = passwordText

        loop = asyncio.get_event_loop()
        success, wallet_handle = loop.run_until_complete(sign(loginText, passwordText))
        if not success:
            self.ids.success_label.text = "User "+loginText+" already exists. Try again."
        else:
            app.login = wallet_handle
            self.manager.transition = SlideTransition(direction="left")
            self.manager.current = 'login'
            self.manager.get_screen('login').fillForm(loginText, passwordText)

            
        
            
    def do_home(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'home'
    
    def resetForm(self):
        self.ids['login'].text = ""
        self.ids['password'].text = ""


class LoginApp(App):
    username = StringProperty(None)
    password = StringProperty(None)
    contact = StringProperty(None)
    Registered = False
    AgentCreated = False
    first_port = 20000
    second_port = 23000
    connection_id = StringProperty(None)
    
    def build(self):    
        manager = ScreenManager()
        manager.add_widget(Home(name="home"))
        manager.add_widget(Login(name='login'))
        manager.add_widget(SignUp(name='sign_up'))
        manager.add_widget(Connected(name='connected'))       
        manager.add_widget(ChatPage(name='chat_page'))     
        manager.add_widget(Invite(name='invite'))  
        manager.add_widget(Invitations(name='invitations'))  
        manager.add_widget(SendMessages(name='send_messages'))  
        return manager


# def handler(signum, frame):  
    
#     exit(1)
 
# signal.signal(signal.SIGINT, handler)

if __name__ == '__main__':
    LoginApp().run()
    
