import asyncio
import time
import re
import requests
import aries_cloudagent
import subprocess
#kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
#QRCODE
#from kivy_garden.qrcode import QRCodeWidget
#indy
from indy import crypto, did, wallet

from multiprocessing import Process
import threading

from aries_cloudagent.commands import start


class MyApp(App):
    def build(self):
        # Create a layout
        layout = BoxLayout(orientation="vertical")
        
        #qr_code_label = Label(text="")
        #layout.add_widget(qr_code_label)
        
        #scan_button = Button(text="Scan QR code", on_press=self.start_scanning)
        #layout.add_widget(scan_button)
        
        # Create a button widget
        button = Button(text="Create Wallet and DID")
        buttoninvitation = Button(text = "create invitation")
        #self.camera = Camera(resolution=(640, 480))
        #layout.add_widget(self.camera)
        
        #self.qr_code_widget=QRCodeWidget()
        #layout.add_widget(self.qr_code_widget)
        
        # Bind the on_release event of the button to a callback function
        button.bind(on_release=self.run_init)

        #create tabbed panel
        tp=TabbedPanel()
        tp.default_tab_text = "QR Scanner"
        
        #now add content in default tab
        tp.default_tab_content = layout
        
        th= TabbedPanelHeader(text = "DID")
        th.content = button

        invitation = TabbedPanelHeader(text = "Invit")
        invitation.content = buttoninvitation
        buttoninvitation.bind(on_release=self.run_invitation)
        tp.add_widget(th)
        tp.add_widget(invitation)
        return tp
        
    #def start_scanning(self, instance):
      #self.qr_code_widget.start()
    #def on_qr_code(self, instance):
      #qr_code_label.text = qr_code
        
    def run_invitation(self, instance):
        print('creating invitation link')
        

        r = requests.post("http://localhost:11000/out-of-band/create-invitation", json={"@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/out-of-band/1.0/invitation",
                   "@id": "c927b4a7-1901-433e-ac3f-16158431fd0a",
                   "handshake_protocols": [
                   "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"
                    ],
                    "label": "Alice",
                    "service": [
                    "did:sov:UpFt248WuA5djSFThNjBhq"
                    ]
                    })
        print(r.status_code, r.reason)
        print(r.text[:300] + '...')
        import qrcode
        # Data to be encoded
        json = {"@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/out-of-band/1.0/invitation",
                   "@id": "c927b4a7-1901-433e-ac3f-16158431fd0a",
                   "handshake_protocols": [
                   "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"
                    ],
                    "label": "Alice",
                    "service": [
                    "did:sov:UpFt248WuA5djSFThNjBhq"
                    ]
                    }
 
        # Encoding data using make() function
        img = qrcode.make(json)
        # Saving as an image file
        img.save('MyQRCode1.png')
        return img
        
        
    def run_init(self, instance):
      try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(demo())
        time.sleep(1)  # waiting for libindy thread complete
      except KeyboardInterrupt:
        print('')

#Creates wallet and did,verkey
async def init():
    wallet_config = '{"id": "%s-wallet"}'
    wallet_credentials = '{"key": "%s-wallet-key"}'
    try:
        await wallet.create_wallet(wallet_config, wallet_credentials)
        print("wallet created")
    except:
        pass
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)       
    print('wallet = %s' % wallet_handle)    
    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, "{}")
    print('my_did and verkey = %s %s' % (my_did, my_vk))
    #else:
        #did_vk = input("Your DID and verkey? ").strip().split(' ')
        #my_did = did_vk[0]
        #my_vk = did_vk[1]
        # 
        #    
    #post the new did on the von network
    r = requests.post("http://localhost:9000/register", json={'role': 'ENDORSER', 'alias': 'papa', 'did':0, 'seed': 'papa'})
    print(r.status_code, r.reason)
    print(r.text[:300] + '...')

    #start acapy agent
    
    
    

    # Start the agent
    

    #create an invitation

    #transform it into qr

    #send messages
    return wallet_handle, my_did, my_vk
    


    
async def run_read(wallet_handle, my_vk, interval=1):
    while True:
        await read(wallet_handle, my_vk)
        time.sleep(interval)
        
        
    thread = threading.Thread(target=run2, args=(wallet_handle, my_vk, interval))
    thread.daemon = True
    thread.start()
async def run_demo(wallet_handle, my_did, my_vk, their_did, their_vk):
    while True:
        argv = input('> ').strip().split(' ')
        cmd = argv[0].lower()
        rest = ' '.join(argv[1:])
        if re.match(cmd, 'write'):
            await write(wallet_handle, my_vk, their_vk, rest)
        elif re.match(cmd, 'read'):
            await read(wallet_handle, my_vk)
        elif re.match(cmd, 'quit'):
            break
        else:
            print('Huh?')

async def read(wallet_handle, my_vk):
    with open('message.dat', 'rb') as f:
        encrypted = f.read()
    decrypted = await crypto.auth_decrypt(wallet_handle, my_vk, encrypted)
    # decrypted = await crypto.anon_decrypt(wallet_handle, my_vk, encrypted)
    print(decrypted)
    
    


async def init():
    wallet_config = '{"id": "%s-wallet"}'
    wallet_credentials = '{"key": "%s-wallet-key"}'
    try:
        await wallet.create_wallet(wallet_config, wallet_credentials)
        print("wallet created")
    except:
        pass
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)       
    print('wallet = %s' % wallet_handle)    
    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, "{}")
    print('my_did and verkey = %s %s' % (my_did, my_vk))
    #else:
        #did_vk = input("Your DID and verkey? ").strip().split(' ')
        #my_did = did_vk[0]
        #my_vk = did_vk[1]
        # 
        #    
    #post the new did on the von network
    r = requests.post("http://localhost:9000/register", json={'role': 'ENDORSER', 'alias': 'papa', 'did':0, 'seed': 'papa'})
    print(r.status_code, r.reason)
    print(r.text[:300] + '...')

#launch init()
async def demo():
    wallet_handle, my_did, my_vk = await init()
    # task1 = asyncio.create_task(read_infinite(wallet_handle, my_vk))
    # task2 = asyncio.create_task(demo_infinite(wallet_handle, my_did, my_vk, their_did, their_vk))
    # await task1
    # await task2

if __name__ == '__main__':
    MyApp().run()
