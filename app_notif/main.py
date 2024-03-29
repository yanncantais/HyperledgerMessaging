from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
import asyncio
#indy
from indy import crypto, did, wallet
import json
import requests
import qrcode
import cv2
import time
from flask import Flask, request
import threading
import os



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


async def close_wallet(wallet_handle):
    await wallet.close_wallet(wallet_handle)


class Connected(Screen):         
    def on_enter(self):
        app = App.get_running_app()
        if not app.Registered:
            self.ids.welcome_label.text = "Welcome "+str(app.username)
            json_register = {'role': 'ENDORSER', 'alias': app.username, 'did':0, 'seed': app.username}
            r = requests.post("http://localhost:9000/register", json=json_register)
            print(r.status_code, r.reason)
            print(r.text[:300] + '...')
            app.Registered = True
        if not app.Reloading:
            thread = threading.Thread(target=self.reload_messages)
            thread.start()

    def see_invitations(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'invitations'
        
    def send_messages(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'send_messages'
    
    def contact(self, contact):
        app = App.get_running_app()
        app.contact = contact
        try:
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
            self.ids.qr_connect_label.text = "Invitation sent to "+contact
        except:
            self.ids.qr_connect_label.text = " An error occured during the sending of the invitation.\nCheck that your agent is online and the QR code is valid."
         
        
    def invite(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'invite'
        
    def disconnect(self):
        app = App.get_running_app()
        app.Registered = False
        app.Logged = False
        loop = asyncio.get_event_loop()
        loop.run_until_complete(close_wallet(app.login))
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        self.manager.get_screen('login').resetForm()
        self.manager.get_screen('sign_up').resetForm()
        
        
        
    def read_messages(self):
        app = App.get_running_app()
        connections = os.listdir(app.username)
        for connection in connections:
            if connection[-4:] != ".dat":
                connections.remove(connection)
        for path in connections:
            connection_id = path.split(".")[0]
            f = open(app.username+"/"+path, "r")
            Messages = f.readlines()  
            f.close()
            for message in Messages:
                message = message.replace("'",'"')
                message = json.loads(message)
                message_id = message["message_id"]
                if "message_id" in message:
                    if os.path.isfile(app.username+"/"+path.replace(".dat",".rd")):                        
                        m = open(app.username+"/"+path.replace(".dat",".rd"), "r")
                        MessagesRead = m.read().split("\n")
                        m.close()
                        if message_id not in MessagesRead:                        
                            if connection_id not in app.NewMessages:
                                app.NewMessages[connection_id] = [message_id]
                            else:
                                if message_id not in app.NewMessages[connection_id]:
                                    app.NewMessages[connection_id].append(message_id)
                    else:
                        app.NewMessages[connection_id] = [message_id]

        
        
    def reload_messages(self):
        app = App.get_running_app()
        while app.Logged:
            app.Reloading = True
            print("reloading loop running...")
            time.sleep(2) 
            r = requests.get("http://0.0.0.0:"+str(app.second_port)+"/connections").text
            r_json = json.loads(r)
            r_json = r_json["results"]
            counter_invitation = 0
            for item in r_json:
                if item["rfc23_state"] == "completed":
                    app.Contacts[item["connection_id"]] = item["their_label"]
                if item["rfc23_state"] == "request-received":
                    counter_invitation += 1
            if counter_invitation > 0:
                self.ids.invitation_button.text = "Invitations ("+str(counter_invitation)+")"
            else:
                self.ids.invitation_button.text = "Invitations"


                    
                    
            self.read_messages()
            print(app.Contacts)
            new_messages = 0
            for connection in app.NewMessages:
                if len(app.NewMessages[connection]) > 0:
                    print(len(app.NewMessages[connection]), "nouveaux messages de", app.Contacts[connection])
                    screen_messages = self.manager.get_screen('send_messages')
                    for button in screen_messages.ids.send_messages_layout.children:
                        if isinstance(button, Button):
                            if button.name != "profile":
                                if button.connection_id == connection:                                
                                    button.text = app.Contacts[connection] + " ("+str(len(app.NewMessages[connection]))+")"
                    new_messages+=len(app.NewMessages[connection])
            if new_messages != 0:
                self.ids.messages_button.text = "Messages ("+str(new_messages)+")"
            else:
                self.ids.messages_button.text = "Messages"
        app.Reloading = False
                
        
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
                Contacts.append((item["their_label"], item["connection_id"]))
        print(Contacts)    
        for item in Contacts:
            contact, connection_id = item
            if connection_id in app.NewMessages:
                counter = len(app.NewMessages[connection_id])
                if counter > 0:
                    text = contact+" ("+str(counter)+")"
                else:
                    text = contact
            else:
                text = contact
            button = Button(text=text, on_press=lambda btn, item=item: self.button_pressed(*item), size_hint=(1, 0.3), name="contact")
            button.font_size = 20
            button.connection_id = connection_id
            self.ids.send_messages_layout.add_widget(button)

    def button_pressed(self, contact, connection_id):
        app = App.get_running_app()
        app.contact = contact
        app.contact_connection_id = connection_id
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'chat_page'
    
    def profile(self):
        
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'connected'        



class ChatPage(Screen):
    def reload_messages(self):
        app = App.get_running_app()
        connection_id = app.contact_connection_id
        path = app.username+"/"+connection_id+".dat"
        if not os.path.isfile(path):
            f = open(path, "w+")
        f = open(path, "r")
        Messages = f.readlines()
        while self.manager.current == 'chat_page':     
            time.sleep(1)
            f = open(app.username+"/"+connection_id+".dat", "r")
            Messages = f.readlines()
            f.close()
            if os.path.isfile(app.username+"/"+connection_id+".rd"):
                m = open(app.username+"/"+connection_id+".rd", "r")
                MessagesRead = m.read().split("\n") 
                m.close()
            else:
                MessagesRead = []
            messages_to_print = ""
            for message in Messages:
                message = message.replace("'",'"')
                message = json.loads(message)
                new_message = ""
                content = message["content"]
                if "message_id" in message:
                    message_id = str(message["message_id"])
                    if message_id not in MessagesRead:
                        with open(app.username+"/"+connection_id+".rd", "a") as output:
                            output.write(str(message["message_id"])+"\n")
                    if connection_id in app.NewMessages:
                        if message_id in app.NewMessages[connection_id]:
                            app.NewMessages[connection_id].remove(message_id)
                content = content.replace("u2019","'").replace("u0022",'"')
                state = message["state"]
                if state == "sent":
                    new_message = app.username+" : "+content+"\n"
                else:
                    new_message = app.contact+" : "+content+"\n"
                messages_to_print += new_message     
            if messages_to_print != self.ids.messages_label.text:
                print(messages_to_print)
                self.ids.messages_label.text = messages_to_print

            
    
    def on_enter(self, **kwargs):
        app = App.get_running_app()
        self.ids.contact_label.text = str(app.contact)
        thread = threading.Thread(target=self.reload_messages)
        thread.start()
        
    def send(self, message):
        app = App.get_running_app()
        connection_id = app.contact_connection_id
        print("message", message, "will be sent")
        self.ids.messages_label.text += app.username+" : "+message+"\n"
        url = "http://0.0.0.0:"+str(app.second_port)+"/connections/"+connection_id+"/send-message"
        print(url)
        message = message.replace("'","u2019").replace("'","u0022")
        response = requests.post(url, json = {"content": message})
        message_content = {'connection_id': connection_id, 'content': message, 'state': 'sent'}
        print(response.text)
        with open(app.username+"/"+connection_id+".dat", "a") as output:
            output.write(str(message_content)+"\n")
        self.ids['message'].text = ""
    
    def do_account(self):
        self.ids.messages_label.text = ""
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'send_messages'


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
        text, url = item
        response = requests.post(url)
        print(response.text)
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'connected'
        
        
    def profile(self):
        
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'connected'
        
        
async def get_did(wallet_handle):
    firstdid, firstverkey = await did.create_and_store_my_did(wallet_handle = wallet_handle, did_json = "{}")
    return firstdid, firstverkey

class Invite(Screen):   
    
    
    def on_enter(self):  
        for widget in self.ids.qr_layout.walk():
            if isinstance(widget, Image):
                self.ids.qr_layout.remove_widget(widget)                
        app = App.get_running_app()        
        loop = asyncio.get_event_loop()
        MyDID, MyVerkey = loop.run_until_complete(get_did(app.login))
        print("My DID: ",MyDID)
        print("My verkey: ",MyVerkey)
        GoodQR = False
        while not GoodQR:        
            print('creating invitation link')   
            r = requests.post("http://localhost:"+str(app.second_port)+"/out-of-band/create-invitation", json={"@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/out-of-band/1.0/invitation",
                               "handshake_protocols": [
                               "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"
                                ]                 
                                })
            json_response = json.loads(r.text)
            json_invite = json_response["invitation"] 
            json_invite["recipientKeys"] = [MyVerkey]
            json_invite["label"] = app.username+":"+MyDID
            print(type(json_invite))
            print(json_invite)
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


 
class Login(Screen):
    def do_login(self, loginText, passwordText):
        PortFound = False
        app = App.get_running_app()        
        if not os.path.isfile("ports.conf"):
            self.ids.success_label.text = "No ports.conf file found."
            return ""
        p = open("ports.conf", "r")
        AgentsPorts = p.read().split("\n") 
        p.close()
        for port_line in AgentsPorts:
            if ":" in port_line:
                port_line_separated = port_line.split(":")
                agent = port_line_separated[0]
                port = int(port_line_separated[1])
                if agent == loginText:
                    app.first_port = port
                    PortFound = True
                    break
        if not PortFound:
            self.ids.success_label.text = "Your agent was not found."
            return ""
        
        app.second_port = int(app.first_port) + 3000
        app.third_port = int(app.second_port) + 3000
        
        try:
            requests.get("http://localhost:"+str(app.second_port))
        except:
            self.ids.success_label.text = "Your agent is not running. Please, start it."
            return ""

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
            app.Logged = True
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
    def do_sign(self, loginText, passwordText, passwordText2):
        app = App.get_running_app()

        if passwordText != passwordText2:
            self.ids.success_label.text = "The 2 passwords do not match. Try again."
            return ""
        app.username = loginText
        app.password = passwordText

        loop = asyncio.get_event_loop()
        success, wallet_handle = loop.run_until_complete(sign(loginText, passwordText))
        if not success:
            self.ids.success_label.text = "User "+loginText+" already exists. Try again."
        else:
            app.login = wallet_handle
            json_register = {'role': 'ENDORSER', 'alias': app.username, 'did':0, 'seed': app.username}
            requests.post("http://localhost:9000/register", json=json_register)
            
            Ports = []
            if os.path.isfile("ports.conf"):
                p = open("ports.conf", "r")
                AgentsPorts = p.read().split("\n") 
                p.close()
                for agent in AgentsPorts:
                    if ":" in agent:
                        port_line = agent.split(":")
                        Ports.append(int(port_line[1]))
            allocated_port = 8000
            
            while allocated_port in Ports:
                allocated_port+=1
                
                
            with open("ports.conf", "a") as output:
                output.write(app.username+":"+str(allocated_port)+"\n")          
                
                
            
            loop = asyncio.get_event_loop()
            loop.run_until_complete(close_wallet(app.login))
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
    Logged = False
    Reloading = False
    NotifMessages = {"total" : 0}
    Contacts = {}
    NewMessages = {}
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



if __name__ == '__main__':
    LoginApp().run()
    
