import json
import sys
from tkinter import *
from tkinter import ttk

from utils.not_windows import NotWindows
from windows.window import Window
from windows.main.menu_bar import MenuBar
from utils.user_settings import UserSettings
from utils.get_file import resource_path
from utils.warning_pop_up_save import confirm_save
from utils.record_file_management import RecordFileManagement
from utils.version import Version
from windows.others.new_ver_avalaible import NewVerAvailable
from hotkeys.hotkeys_manager import HotkeysManager
from macro import Macro
from os import path
from sys import platform, argv
from pystray import Icon
from pystray import MenuItem
from PIL import Image
from threading import Thread
from json import load
from time import time

if platform.lower() == "win32":
    from tkinter.ttk import *


class MainApp(Window):
    """Main windows of the application"""

    def __init__(self):
        super().__init__("PyMacroRecord", 300, 200)
        self.attributes("-topmost", 1)
        if platform == "win32":
            self.iconbitmap(resource_path(path.join("assets", "logo.ico")))

        self.settings = UserSettings(self)

        self.lang = self.settings.get_config()["Language"]
        with open(resource_path(path.join('langs',  self.lang+'.json')), encoding='utf-8') as f:
            self.text_content = json.load(f)

        self.text_content = self.text_content["content"]

        # For save message purpose
        self.macro_saved = False
        self.macro_recorded = False
        self.prevent_record = False

        self.version = Version(self.settings.get_config(), self)

        self.menu = MenuBar(self)  # Menu Bar
        self.macro = Macro(self)

        self.validate_cmd = self.register(self.validate_input)

        self.hotkeyManager = HotkeysManager(self)

        # Main Buttons (Start record, stop record, start playback, stop playback)
        top_frame = Frame(self)
        top_frame.pack(fill=BOTH, expand=True, padx=16)
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=3)

        Label(top_frame, text = 'Speed:').grid(column=0, row=0, padx=8)
        self.speed_value = DoubleVar()
        self.speed_value.set(self.settings.get_config()["Playback"]["Speed"])
        Scale(
            top_frame,
            from_=1.0,
            to=1000,
            orient='horizontal',
            length=150,
            showvalue=1,
            resolution=0.01,
            command=self.speed_changed,
            variable=self.speed_value
        ).grid(column=1, row=0, padx=8)

        Label(top_frame, text = 'Repeat:').grid(column=0, row=1, padx=8)
        self.repeatSpinbox = ttk.Spinbox(
            top_frame,
            from_=1,
            to=999999999,
            command=self.repeat_changed
        )
        self.repeatSpinbox.grid(column=1, row=1, padx=8)
        self.repeatSpinbox.set(self.settings.get_config()["Playback"]["Repeat"]["Times"])

        bot_frame = Frame(self)
        bot_frame.pack(fill=BOTH, expand=True, padx=16)

        # Play Button
        self.playImg = PhotoImage(file=resource_path(path.join("assets", "button", "play.png")))

        # Import record if opened with .pmr extension
        if len(argv) > 1:
            with open(sys.argv[1], 'r') as record:
                loaded_content = load(record)
            self.macro.import_record(loaded_content)
            self.playBtn = Button(bot_frame, image=self.playImg, command=self.macro.start_playback)
            self.macro_recorded = True
            self.macro_saved = True
        else:
            self.playBtn = Button(bot_frame, image=self.playImg, state=DISABLED)
        self.playBtn.pack(side=LEFT, padx=8)

        # Record Button
        self.recordImg = PhotoImage(file=resource_path(path.join("assets", "button", "record.png")))
        self.recordBtn = Button(bot_frame, image=self.recordImg, command=self.macro.start_record)
        self.recordBtn.pack(side=RIGHT, padx=8)

        # Stop Button
        self.stopImg = PhotoImage(file=resource_path(path.join("assets", "button", "stop.png")))

        record_management = RecordFileManagement(self, self.menu)

        self.bind('<Control-Shift-S>', record_management.save_macro_as)
        self.bind('<Control-s>', record_management.save_macro)
        self.bind('<Control-l>', record_management.load_macro)
        self.bind('<Control-n>', record_management.new_macro)

        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        if platform.lower() != "darwin":
            Thread(target=self.systemTray).start()

        self.attributes("-topmost", 0)

        if platform != "win32" and self.settings.first_time:
            NotWindows(self)

        if self.settings.get_config()["Others"]["Check_update"]:
            if self.version.new_version != "" and self.version.version != self.version.new_version:
                if time() > self.settings.get_config()["Others"]["Remind_new_ver_at"]:
                    NewVerAvailable(self, self.version.new_version)

        self.withdraw()
        self.mainloop()

    def speed_changed(self, event):
        self.settings.change_settings("Playback", "Speed", None, self.speed_value.get())

    def repeat_changed(self):
        self.settings.change_settings("Playback", "Repeat", "Times", self.repeatSpinbox.get())

    def systemTray(self):
        """Just to show little icon on system tray"""
        image = Image.open(resource_path(path.join("assets", "logo.ico")))
        menu = (
            MenuItem('Show', action=self.deiconify, default=True),
            MenuItem('Quit', action=self.force_quit_window, default=True),
        )
        self.icon = Icon("name", image, "PyMacroRecord", menu)
        self.icon.run()

    def validate_input(self, action, value_if_allowed):
        """Prevents from adding letters on an Entry label"""
        if action == "1":  # Insert
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False
        return True

    def force_quit_window(self):
        self.quit_window(True)

    def quit_window(self, force=False):
        if not self.macro_saved and self.macro_recorded and not force:
            self.deiconify()
            wantToSave = confirm_save(self)
            if wantToSave:
                RecordFileManagement(self, self.menu).save_macro()
            elif wantToSave == None:
                return
        if platform.lower() != "darwin":
            self.icon.stop()
        #if platform.lower() == "linux":
        #    self.destroy()
        self.quit()
