from kivy.app import App
from kivy.lang import Builder
from kivy_garden.zbarcam import ZBarCam
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition




class Scanner(Screen):
    def login(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current='scanner'

class QrCodeApp(App):
    def build(self):
        manager = ScreenManager
        manager.add_widget(Scanner(name='scanner'))
        return manager


if __name__ == '__main__':
    QrCodeApp().run()