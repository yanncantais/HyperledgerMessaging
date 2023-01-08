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

async def close_wallet(wallet_handle):
    await wallet.close_wallet(wallet_handle)


class Connected(Screen):  
    def on_enter(self):
        app = App.get_running_app()
        self.ids.welcome_label.text = "Welcome "+str(app.username)
    def contact(self, contact):
        app = App.get_running_app()
        app.contact = contact        
        self.manager.get_screen('chat_page').load()
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'chat_page'
        print(contact)
        print(app.login)
    def invite(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'invite'
    def disconnect(self):
        app = App.get_running_app()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(close_wallet(app.login))
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        self.manager.get_screen('login').resetForm()
        self.manager.get_screen('sign_up').resetForm()


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

        
class Invite(Screen):
    def on_enter(self):  
        for widget in self.ids.qr_layout.walk():
            if isinstance(widget, Image):
                self.ids.qr_layout.remove_widget(widget)
                
        app = App.get_running_app()            
        print('creating invitation link')   
        json_did = {"@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/out-of-band/1.0/invitation",
                   "@id": "c927b4a7-1901-433e-ac3f-16158431fd0a",
                   "handshake_protocols": [
                   "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"
                    ],
                    "label": app.username,
                    "service": [
                    "did:sov:UpFt248WuA5djSFThNjBhq"
                    ]
                    }
        # r = requests.post("http://localhost:11000/out-of-band/create-invitation", json = json_did)
        # print(r.status_code, r.reason)
        # print(r.text[:300] + '...')
        # Encoding data using make() function
        img = qrcode.make(json_did)
        # Saving as an image file
        img.save('MyQRCode1.png')
        wimg = Image(source='MyQRCode1.png')
        self.ids.qr_layout.remove_widget(self.ids.loading_label)
        self.ids.qr_layout.add_widget(wimg)
                     
    def profile(self):
        
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'connected'


class Login(Screen):
    
    def do_login(self, loginText, passwordText):
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
            self.manager.current = 'connected'
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
    
    def build(self):    
        manager = ScreenManager()
        manager.add_widget(Home(name="home"))
        manager.add_widget(Login(name='login'))
        manager.add_widget(SignUp(name='sign_up'))
        manager.add_widget(Connected(name='connected'))       
        manager.add_widget(ChatPage(name='chat_page'))     
        manager.add_widget(Invite(name='invite'))     
        return manager


if __name__ == '__main__':
    LoginApp().run()