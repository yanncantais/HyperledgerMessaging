from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import os
import asyncio
#indy
from indy import crypto, did, wallet
import json
from kivy.clock import Clock


async def close_wallet(wallet_handle):
    await wallet.close_wallet(wallet_handle)


class Connected(Screen):    
    def contact(self, contact):
        app = App.get_running_app()
        app.contact = contact        
        self.manager.get_screen('chat_page').load()
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'chat_page'
        print(contact)
        print(app.login)
    def disconnect(self):
        app = App.get_running_app()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(close_wallet(app.login))
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        self.manager.get_screen('login').resetForm()
        self.manager.get_screen('sign_in').resetForm()


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
        self.ids.contact_label.text = str(app.contact)
        
        
        
    def send(self, message):
        print("message", message, " will be sent")

    def do_account(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'connected'


class Home(Screen):
    def login(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'login'
    def sign_in(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'sign_in'
      

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
        
        
class SignIn(Screen):
    
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
        manager.add_widget(SignIn(name='sign_in'))
        manager.add_widget(Connected(name='connected'))       
        manager.add_widget(ChatPage(name='chat_page'))       
        return manager


if __name__ == '__main__':
    LoginApp().run()