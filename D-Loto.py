import tkinter as tk
import webbrowser
import os
import sys
import shutil
import datetime
import subprocess
import json
import logging
import time
from tkinter import ttk,filedialog
from tkinter import *
from tkinter import messagebox
from tkinter.font import Font
from datetime import datetime
from tkinter import font as tkFont
from PIL import Image, ImageTk
import ctypes
from ctypes import windll
ctypes.windll.shcore.SetProcessDpiAwareness(1)
import sqlite3
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


# # Set up logging to file
# log_file_path = os.path.join(os.path.dirname(sys.argv[0]), 'error_log.txt')
# logging.basicConfig(filename=log_file_path,
#                     level=logging.ERROR,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

# Example function to capture all uncaught exceptions
def log_exception(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# Register the handler
sys.excepthook = log_exception

# Setup rev of program
rev = '1.0.3'

# Helper function to get the resource path
def resource_path(relative_path):
    # For PyInstaller temporary folder if bundled
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Load the database path from config.json
config_path = resource_path("config.json")
with open(config_path, "r") as f:
    config = json.load(f)
database_path = config["database_path"]

# # Select the Folder to create DB
# #https://pttgrp.sharepoint.com/sites/PanelOperator/Shared Documents/Daily Log Book/LOTO
# # directory =  resource_path("C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/LNG Project/2024/2.LOTO Project")
# directory =  resource_path("L:/4.4LO.T1/06-Operational_and_Record/6.56 LOTO")
# db_name = "loto_data.db"
# database_path = os.path.join(directory,db_name)

# Connection test to DB 
def connect_to_database(db_path):
    if not os.path.exists(db_path):  # Check if the database file exists
        messagebox.showerror("Network Error", "Please try to connect to the L: drive. or check pttlng server '10.232.104.130'")
        return None

    try:
        conn = sqlite3.connect(db_path)  # Try to connect to the database
        return conn
    except sqlite3.OperationalError as e:  # Catch operational errors
        messagebox.showerror("Database Connection Error", f"Failed to connect to the database. Error: {e}")
        return None
    except Exception as e:  # Catch all other exceptions
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        return None

connect_to_database(database_path)


# Create CONNECTION to the DB (sqlite3-)atabase
conn = sqlite3.connect(database_path)

# Create CURSOR for do database operation
c = conn.cursor()

# Create table loto_overview
c.execute(""" CREATE TABLE IF NOT EXISTS loto_overview (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    loto_no TEXT,
                    work_title TEXT,
                    owner TEXT,
                    lock_date TEXT,
                    status TEXT)""")

# Insert data to loto_overview table
def insert_data(loto_no,work_title,owner,telephone):
    # CREATE
    with conn:
        command =  'INSERT INTO loto_overview VALUES (?,?,?,?,?,?)'
        c.execute(command,(None,loto_no,work_title,owner,telephone,'new'))
    conn.commit() # Save database

# Feth data from loto_overview table to Show
def view_data():
    # READ
    with conn:
        command = 'SELECT * FROM loto_overview'
        c.execute(command)
        result = c.fetchall()
        # print(result)
    return result

def view_data_new():
    with conn:
        command = """SELECT new_loto_no, new_work_title, new_incharge_dept, new_owner, new_prepare, new_lock_date, status
        FROM loto_new
        WHERE status = 'Waiting' OR status = 'Rejected' OR status = 'Postpone'
        """
        c.execute(command)
        result = c.fetchall()
    return result

def view_data_completed():
    with conn:
        command = """SELECT loto_no, work_title, owner, lock_date, completed_date, total_lock_days, status
        FROM loto_completed
        WHERE status = 'Completed' OR status = 'Cancel'
        """
        c.execute(command)
        result = c.fetchall()
    return result

# Create table loto_new
c.execute(""" CREATE TABLE IF NOT EXISTS loto_new (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_id TEXT,
                    new_work_title TEXT,
                    new_incharge_dept TEXT,
                    new_owner TEXT,
                    new_telephone TEXT,
                    new_area TEXT,
                    new_equipment TEXT,
                    new_lock_date TEXT,
                    new_loto_no TEXT,
                    new_loto_keys TEXT,
                    new_pid_pdf TEXT,
                    new_override_list TEXT,
                    new_remark TEXT,
                    new_prepare TEXT,
                    new_verify TEXT,
                    new_approve TEXT,
                    status TEXT)""")

# Insert data to loto_new DB
def insert_new_loto(log_id,new_work_title,new_incharge_dept,new_owner,
                new_telephone,new_area,new_equipment,new_lock_date,
                new_loto_no,new_loto_keys,new_pid_pdf,new_override_list,new_remark,
                new_prepare,new_verify,new_approve):
    # CREATE
    with conn:
        command =  'INSERT INTO loto_new VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
        c.execute(command,(None,log_id,new_work_title,new_incharge_dept,new_owner,
                new_telephone,new_area,new_equipment,new_lock_date,
                new_loto_no,new_loto_keys,new_pid_pdf,new_override_list,new_remark,
                new_prepare,new_verify,new_approve,'Waiting'))
    conn.commit() # Save database

# Feth data from loto_new to loto_overview for show
def transfer_data_overview():
    with conn:
        command = """
        INSERT INTO loto_overview (loto_no, work_title, owner, lock_date, status) 
        SELECT new_loto_no, new_work_title, new_incharge_dept, new_lock_date, status
        FROM loto_new 
        WHERE status IN ('Active', 'Onsite')
        AND (new_loto_no, new_work_title, new_incharge_dept, new_lock_date) NOT IN (
        SELECT loto_no, work_title, owner, lock_date FROM loto_overview)
        """
        c.execute(command)
    conn.commit()

    print("data transfered to overview tab")

def transfer_data_completed():
    with conn:
        command = """
        INSERT INTO loto_completed (loto_no, work_title, owner, lock_date, status) 
        SELECT new_loto_no, new_work_title, new_incharge_dept, new_lock_date, status
        FROM loto_new 
        WHERE status IN ('Completed', 'Cancel')
        AND (new_loto_no, new_work_title, new_incharge_dept, new_lock_date) NOT IN (
        SELECT loto_no, work_title, owner, lock_date FROM loto_completed)
        """
        c.execute(command)
    conn.commit()

    print("data transfered to completed tab")

# Create table loto_completed
c.execute(""" CREATE TABLE IF NOT EXISTS loto_completed (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    loto_no TEXT,
                    work_title TEXT,
                    owner TEXT,
                    lock_date TEXT,
                    completed_date TEXT,
                    total_lock_days TEXT,
                    status TEXT)""")

# the main application window
root = tk.Tk()
root.title("LOTO-LOT1")
root.resizable(False, False)

# CONFIGURE: Auto adjust size of windows program
# Get the scaling factor of the system
def get_scaling_factor():
    user32 = ctypes.windll.user32
    # Gets the DPI from the system; assuming 96 dpi is 100%
    dpi = user32.GetDpiForSystem()
    return dpi / 96  # Scaling factor
scaling_factor = get_scaling_factor()

# Define base dimensions (for 100% scaling)
base_width = 1050
base_height = 650

# Adjust dimensions based on the current scaling factor
adjusted_width = int(base_width * scaling_factor)
adjusted_height = int(base_height * scaling_factor)

# Folder location
# folder_path = resource_path("C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/LNG Project/2024/2.LOTO Project")
folder_path = resource_path("L:/4.4LO.T1/06-Operational_and_Record/6.56 LOTO/WorkList")

# Adjust position of GUI Window
def center_windows(w,h):
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2) - 30
    return f'{w}x{h}+{x:.0f}+{y:.0f}'
win1size = center_windows(adjusted_width,adjusted_height)
root.geometry(win1size)

# Define date string format
def date_str(select):
    a = datetime.now()
    day_today = a.strftime("%d")
    month_today = a.strftime("%m")
    year_today_F = a.strftime("%Y")
    year_today_S = a.strftime("%y")
    date_today = day_today+'/'+month_today+'/'+year_today_S
    folder_date = year_today_F+month_today+day_today
    remark_date = date_today+' '+a.strftime("%H:%M")
    if select == 1:
        return date_today
    elif select == 2:
        return folder_date
    elif select == 3:
        return remark_date

# Add function to the Field input
def on_focus_in(event):
        event.widget.config(highlightbackground="#5f87aa", highlightcolor="#5f87aa", highlightthickness=2)
def on_focus_out(event):
        event.widget.config(highlightbackground="grey", highlightcolor="grey", highlightthickness=1)
def focus_next_widget(event):
    """Move focus to the next widget in the tab order."""
    event.widget.tk_focusNext().focus()
    return "break"

# Set the icon program
def set_window_icon(root):
    icon_path = resource_path("IconProgram1.ico")
    icon_image = Image.open(icon_path)
    photo = ImageTk.PhotoImage(icon_image)
    root.iconphoto(True,photo)
set_window_icon(root)

# Resize icon image
def create_resized_image(path, width, height):
        # Load the image with Pillow
        original_image = Image.open(resource_path(path))
        # Resize the image
        resized_image = original_image.resize((width, height))
        # Convert to PhotoImage
        return ImageTk.PhotoImage(resized_image)

# Configure the label style and Font
def font_setup():
    FONT1 = tkFont.Font(family='Tahoma', size=9)
    FONT2 = tkFont.Font(family='Tahoma', size=10,weight='bold')
    FONT3 = tkFont.Font(family='Tahoma', size=10)
    FONT4 = tkFont.Font(family='Tahoma', size=18,weight='bold')
    FONT5 = tkFont.Font(family='Tahoma', size=14,weight='bold')
    FONT6 = tkFont.Font(family='Tahoma', size=9)
    FONT7 = tkFont.Font(family='Tahoma', size=9)
    FONT8 = tkFont.Font(family='Tahoma', size=9)
    return FONT1,FONT2,FONT3,FONT4,FONT5,FONT6,FONT7,FONT8
FONT1, FONT2, FONT3, FONT4, FONT5, FONT6, FONT7, FONT8 = font_setup()

# Configure theme 
style = ttk.Style(root)
style.theme_use("clam")

# Create and Custom TAB
def configure_widget_style(scaling_factor, FONT1, style):
    pad_x1 = int(4*scaling_factor)
    pad_y1 = int(3*scaling_factor)
    style.configure("Custom1.TNotebook.Tab", 
                # padding=[pad_x1, pad_y1], 
                font = FONT1)
    style.map("Custom1.TNotebook.Tab",
        #    expand = [("selected", [0, 0, 0, 0]), ("!selected", [0, 0, 0, 0])],
        background=[("selected", "lightblue")],
        foreground=[("selected", "Black")],
        focuscolor=[("selected", "lightblue")])
configure_widget_style(scaling_factor, FONT1, style)

# Add TAB to the GUI
notebook = ttk.Notebook(root, style="Custom1.TNotebook")
notebook.pack(expand=True, fill="both")

# Set focus on TAB
def set_focus_on_tab(index):
    notebook.select(index)

# Configure button styles
def configure_button_styles(scaling_factor, style):
    style.configure("Custom1.TButton", 
                font=("tahoma", 10),  # Font family, size, and style
                padding=(int(12*scaling_factor), int(8*scaling_factor)), # Padding (width, height)
                focuscolor='none')  
    style.configure("Custom2.TButton", 
                font=("tahoma", 9),  # Font family, size, and style
                padding=(int(8*scaling_factor), int(5*scaling_factor)), # Padding (width, height)
                focuscolor='none')  
    style.configure("Custom3.TButton", 
                font=("tahoma", 8),  # Font family, size, and style
                padding=(int(4*scaling_factor), int(5*scaling_factor)), # Padding (width, height)
                focuscolor='none')
configure_button_styles(scaling_factor, style)  

# Configure combobox styles
style.configure("Custom.TCombobox", arrowsize=25) # Adjust the size of the dropdown arrow

# Show message box
def show_message(title, message):
    messagebox.showinfo(title, message)

# Create list for Dropdown
def list_setup():
    incharge_list = ['MT.Mech','MT.Ins','MT.Elec','ED.Mech','ED.Ins','ED.Elec',
                'ED.Process','Project','LO.','ED.','PI',]

    owner_list = ['Jutharat.P','Chanida.H','Pajaree.L','Kittipong.V','Amporn.T',
            'Somchai.R','Witawit.P','Phaksunee.In','Chanchai.S','Jedsada.M',
            'Chalermpon.K','Siriwan.K','Dan.S','Pimjai.I','Gunthon.U','Wirasak.B',
            'Panuphot.P','Nugul.J','Parinya.Y','Seksan.S','Kritsakon.P','Jakkrit.C',
            'Nattagorn.R','Preeyaporn.S','Taipob.K','Sarawut.S','Yutasart.P','Sarayut.K',
            'Nopparat.J','Wisud.D','Dhosapol.S','Natthakorn.S','Kittituch.L','Tanisorn.S',
            'Piyapong.P','Weerayut.P','Rapeepan.W','Phissara.W','Issarush.K','Phaopan.T',
            'Teerayut.S','Rungroj.S','Narunard.H','Boonlert.S','Chatdanai.B','Maytungkorn.S',
            'Rachanon.Y','Artit.K','Anusorn.N','Nutrada.S','Pornthep.D','Pornthep.L',
            'Dumrongsak.J','Wanchai.J','Maythika.S','Wachirasak.L','Sirapong.W','Wisit.O',
            'Warin.I','Chomphoonuch.W','Kitipoom.T','Mongkol.S','Phuekpon.S','Kittipong.P',
            'Kittisak.T','Noppanan.T','Rattikool.P','Narupon.K','Ukrit.C','Teerasak.S',
            'Wimmalak.R','Isarah.P','Rinrada.K','Sakda.P','Amaris.U','Kittiwat.R','Visarn.K',
            'Kosin.S','Ronnaporn.K','Krit.Y','Wiwid.B','Weerachon.S','Hirun.U','Kanate.Th',
            'Ratchapon.P','Thanongsak.K','Eakkarin.B','Kittiwat.Ro','Weerawat.N','Korakot.C',
            'Suphamit.K','Tharadon.J','Naret.N','Chidsanupong.V','Suttipat.V','Sasiwan.M',
            'Worapon.P','Mutitaporn.P','Nattanich.B','Thanaphorn.T','Puttiporn.J','Piyanut.M',
            'Witthawat.K','Siriwit.P','Piyachai.M','Jantakan.P','Siwakan.K','Nuttanan.P',
            'Teepakorn.R','Thanaporn.S','Nadthanakorn.K','Thatsapong.S','Chintara.R','Tanchanok.W',
            'Siriphop.J','Sukritta.J','Chalermchat.C','Worapong.S','Yolada.O','Pakin.A',
            'Panyawat.L','Nateetorn.A','Jirayu.J','Kornpong.V','Tanawat.T','Nasrada.S','Mintra.M',
            'Nattakorn.B','Suphachai.C','Phuradech.M','Kamonchanok.J','Kriangkrai.A','Natthawut.C',
            'Pitchayut.P','Vichaiprat.S','Wechpisit.S','Palathip.S','Jirapon.P','Pacharapol.J',
            'Surasak.D','Trin.J','Sanya.R','Naruepol.L','Puttachat.T','Narisara.P','Sarit.J',
            'Kodchakorn.W','Sirawit.S','Saransak.N','Natnicha.L','Thut.B','Peeranut.N','Soravit.C',
            'Koragoch.T','Sukrit.I','Theerawit.J','Saranya.W','Napak.W','Warunyoo.W','Karan.B',
            'Papawich.P','Prolamath.P','Natchaiyot.W','Kridsakorn.S','Pornphun.C','Khathawut.B',
            'Thapanee.M','Nara.T','Chanitpak.A','Dhana.P','Tritep.O','Suphachot.P','Arnonnat.C',
            'Natchapol.H','Jakkrit.S','Wuttipat.W','Khemmachat.P','Tossapol.K','Suwicha.N',
            'Alongkorn.K','Amorntep.S','Boonchoo.J','Kiangkai.C','Supanat.T','Narudech.S',
            'Thanasak.S','Weerapong.L','Peeranut.S','Jetsadakorn.B','Siravit.C','Poramane.C',
            'Natcharikan.P','Nopphakao.C','Ativit.P','Phichate.N','Thonthan.J','Raviwat.T',
            'Phanuwat.J','Sudaphorn.Y','Supachai.Y','Anurak.S','Danuwat.B','Phuangpayom.S',
            'Surachai.U','Chayathorn.C','Warayus.S','Siripop.P','Thanayod.W','Nawi.T',
            'Thanatchaporn.K','Sarawut.Bo','Jenjira.R','Sittichok.C','Komtanut.C','Raiwin.N',
            'Ratatummanoon.S','Thitithanu.B','Chinnakrit.M','Thanadon.T','Nutchana.N','Veeraphat.K',
            'Chatchaiwat.R','Nawin.S','Wichanath.P','Thitapa.C','Warut.T']

    sectionmgr_list = ['Yutasart.P','Kritsakon.P','Piyapong.P','Sarayut.K','Dumrongsak.J','Kittiwat.Ro',]

    lomember_list = ['Parinya.Y','Kritsakon.P','Sarawut.S','Yutasart.P','Sarayut.K',
                'Tanisorn.S','Piyapong.P','Weerayut.P','Rachanon.Y','Artit.K',
                'Dumrongsak.J','Mongkol.S','Kittiwat.Ro','Weerawat.N','Naret.N',
                'Suttipat.V','Jantakan.P','Phuradech.M','Wechpisit.S','Palathip.S',
                'Koragoch.T','Saranya.W','Suphachot.P','Jakkrit.S','Wuttipat.W',
                'Boonchoo.J','Thanasak.S','Nopphakao.C','Thanayod.W','Sittichok.C',
                'Komtanut.C','Chinnakrit.M','Thanadon.T','Veeraphat.K','Nawin.S']

    area_list = ['HP Pump','BOG Compressor','SOG Compressor','Recondenser','BOG Suction drum',
            'Truck load','LNG Tank','Drain pump','ORV','IA / N2 ','Sanitary','NG Metering',
            'Chlorination','Seawater pump','Seawater intake','Jetty Berth1','Jetty Berth2',
            'Jetty Berth3','LNG Sampling','Firewater pump','ORC','GTG','WHRU','IFV',
            'CWG Pump','CWG','IPG IA','IPG Metering','OSBL MAP Metering','OSBL GSP#7 Metering','Admin building','Canteen building','GIS I','GIS II',
            'Fire station','Maintenance workshop','LAB','Warehouse','AIB Building',
            'CCR Building','Main Substation','IPG Substation','JCR Building',
            'Jetty Substation','Truck load admin','Truck load control room','Potable water',
            'Service water','OSBL MAP','OSBL GSP7','MHX','Ground flare','New IA','ITCP','ITCP Metering']

    machine_list = ['HP Pump A','HP Pump B','HP Pump C','HP Pump D','HP Pump E','HP Pump F','HP Pump G','HP Pump H','HP Pump I','HP Pump J','HP Pump K',
                'BOG Compressor A','BOG Compressor B','BOG Compressor C','BOG Compressor D','SOG Compressor A','SOG Compressor B',
                'Seawater pump A','Seawater pump B','Seawater pump C','Seawater pump D','Seawater pump E',
                'ORV A','ORV B','ORV C','ORV D','ORV E','ORV F','ORV G','ORV H','ORV I','ORV J',
                'Truck bay A','Truck bay B','Truck bay C','Truck bay D','Metering A','Metering B','Metering C','Metering D','Metering E',
                'Intank pump  1A','Intank pump  1B','Intank pump  1C','Intank pump  2A','Intank pump  2B','Intank pump  2C',
                'Intank pump  3A','Intank pump  3B','Intank pump  3C','Intank pump  4A','Intank pump  4B','Intank pump  4C',
                'LNG Tank 1','LNG Tank 2','LNG Tank 3','LNG Tank 4','IA Comp A','IA Comp B','IA Air dryer A','IA Air dryer B',
                'Drain pump','Electrolyzer A','Electrolyzer B','Booster pump A','Booster pump B','Dosing pump A','Dosing pump B',
                'Dosing pump C','Air Blower A','Air Blower B','IFV A','IFV B','Warm water pump A','Warm water pump B','Warm water pump C',
                'Warm water pump D','Warm water pump E','IPG water pump A','IPG water pump B','IPG water pump C','IPG water pump D',
                'IPG water pump E','HVAC water pump A','HVAC water pump B','HVAC water pump C','HVAC water pump D','HVAC water pump E',
                'GTG A','GTG B','WHRU A','WHRU B','ORC','ORC Seal oil system','ORC Lube oil system','CEMs','CYP Pump A','CYP Pump B',
                'IPG IA Comp A','IPG IA Comp B','IPG IA Air dryer A','IPG IA Air dryer B','Hot oil pump A','Hot oil pump B','WHRU-A Seal fan A',
                'WHRU-A Seal fan B','WHRU-B Seal fan A','WHRU-B Seal fan B','Truck bay A','Truck bay B','Truck bay C','Truck bay D',
                'Unloading arm','Jetty platform','MD','BD','Hydrualic oil pump','Fire truck','Deluge valve','Fire extinguisher',
                'B.1 MLA "A"','B.1 MLA "B"','B.1 MLA "C"','B.1 MLA "D"','B.2 MLA "E"',
                'B.2 MLA "F"','B.2 MLA "G"','B.2 MLA "H"','B.2 MLA "I"', 'DFBS A', 'DFBS B', 'DFBS C',
                'DFBS D', 'DFBS E', 'Wash water pump A', 'Wash water pump B', 'Wash water pump C', 'Service water pump A', 'Service water pump B',
                'Potable water pump A','Potable water pump B','Valve','MHX','New IA','Jockey pump A','Jockey pump B','Diesel fire water pump','Electrical firewater pump']

    email_list = {'Parinya.Y': 'parinya.y@pttlng.com','Kritsakon.P': 'kritsakon.p@pttlng.com',
            'Sarawut.S': 'sarawut.s@pttlng.com','Yutasart.P': 'yutasart.p@pttlng.com',
            'Sarayut.K': 'sarayut.k@pttlng.com','Tanisorn.S': 'tanisorn.s@pttlng.com',
            'Piyapong.P': 'piyapong.p@pttlng.com','Weerayut.P': 'weerayut.p@pttlng.com',
            'Rachanon.Y': 'rachanon.y@pttlng.com','Artit.K': 'artit.k@pttlng.com',
            'Dumrongsak.J': 'dumrongsak.j@pttlng.com','Mongkol.S': 'mongkol.s@pttlng.com',
            'Kittiwat.Ro': 'kittiwat.ro@pttlng.com','Weerawat.N': 'weerawat.n@pttlng.com',
            'Naret.N': 'naret.n@pttlng.com','Suttipat.V': 'suttipat.v@pttlng.com',
            'Jantakan.P': 'jantakan.p@pttlng.com','Phuradech.M': 'phuradech.m@pttlng.com',
            'Wechpisit.S': 'wechpisit.s@pttlng.com','Palathip.S': 'palathip.s@pttlng.com',
            'Koragoch.T': 'koragoch.t@pttlng.com','Saranya.W': 'saranya.w@pttlng.com',
            'Suphachot.P': 'suphachot.p@pttlng.com','Jakkrit.S': 'jakkrit.s@pttlng.com',
            'Wuttipat.W': 'wuttipat.w@pttlng.com','Boonchoo.J': 'boonchoo.j@pttlng.com',
            'Thanasak.S': 'Thanasak.s@pttlng.com','Nopphakao.C': 'Nopphakao.c@pttlng.com',
            'Thanayod.W': 'thanayod.w@pttlng.com','Sittichok.C': 'sittichok.c@pttlng.com',
            'Komtanut.C': 'komtanut.c@pttlng.com','Chinnakrit.M': 'chinnakrit.m@pttlng.com',
            'Thanadon.T': 'thanadon.t@pttlng.com','Veeraphat.K': 'veeraphat.k@pttlng.com',
            'Nawin.S': 'nawin.s@pttlng.com',}
    
    return incharge_list,owner_list,sectionmgr_list,lomember_list,area_list,machine_list, email_list
incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list = list_setup()

# Fetch data from DB and Reset the table in GUI
def refresh_treeview():
    print("Refreshing treeview")
    update_table_overview()
    update_table_pending()
    update_table_completed()
total_loto = 0
def update_table_overview():
    global total_loto
    total_loto = 0
    loto_datalist.delete(*loto_datalist.get_children())
    transfer_data_overview()
    data = view_data()
    for index, (d) in enumerate(data):
        d = list(d)
        del d[0]
        status = d[4]
        tag = 'evenrow' if index % 2 == 0 else 'oddrow'
        if status == 'Active':
            loto_datalist.insert('', 'end', values=d, tags=(tag,))
            total_loto += 1
    label1.config(text=f"Total active LOTO : {total_loto}")
total_loto_p = 0    
def update_table_pending():
    global total_loto_p
    total_loto_p = 0
    loto_datalist_p.delete(*loto_datalist_p.get_children())
    data = view_data_new()
    total_loto_p = len(data)
    for index, (d) in enumerate(data):
        d = list(d)
        tag = 'evenrow' if index % 2 == 0 else 'oddrow'
        loto_datalist_p.insert('','end',values=d,tags=tag)
    label1_p.config(text=f"Total active LOTO : {total_loto_p}")
total_loto_c = 0
def update_table_completed():
    global total_loto_c
    total_loto_c = 0
    loto_datalist_c.delete(*loto_datalist_c.get_children())
    data = view_data_completed()
    total_loto_c = len(data)
    for index, (d) in enumerate(data):
        d = list(d)
        tag = 'evenrow' if index % 2 == 0 else 'oddrow'
        loto_datalist_c.insert('','end',values=d,tags=tag)
    label1_c.config(text=f"Total LOTO : {total_loto_c}")

def fetch_data_from_loto_new(v1,v2,v3):
        loto_no = v1
        work_title = v2
        lock_date = v3
        result = add_data_to_popup(loto_no,work_title,lock_date)
        return result

# CREATE: Function Show top level when Double clikc at Table
def on_row_double_click_overview(event):
    # Get the treeview widget that triggered the event
    table_select = event.widget
    
    # Check if an item is selected in the table
    selected_item = table_select.selection()
    if not selected_item:
        messagebox.showinfo("Error", "No item selected.")
        return
    selected_item = selected_item[0]
    item_values = table_select.item(selected_item, "values")
    # Recieve the value from the table at Overview tab
    v1 = item_values[0]
    v2 = item_values[1]
    v3 = item_values[3]

    # Fetch data from the database based on the selected item's values
    data_to_popup = fetch_data_from_loto_new(v1,v2,v3)
    data_to_popup = list(data_to_popup[0])
    # Create a new Toplevel window
    detail_overview_GUI, NewLoto_x, NewLoto_y = create_new_window('Detail')

    # Configure the label style and layout
    configure_label_style()

    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(detail_overview_GUI,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(detail_overview_GUI, text="Work detail",style="label1.TLabel")
    label1.place(x=int(20*scaling_factor),y=int(13*scaling_factor))
    line1_x1 = int(16*scaling_factor)
    line1_y1 = int(25*scaling_factor)
    line1_x2 = int(463*scaling_factor)
    line1_y2 = int(490*scaling_factor)
    line1.create_rectangle(line1_x1,line1_y1,line1_x2,line1_y2,fill='#dcdad5',width=1,outline='#a9a7a3')
    line1.create_rectangle(line1_x1+scaling_factor,line1_y1+scaling_factor,
                        line1_x2-scaling_factor,line1_y2-scaling_factor,
                        fill='#dcdad5',width=1,outline='#f8f2ea')
    
    ## CREATE: FRAME
    frame3 = tk.Frame(detail_overview_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(265*scaling_factor), y=int(495*scaling_factor), width=200*scaling_factor, height=40*scaling_factor)

    ## CREATE: BUTTON
    button_y = 501
    button1 = ttk.Button(detail_overview_GUI, text="COMPLETED", style="Custom2.TButton",command=lambda: completed_button_for_overview(detail_overview_GUI,detail_overview_GUI,data_to_popup[9],data_to_popup[2],
                                                                                                        data_to_popup[8]))
    button1.place(x=16*scaling_factor,y=button_y*scaling_factor)
    button2 = ttk.Button(frame3, text="UPDATE", style="Custom2.TButton",command=lambda: update_button_for_overview(detail_overview_GUI,data_to_popup[9],data_to_popup[2],
                                                                                                        data_to_popup[8],open_folder_replace_data_to_popup_11
                                                                                                        ,refresh_gui3_data))
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="POSTPONE", style="Custom2.TButton",command=lambda: postpone_button_for_overview(detail_overview_GUI,data_to_popup[9],data_to_popup[2],
                                                                                                        data_to_popup[8]))
    button3.pack(side=RIGHT)

    #### FUNCTION: Loop for indicate hieght each row
    topic_x = int(30*scaling_factor)
    entry_1 = [int(40*scaling_factor)]
    current_ent = 0
    for i in range(1,12):
        current_ent = entry_1[i-1]+int(27*scaling_factor)
        entry_1.append(current_ent)

    if not data_to_popup[11]:
        # print(f'location is {data_to_popup[11]}')
        date_from_db = data_to_popup[8]
        # Create object date string
        date_obj = datetime.strptime(date_from_db,"%d/%m/%y")
        # Change format to "YYYYMMDD"
        date_for_folder = date_obj.strftime("%Y%m%d")
        folder_name = f"{date_for_folder}_{data_to_popup[6]}_{data_to_popup[2]}"
        new_folder_path = os.path.join(folder_path, folder_name)
        open_folder_replace_data_to_popup_11 = new_folder_path
        # print(f'The folder path is {open_folder_replace_data_to_popup_11}')
    else:
        open_folder_replace_data_to_popup_11 = data_to_popup[11]
    # Create entries
    create_work_title_show(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[2], open_folder=open_folder_replace_data_to_popup_11, 
                        toggle_var=False,fg='#4f4f4f')
    create_incharge_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[3], toggle_var=False,fg='#4f4f4f')
    create_owner_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[4], toggle_var=False,fg='#4f4f4f')
    create_telephone_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[5], toggle_var=False,fg='#4f4f4f')
    create_working_area_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[6], toggle_var=False,fg='#4f4f4f')
    create_equipment_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[7], toggle_var=False,fg='#4f4f4f')
    create_lock_date_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[8], toggle_var=False,fg='#4f4f4f')
    create_loto_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[9], toggle_var=False,fg='#4f4f4f')
    create_total_lock_keys_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[10], toggle_var=False,fg='#4f4f4f')
    pdf_entry_GUI3 = create_pdf_show(detail_overview_GUI, entry_1, pdf_url=data_to_popup[11])
    override_entry_GUI3 = create_overide_show(detail_overview_GUI, entry_1, ovrd_url=data_to_popup[12])
    remark_entry_GUI3 = create_remark_entry_for_update_widget(detail_overview_GUI, entry_1, default_text=data_to_popup[13], toggle_var=False,fg='#4f4f4f')
    remark_entry_GUI3.text_widget.see(tk.END)

    
    # print(f'folder path is: {data_to_popup[11]}')
    def refresh_gui3_data(v_loto_no, v_work_title, v_lock_date):
        # Destroy the current widget
        remark_entry_GUI3.destroy()
        override_entry_GUI3.destroy()
        pdf_entry_GUI3.destroy()
        # Fetch updated data from the database
        updated_data = fetch_data_from_loto_new(v_loto_no, v_work_title, v_lock_date)

        if updated_data:
            new_remark = updated_data[0][13]  # Remark
            new_pdf = updated_data[0][11]     # PDF path
            new_override = updated_data[0][12]  # Override list
            # Update the remark entry in detail_overview_GUI
            pdf_update = create_pdf_show(detail_overview_GUI, entry_1, pdf_url=new_pdf)
            override_update = create_overide_show(detail_overview_GUI, entry_1, ovrd_url=new_override)
            input_field_remark_for_update_button = create_remark_entry_for_update_widget(detail_overview_GUI, entry_1, default_text=new_remark, toggle_var=False,fg='#4f4f4f')
            input_field_remark_for_update_button.text_widget.see(tk.END)

    # Loop for indicating height of each row
    entry_2 = [int(395 * scaling_factor)]
    current_ent = 0
    for i in range(1, 3):
        current_ent = entry_2[i - 1] + int(26 * scaling_factor)
        entry_2.append(current_ent)

    # Create additional entries
    create_prepare_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[14], toggle_var=False,fg='#4f4f4f')
    create_verify_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[15], toggle_var=False,fg='#4f4f4f')
    create_approve_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[16], toggle_var=False,fg='#4f4f4f')

    return detail_overview_GUI
    detail_overview_GUI.mainloop

def on_row_double_click_pending(event=None):
    # Get the treeview widget that triggered the event
    table_select = event.widget
    
    # Check if an item is selected in the table
    selected_item = table_select.selection()
    if not selected_item:
        messagebox.showinfo("Error", "No item selected.")
        return
    selected_item = selected_item[0]
    item_values = table_select.item(selected_item, "values")

    v1 = item_values[0]
    v2 = item_values[1]
    v3 = item_values[5]
    data_to_popup = fetch_data_from_loto_new(v1,v2,v3)
    data_to_popup = list(data_to_popup[0])
    # print(f'data_to_popup is : {data_to_popup}')


    # Create a new Toplevel window
    detail_overview_GUI,NewLoto_x,NewLoto_y = create_new_window('Detail')

    # CONFIGURE: label1 (Main)
    configure_label_style()

    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(detail_overview_GUI,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(detail_overview_GUI, text="Work detail",style="label1.TLabel")
    label1.place(x=int(20*scaling_factor),y=int(13*scaling_factor))
    line1_x1 = int(16*scaling_factor)
    line1_y1 = int(25*scaling_factor)
    line1_x2 = int(463*scaling_factor)
    line1_y2 = int(490*scaling_factor)
    line1.create_rectangle(line1_x1,line1_y1,line1_x2,line1_y2,fill='#dcdad5',width=1,outline='#a9a7a3')
    line1.create_rectangle(line1_x1+scaling_factor,line1_y1+scaling_factor,
                        line1_x2-scaling_factor,line1_y2-scaling_factor,
                        fill='#dcdad5',width=1,outline='#f8f2ea')
    
    ## CREATE: FRAME
    frame3 = tk.Frame(detail_overview_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(265*scaling_factor), y=int(495*scaling_factor), width=200*scaling_factor, height=40*scaling_factor)

    ## CREATE: BUTTON
    button2 = ttk.Button(frame3, text="APPROVE", style="Custom2.TButton",command=lambda: approve_button_for_pending(detail_overview_GUI,data_to_popup[9],data_to_popup[2],
                                                                                                        data_to_popup[8]))
    button2.pack(side=LEFT)

    button3 = ttk.Button(frame3, text="REJECT", style="Custom2.TButton",command=lambda: reject_button_for_pending(detail_overview_GUI,data_to_popup[9],data_to_popup[2],
                                                                                                        data_to_popup[8]))
    button3.pack(side=RIGHT)

    #### FUNCTION: Loop for indicate hieght each row
    topic_x = int(30*scaling_factor)
    entry_1 = [int(40*scaling_factor)]
    current_ent = 0
    for i in range(1,12):
        current_ent = entry_1[i-1]+int(27*scaling_factor)
        entry_1.append(current_ent)
    
        if not data_to_popup[11]:
        # print(f'location is {data_to_popup[11]}')
            date_from_db = data_to_popup[8]
            # Create object date string
            date_obj = datetime.strptime(date_from_db,"%d/%m/%y")
            # Change format to "YYYYMMDD"
            date_for_folder = date_obj.strftime("%Y%m%d")
            folder_name = f"{date_for_folder}_{data_to_popup[6]}_{data_to_popup[2]}"
            new_folder_path = os.path.join(folder_path, folder_name)
            open_folder_replace_data_to_popup_11 = new_folder_path
        # print(f'The folder path is {open_folder_replace_data_to_popup_11}')
        else:
            open_folder_replace_data_to_popup_11 = data_to_popup[11]

    # Create entries
    create_work_title_show(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[2], open_folder=open_folder_replace_data_to_popup_11, 
                        toggle_var=False,fg='#4f4f4f')
    create_incharge_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[3], toggle_var=False,fg='#4f4f4f')
    create_owner_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[4], toggle_var=False,fg='#4f4f4f')
    # create_internal_phone_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[5], toggle_var=False,fg='#4f4f4f')
    create_telephone_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[5], toggle_var=False,fg='#4f4f4f')
    create_working_area_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[6], toggle_var=False,fg='#4f4f4f')
    create_equipment_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[7], toggle_var=False,fg='#4f4f4f')
    create_lock_date_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[8], toggle_var=False,fg='#4f4f4f')
    create_loto_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[9], toggle_var=False,fg='#4f4f4f')
    create_total_lock_keys_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[10], toggle_var=False,fg='#4f4f4f')
    create_pdf_show(detail_overview_GUI, entry_1, pdf_url=data_to_popup[11])
    create_overide_show(detail_overview_GUI, entry_1, ovrd_url=data_to_popup[12])
    create_remark_entry_for_update_widget(detail_overview_GUI, entry_1, default_text=data_to_popup[13], toggle_var=False,fg='#4f4f4f')

    # Loop for indicating height of each row
    entry_2 = [int(395 * scaling_factor)]
    current_ent = 0
    for i in range(1, 3):
        current_ent = entry_2[i - 1] + int(26 * scaling_factor)
        entry_2.append(current_ent)

    # Create additional entries
    create_prepare_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[14], toggle_var=False,fg='#4f4f4f')
    create_verify_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[15], toggle_var=False,fg='#4f4f4f')
    create_approve_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[16], toggle_var=False,fg='#4f4f4f')

    return detail_overview_GUI
    detail_overview_GUI.mainloop

def on_row_double_click_completed(event=None):
    # Get the treeview widget that triggered the event
    table_select = event.widget
    
    # Check if an item is selected in the table
    selected_item = table_select.selection()
    if not selected_item:
        messagebox.showinfo("Error", "No item selected.")
        return
    selected_item = selected_item[0]
    item_values = table_select.item(selected_item, "values")
    v1 = item_values[0]
    v2 = item_values[1]
    v3 = item_values[3]

    # Fetch data from the database based on the selected item's values
    data_to_popup = fetch_data_from_loto_new(v1,v2,v3)
    data_to_popup = list(data_to_popup[0])
    # Create a new Toplevel window
    detail_overview_GUI, NewLoto_x, NewLoto_y = create_new_window('Detail')

    # Configure the label style and layout
    configure_label_style()

    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(detail_overview_GUI,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(detail_overview_GUI, text="Work detail",style="label1.TLabel")
    label1.place(x=int(20*scaling_factor),y=int(13*scaling_factor))
    line1_x1 = int(16*scaling_factor)
    line1_y1 = int(25*scaling_factor)
    line1_x2 = int(463*scaling_factor)
    line1_y2 = int(490*scaling_factor)
    line1.create_rectangle(line1_x1,line1_y1,line1_x2,line1_y2,fill='#dcdad5',width=1,outline='#a9a7a3')
    line1.create_rectangle(line1_x1+scaling_factor,line1_y1+scaling_factor,
                        line1_x2-scaling_factor,line1_y2-scaling_factor,
                        fill='#dcdad5',width=1,outline='#f8f2ea')
    
    ## CREATE: FRAME
    frame3 = tk.Frame(detail_overview_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(265*scaling_factor), y=int(495*scaling_factor), width=200*scaling_factor, height=40*scaling_factor)

    ## CREATE: BUTTON
    # button3 = ttk.Button(frame3, text="CANCEL", style="Custom2.TButton",command=detail_overview_GUI.destroy)
    # button3.pack(side=RIGHT)

    #### FUNCTION: Loop for indicate hieght each row
    topic_x = int(30*scaling_factor)
    entry_1 = [int(40*scaling_factor)]
    current_ent = 0
    for i in range(1,12):
        current_ent = entry_1[i-1]+int(27*scaling_factor)
        entry_1.append(current_ent)

    if not data_to_popup[11]:
        # print(f'location is {data_to_popup[11]}')
        date_from_db = data_to_popup[8]
        # Create object date string
        date_obj = datetime.strptime(date_from_db,"%d/%m/%y")
        # Change format to "YYYYMMDD"
        date_for_folder = date_obj.strftime("%Y%m%d")
        folder_name = f"{date_for_folder}_{data_to_popup[6]}_{data_to_popup[2]}"
        new_folder_path = os.path.join(folder_path, folder_name)
        open_folder_replace_data_to_popup_11 = new_folder_path
        # print(f'The folder path is {open_folder_replace_data_to_popup_11}')
    else:
        open_folder_replace_data_to_popup_11 = data_to_popup[11]
    # Create entries
    create_work_title_show(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[2], open_folder=open_folder_replace_data_to_popup_11, 
                        toggle_var=False,fg='#4f4f4f')
    create_incharge_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[3], toggle_var=False,fg='#4f4f4f')
    create_owner_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[4], toggle_var=False,fg='#4f4f4f')
    create_telephone_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[5], toggle_var=False,fg='#4f4f4f')
    create_working_area_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[6], toggle_var=False,fg='#4f4f4f')
    create_equipment_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[7], toggle_var=False,fg='#4f4f4f')
    create_lock_date_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[8], toggle_var=False,fg='#4f4f4f')
    create_loto_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[9], toggle_var=False,fg='#4f4f4f')
    create_total_lock_keys_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[10], toggle_var=False,fg='#4f4f4f')
    create_pdf_show(detail_overview_GUI, entry_1, pdf_url=data_to_popup[11])
    create_overide_show(detail_overview_GUI, entry_1, ovrd_url=data_to_popup[12])
    remark_entry_GUI3 = create_remark_entry_for_update_widget(detail_overview_GUI, entry_1, default_text=data_to_popup[13], toggle_var=False,fg='#4f4f4f')
    remark_entry_GUI3.text_widget.see(tk.END)

    # Loop for indicating height of each row
    entry_2 = [int(395 * scaling_factor)]
    current_ent = 0
    for i in range(1, 3):
        current_ent = entry_2[i - 1] + int(26 * scaling_factor)
        entry_2.append(current_ent)

    # Create additional entries
    create_prepare_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[14], toggle_var=False,fg='#4f4f4f')
    create_verify_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[15], toggle_var=False,fg='#4f4f4f')
    create_approve_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[16], toggle_var=False,fg='#4f4f4f')

    return detail_overview_GUI
    detail_overview_GUI.mainloop

def create_approve_reject_window(title_name,size_x,size_y,parent=None):
    new_loto_GUI = tk.Toplevel(parent, background='#dcdad5')
    NewLoto_x = int(size_x*scaling_factor)
    NewLoto_y = int(size_y*scaling_factor)
    win2size = center_windows(NewLoto_x,NewLoto_y)
    new_loto_GUI.geometry(win2size)
    new_loto_GUI.title(title_name) 
    new_loto_GUI.resizable(False, False)
    return new_loto_GUI,NewLoto_x,NewLoto_y
    
def add_data_to_popup(loto_no, work_title, lock_date):
    with conn:
        command = """
        SELECT * FROM loto_new
        WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
        """
        c.execute(command, (loto_no, work_title, lock_date))
        result = c.fetchall()  # Fetch all the matching records
        # print(f'Result from add_data_to_popup is: {result}')
    return result

def approve_button_for_pending(parent_window, v_loto_no, v_work_title, v_lock_date):
    approve_button_in_pending_GUI,NewLoto_x,NewLoto_y  = create_approve_reject_window('Approve',380,200,parent=parent_window)
    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(approve_button_in_pending_GUI,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(approve_button_in_pending_GUI, text="Approve detail",style="label1.TLabel")
    label1.place(x=int(20*scaling_factor),y=int(13*scaling_factor))
    line1_x1 = int(16*scaling_factor)
    line1_y1 = int(25*scaling_factor)
    line1_x2 = int(NewLoto_x-(17*scaling_factor))
    line1_y2 = int(NewLoto_y-(50*scaling_factor))
    line1.create_rectangle(line1_x1,line1_y1,line1_x2,line1_y2,fill='#dcdad5',width=1,outline='#a9a7a3')
    line1.create_rectangle(line1_x1+scaling_factor,line1_y1+scaling_factor,
                        line1_x2-scaling_factor,line1_y2-scaling_factor,
                        fill='#dcdad5',width=1,outline='#f8f2ea')
    
    ## CREATE: FRAME FOR BUTTON
    frame3 = tk.Frame(approve_button_in_pending_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(NewLoto_x-(216*scaling_factor)), y=int(NewLoto_y-(45*scaling_factor)), width=200*scaling_factor, height=40*scaling_factor)
    ## CREATE: BUTTON
    button2 = ttk.Button(frame3, text="CONFIRM", style="Custom2.TButton",command=lambda: confirm_button_approve(approve_button_in_pending_GUI,parent_window, v_loto_no, v_work_title, 
                                                                                                                v_lock_date, v_remark0, 
                                                                                                                v_approve0,state=True,refresh_callback=refresh_treeview))
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton",command=approve_button_in_pending_GUI.destroy)
    button3.pack(side=RIGHT)
    ## CREATE: LABEL FOR REMARK
    label_remark = ttk.Label(approve_button_in_pending_GUI,text='Remark:',style="label2.TLabel")
    label_remark.place(x=28*scaling_factor,y=45*scaling_factor)
    ## CREATE: REMARK ENTRY
    v_remark0 = StringVar()
    default_text = "***Remark entry***"
    input_field_remark_for_approve_button(approve_button_in_pending_GUI,font=FONT7,scaling_factor=scaling_factor,textvariable=v_remark0,
                            placeholder=default_text,fg='grey',y_position=(45*scaling_factor))
    ## CREATE: APPROVE LABEL AND ENTRY
    v_approve0 = StringVar()
    default_text = "ex.Kritsakon.P"
    E14 = input_field_dropdown(GUI=approve_button_in_pending_GUI,label='Approve by:',options=sectionmgr_list,textvariable=v_approve0,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=True,fg='Grey',
            x_position=-34,frame_width=-90,widget_width=-39)
    E14.place(x=18*scaling_factor,y=110*scaling_factor)

def confirm_button_approve(approve_button_in_pending_GUI, detail_overview_GUI, v_loto_no, v_work_title, v_lock_date, v_remark, v_approve,state,refresh_callback=None):
    # print(f'v_loto_no: {v_loto_no}')
    # print(f'v_remark: {v_remark}')
    remark_value0 = v_remark.get()
    approve_value = v_approve.get()
    remark_value = date_str(3) + ' approve by ' + approve_value + '\n' + remark_value0
    print('working on the confirm_button_approve')
    print(f'v_loto_no: {v_loto_no}')
    print(f'v_work_title: {v_work_title}')
    print(f'v_lock_date: {v_lock_date}')
    with conn:
        command_fetch = """
        SELECT new_remark, new_approve, status
        FROM loto_new
        WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
        """
        # print('working on the fetch')
        c.execute(command_fetch, (v_loto_no, v_work_title, v_lock_date))
        result = c.fetchone()
        # print(f'result: {result}')

        if result:
            # Extract the existing remark, approve, and status
            existing_remark = result[0]  # This is the existing remark
            existing_approve = result[1]  # This is the existing approval person
            current_status = result[2]  # This is the current status
            

            # Check if the status is "Waiting" before proceeding
            if current_status == "Waiting" or current_status == "Rejected" or current_status == "Postpone":
                # 1. Add the new remark after the old one (on a new line)
                updated_remark = f"{existing_remark}\n{remark_value}" if existing_remark else remark_value
                # 2. Replace the old approval with the new one
                updated_approve = approve_value
                # 3. Change the status to "Active", Wating -> Active for test
                # print('Working on the state')
                if state == True:
                    updated_status = "Active"
                    # print(f'updated_status: {updated_status}')
                elif state == False:
                    updated_status = "Rejected"
                # 4. Update the lock date to the current date
                updated_lock_date = date_str(1)
                # print(f'updated_lock_date: {updated_lock_date}')

            # Update the record in the database
                command_update = """
                UPDATE loto_new
                SET new_remark = ?, new_approve = ?, status = ?, new_lock_date = ?
                WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
                """
                c.execute(command_update, (updated_remark, updated_approve, updated_status, updated_lock_date, v_loto_no, v_work_title, v_lock_date))
                conn.commit()   
    transfer_data_overview()

    if refresh_callback:
        refresh_callback()

    print("GUI DESTROY")
    approve_button_in_pending_GUI.destroy()
    detail_overview_GUI.destroy()

def reject_button_for_pending(parent_window, v_loto_no, v_work_title, v_lock_date):
    reject_button_in_pending_GUI,NewLoto_x,NewLoto_y  = create_approve_reject_window('Reject',380,200,parent=parent_window)
    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(reject_button_in_pending_GUI,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(reject_button_in_pending_GUI, text="Reject detail",style="label1.TLabel")
    label1.place(x=int(20*scaling_factor),y=int(13*scaling_factor))
    line1_x1 = int(16*scaling_factor)
    line1_y1 = int(25*scaling_factor)
    line1_x2 = int(NewLoto_x-(17*scaling_factor))
    line1_y2 = int(NewLoto_y-(50*scaling_factor))
    line1.create_rectangle(line1_x1,line1_y1,line1_x2,line1_y2,fill='#dcdad5',width=1,outline='#a9a7a3')
    line1.create_rectangle(line1_x1+scaling_factor,line1_y1+scaling_factor,
                        line1_x2-scaling_factor,line1_y2-scaling_factor,
                        fill='#dcdad5',width=1,outline='#f8f2ea')
    ## CREATE: FRAME FOR BUTTON
    frame3 = tk.Frame(reject_button_in_pending_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(NewLoto_x-(216*scaling_factor)), y=int(NewLoto_y-(45*scaling_factor)), width=int(200*scaling_factor), height=int(40*scaling_factor))
    ## CREATE: BUTTON
    button2 = ttk.Button(frame3, text="CONFIRM", style="Custom2.TButton",command=lambda: confirm_button_approve(reject_button_in_pending_GUI,parent_window, v_loto_no, v_work_title, 
                                                                                                                v_lock_date, v_remark0, 
                                                                                                                v_approve0,state=False,refresh_callback=refresh_treeview))
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton",command=reject_button_in_pending_GUI.destroy)
    button3.pack(side=RIGHT)
    ## CREATE: LABEL FOR REMARK
    label_remark = ttk.Label(reject_button_in_pending_GUI,text='Remark:',style="label2.TLabel")
    label_remark.place(x=28*scaling_factor,y=45*scaling_factor)
    ## CREATE: REMARK ENTRY
    v_remark0 = StringVar()
    default_text = "***Remark entry***"
    input_field_remark_for_approve_button(reject_button_in_pending_GUI,font=FONT7,scaling_factor=scaling_factor,textvariable=v_remark0,
                            placeholder=default_text,fg='grey',y_position=(45*scaling_factor))
    ## CREATE: APPROVE LABEL AND ENTRY
    v_approve0 = StringVar()
    default_text = "ex.Kritsakon.P"
    E14 = input_field_dropdown(GUI=reject_button_in_pending_GUI,label='Reject by:',options=sectionmgr_list,textvariable=v_approve0,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=True,fg='Grey',
            x_position=-34,frame_width=-90,widget_width=-39)
    E14.place(x=18*scaling_factor,y=110*scaling_factor)

def update_button_for_overview(parent_window, v_loto_no, v_work_title, v_lock_date, v_folder_location, refresh_gui3_callback):
    # Define a refresh function to update the fields in detail_overview_GUI

    update_button_in_overview_GUI,NewLoto_x,NewLoto_y  = create_approve_reject_window('Update',400,270,parent=parent_window)
    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(update_button_in_overview_GUI,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(update_button_in_overview_GUI, text="Update work detail",style="label1.TLabel")
    label1.place(x=int(20*scaling_factor),y=int(13*scaling_factor))
    line1_x1 = int(16*scaling_factor)
    line1_y1 = int(25*scaling_factor)
    line1_x2 = int(NewLoto_x-(17*scaling_factor))
    line1_y2 = int(NewLoto_y-(50*scaling_factor))
    line1.create_rectangle(line1_x1,line1_y1,line1_x2,line1_y2,fill='#dcdad5',width=1,outline='#a9a7a3')
    line1.create_rectangle(line1_x1+scaling_factor,line1_y1+scaling_factor,
                        line1_x2-scaling_factor,line1_y2-scaling_factor,
                        fill='#dcdad5',width=1,outline='#f8f2ea')
    
    ## CREATE: FRAME FOR BUTTON
    frame3 = tk.Frame(update_button_in_overview_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(NewLoto_x-(216*scaling_factor)), y=int(NewLoto_y-(45*scaling_factor)), width=200*scaling_factor, height=40*scaling_factor)
    ## CREATE: BUTTON
    button2 = ttk.Button(frame3, text="CONFIRM", style="Custom2.TButton",command=lambda: confirm_button_update(update_button_in_overview_GUI, v_loto_no, v_work_title, 
                                                                                                                v_lock_date,v_pdf_update,v_override_update, v_remark0, 
                                                                                                                v_update0, v_folder_location=v_folder_location,
                                                                                                                refresh_treeview_callback=refresh_treeview,
                                                                                                                refresh_gui3_callback=refresh_gui3_callback))
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton",command=update_button_in_overview_GUI.destroy)
    button3.pack(side=RIGHT)
    ## CREATE: PDF Entry
    v_pdf_update = StringVar()
    pdf_entry = pdf_new_for_update_button(update_button_in_overview_GUI,'P&ID Markup:',28*scaling_factor,45*scaling_factor,v_pdf_update)
    pdf_entry.place(x=28*scaling_factor,y=45*scaling_factor)
    ## CREATE: OVERRIDE Entry
    v_override_update = StringVar()
    override_entry = pdf_new_for_update_button(update_button_in_overview_GUI,'Override:',28*scaling_factor,80*scaling_factor,v_override_update)
    override_entry.place(x=28*scaling_factor,y=80*scaling_factor)
    ## CREATE: LABEL FOR REMARK
    label_remark = ttk.Label(update_button_in_overview_GUI,text='Remark:',style="label2.TLabel")
    label_remark.place(x=28*scaling_factor,y=115*scaling_factor)
    ## CREATE: REMARK ENTRY
    v_remark0 = StringVar()
    default_text = "***Remark entry***"
    input_field_remark_for_update_button(update_button_in_overview_GUI,font=FONT7,scaling_factor=scaling_factor,textvariable=v_remark0,
                            placeholder=default_text,fg='grey',y_position=(115*scaling_factor))
    ## CREATE: APPROVE LABEL AND ENTRY
    v_update0 = StringVar()
    default_text = "ex.Kritsakon.P"
    E14 = input_field_dropdown(GUI=update_button_in_overview_GUI,label='Update by:',options=lomember_list,textvariable=v_update0,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=True,fg='Grey',
            x_position=-34,frame_width=-70,widget_width=-20)
    E14.place(x=18*scaling_factor,y=180*scaling_factor)

    # After setting up update_button_in_overview_GUI, use wait_window to wait until update_button_in_overview_GUI is closed
    update_button_in_overview_GUI.wait_window()  # This will block the execution until update_button_in_overview_GUI is destroyed
    
    # print("approve_reject_GUI is destroyed")
    # Refresh the data in detail_overview_GUI after closing approve_reject_GUI
    if refresh_gui3_callback:
        refresh_gui3_callback(v_loto_no, v_work_title, v_lock_date)
        # print("detail_overview_GUI is refreshed")

def confirm_button_update(update_button_in_overview_GUI, v_loto_no, v_work_title, v_lock_date, v_pdf_update, 
                        v_override_update, v_remark0, v_update0, v_folder_location,
                        refresh_treeview_callback=None, refresh_gui3_callback=None
                        ):
    # Extract values from the input fields
    remark_value0 = v_remark0.get().strip()
    v_update0 = v_update0.get().strip()
    remark_value = date_str(3) + ' updated by ' + v_update0 + '\n' + remark_value0
    pdf_value = v_pdf_update.get().strip()
    override_value = v_override_update.get().strip()
    
    print('working on the confirm_button_update')
    print(f'v_loto_no: {v_loto_no}')
    print(f'v_work_title: {v_work_title}')
    print(f'v_lock_date: {v_lock_date}')
    print(f'remark_value: {remark_value}')
    print(f'pdf_value: {pdf_value}')
    print(f'override_value: {override_value}')
    
    copy_rename_file_value = copy_rename_file_for_update_widget(pdf_value, override_value, v_folder_location)
    # copy_rename_file_for_update_widget.testprint()

    # Fetch the existing data from the database
    with conn:
        command_fetch = """
        SELECT new_pid_pdf, new_override_list, new_remark
        FROM loto_new
        WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
        """
        c.execute(command_fetch, (v_loto_no, v_work_title, v_lock_date))
        result = c.fetchone()
        # print(f'result: {result}')

        if result:
            # Extract the existing values from the database
            existing_pdf = result[0]  # Existing PDF file path
            existing_override = result[1]  # Existing override list
            existing_remark = result[2]  # Existing remarks
            
            # Update remarks only if remark_value0 contains data
            if remark_value0:
                updated_remark = f"{existing_remark}\n{remark_value}" if existing_remark else remark_value
            else:
                updated_remark = existing_remark
            
            # Update PDF only if pdf_value contains data
            if pdf_value:
                copy_rename_file_value.transfer_pdf()
                updated_pdf = copy_rename_file_value.rename_pdf()

            else:
                updated_pdf = existing_pdf
            
            # Update override only if override_value contains data
            if override_value:
                copy_rename_file_value.transfer_override()
                updated_override = copy_rename_file_value.rename_override()
            else:
                updated_override = existing_override
            
            # Update the record in the database only if there's a change
            command_update = """
            UPDATE loto_new
            SET new_pid_pdf = ?, new_override_list = ?, new_remark = ?
            WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
            """
            c.execute(command_update, (updated_pdf, updated_override, updated_remark, v_loto_no, v_work_title, v_lock_date))
            conn.commit()

        # Optionally, refresh the Treeview and detail_overview_GUI
    if refresh_treeview_callback:
        refresh_treeview_callback()  # Refresh the Treeview to update the data table
    if refresh_gui3_callback:
        refresh_gui3_callback(v_loto_no, v_work_title, v_lock_date)

    # Destroy the GUI after updating
    update_button_in_overview_GUI.destroy()

def completed_button_for_overview(detail_overview_GUI,parent_window, v_loto_no, v_work_title, v_lock_date):
    completed_button_in_overview_GUI,NewLoto_x,NewLoto_y  = create_approve_reject_window('Completed',380,200,parent=parent_window)
    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(completed_button_in_overview_GUI,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(completed_button_in_overview_GUI, text="Completed work detail",style="label1.TLabel")
    label1.place(x=int(20*scaling_factor),y=int(13*scaling_factor))
    line1_x1 = int(16*scaling_factor)
    line1_y1 = int(25*scaling_factor)
    line1_x2 = int(NewLoto_x-(17*scaling_factor))
    line1_y2 = int(NewLoto_y-(50*scaling_factor))
    line1.create_rectangle(line1_x1,line1_y1,line1_x2,line1_y2,fill='#dcdad5',width=1,outline='#a9a7a3')
    line1.create_rectangle(line1_x1+scaling_factor,line1_y1+scaling_factor,
                        line1_x2-scaling_factor,line1_y2-scaling_factor,
                        fill='#dcdad5',width=1,outline='#f8f2ea')
    
    ## CREATE: FRAME FOR BUTTON
    frame3 = tk.Frame(completed_button_in_overview_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(NewLoto_x-(216*scaling_factor)), y=int(NewLoto_y-(45*scaling_factor)), width=200*scaling_factor, height=40*scaling_factor)
    ## CREATE: BUTTON
    button2 = ttk.Button(frame3, text="CONFIRM", style="Custom2.TButton",command=lambda: confirm_button_completed(detail_overview_GUI,completed_button_in_overview_GUI, v_loto_no, v_work_title, 
                                                                                                                v_lock_date, v_remark0,v_completed0,refresh_treeview_callback=refresh_treeview))
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton",command=completed_button_in_overview_GUI.destroy)
    button3.pack(side=RIGHT)
    ## CREATE: LABEL FOR REMARK
    label_remark = ttk.Label(completed_button_in_overview_GUI,text='Remark:',style="label2.TLabel")
    label_remark.place(x=28*scaling_factor,y=45*scaling_factor)
    ## CREATE: REMARK ENTRY
    v_remark0 = StringVar()
    default_text = "***Remark entry***"
    input_field_remark_for_approve_button(completed_button_in_overview_GUI,font=FONT7,scaling_factor=scaling_factor,textvariable=v_remark0,
                            placeholder=default_text,fg='grey',y_position=(45*scaling_factor))
    ## CREATE: APPROVE LABEL AND ENTRY
    v_completed0 = StringVar()
    default_text = "ex.Kritsakon.P"
    E14 = input_field_dropdown(GUI=completed_button_in_overview_GUI,label='Completed by:',options=lomember_list,textvariable=v_completed0,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=True,fg='Grey',
            x_position=-33,frame_width=-88,widget_width=-39)
    E14.place(x=18*scaling_factor,y=110*scaling_factor)

def confirm_button_completed(detail_overview_GUI,completed_button_in_overview_GUI, v_loto_no, v_work_title, 
                            v_lock_date, v_remark0,v_completed0,refresh_treeview_callback=None):
    # Extract values from the input fields
    remark_value0 = v_remark0.get().strip()
    v_completed0 = v_completed0.get().strip()
    remark_value = date_str(3) + ' completed by ' + v_completed0 + '\n' + remark_value0

    # Fetch the existing data from the database
    with conn:
        command_fetch = """
        SELECT new_remark
        FROM loto_new
        WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
        """
        c.execute(command_fetch, (v_loto_no, v_work_title, v_lock_date))
        result = c.fetchone()
    
        if result:
            # Extract the existing values from the database
            existing_remark = result[0]

            if remark_value0:
                updated_remark = f"{existing_remark}\n{remark_value}" if existing_remark else remark_value
            else:
                updated_remark = existing_remark
            
            # Update the record in the database only if there's a change
            command_update = """
            UPDATE loto_new
            SET new_remark = ?, status = ?
            WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
            """
            c.execute(command_update, (updated_remark,"Completed", v_loto_no, v_work_title, v_lock_date))
            conn.commit()

            # Delete the record from loto_overview table
            command_delete = """
            DELETE FROM loto_overview
            WHERE loto_no = ? AND work_title = ? AND lock_date = ?
            """
            c.execute(command_delete, (v_loto_no, v_work_title, v_lock_date))
            conn.commit()
    transfer_data_completed()
    # Calculate the total lock days
    lock_date_obj = datetime.strptime(v_lock_date, '%d/%m/%y')
    completed_date_obj = datetime.strptime(date_str(1), '%d/%m/%y')
    # Calculate the difference in days
    total_days = (completed_date_obj - lock_date_obj).days
    print(f'Total lock days: {total_days}')

    # Stamp completed date to loto_completed table
    with conn:
        command_stamp = """
        UPDATE loto_completed
        SET completed_date = ?, total_lock_days = ?
        WHERE loto_no = ? AND work_title = ? AND lock_date = ?
        """
        c.execute(command_stamp, (date_str(1), total_days, v_loto_no, v_work_title, v_lock_date))
        conn.commit()


    if refresh_treeview_callback:
        refresh_treeview_callback()  # Refresh the Treeview to update the data table
    
    # Destroy the GUI after updating
    completed_button_in_overview_GUI.destroy()
    detail_overview_GUI.destroy()

def postpone_button_for_overview(detail_overview_GUI, v_loto_no, v_work_title, v_lock_date):
    postpone_button_in_overview_GUI,NewLoto_x,NewLoto_y  = create_approve_reject_window('Postpone',380,200,parent=detail_overview_GUI)
    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(postpone_button_in_overview_GUI,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(postpone_button_in_overview_GUI, text="Postpone work detail",style="label1.TLabel")
    label1.place(x=int(20*scaling_factor),y=int(13*scaling_factor))
    line1_x1 = int(16*scaling_factor)
    line1_y1 = int(25*scaling_factor)
    line1_x2 = int(NewLoto_x-(17*scaling_factor))
    line1_y2 = int(NewLoto_y-(50*scaling_factor))
    line1.create_rectangle(line1_x1,line1_y1,line1_x2,line1_y2,fill='#dcdad5',width=1,outline='#a9a7a3')
    line1.create_rectangle(line1_x1+scaling_factor,line1_y1+scaling_factor,
                        line1_x2-scaling_factor,line1_y2-scaling_factor,
                        fill='#dcdad5',width=1,outline='#f8f2ea')
    ## CREATE: FRAME FOR BUTTON
    frame3 = tk.Frame(postpone_button_in_overview_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(NewLoto_x-(216*scaling_factor)), y=int(NewLoto_y-(45*scaling_factor)), width=int(200*scaling_factor), height=int(40*scaling_factor))
    ## CREATE: BUTTON
    button2 = ttk.Button(frame3, text="CONFIRM", style="Custom2.TButton",command=lambda: confirm_button_postpone(detail_overview_GUI,postpone_button_in_overview_GUI, v_loto_no, v_work_title, 
                                                                                                                v_lock_date, v_remark0,v_postpone0,refresh_treeview_callback=refresh_treeview))
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton",command=postpone_button_in_overview_GUI.destroy)
    button3.pack(side=RIGHT)
    ## CREATE: LABEL FOR REMARK
    label_remark = ttk.Label(postpone_button_in_overview_GUI,text='Remark:',style="label2.TLabel")
    label_remark.place(x=28*scaling_factor,y=45*scaling_factor)
    ## CREATE: REMARK ENTRY
    v_remark0 = StringVar()
    default_text = "***Remark entry***"
    input_field_remark_for_approve_button(postpone_button_in_overview_GUI,font=FONT7,scaling_factor=scaling_factor,textvariable=v_remark0,
                            placeholder=default_text,fg='grey',y_position=(45*scaling_factor))
    ## CREATE: APPROVE LABEL AND ENTRY
    v_postpone0 = StringVar()
    default_text = "ex.Kritsakon.P"
    E14 = input_field_dropdown(GUI=postpone_button_in_overview_GUI,label='Postpone by:',options=lomember_list,textvariable=v_postpone0,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=True,fg='Grey',
            x_position=-34,frame_width=-90,widget_width=-39)
    E14.place(x=18*scaling_factor,y=110*scaling_factor)

def confirm_button_postpone(detail_overview_GUI,postpone_button_in_overview_GUI, v_loto_no, v_work_title, 
                            v_lock_date, v_remark0,v_postpone0,refresh_treeview_callback=None):
    # Extract values from the input fields
    remark_value0 = v_remark0.get().strip()
    v_postpone0 = v_postpone0.get().strip()
    remark_value = date_str(3) + ' postpone by ' + v_postpone0 + '\n' + remark_value0

    # Fetch the existing data from the database
    with conn:
        command_fetch = """
        SELECT new_remark
        FROM loto_new
        WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
        """
        c.execute(command_fetch, (v_loto_no, v_work_title, v_lock_date))
        result = c.fetchone()
    
        if result:
            # Extract the existing values from the database
            existing_remark = result[0]

            if remark_value0:
                updated_remark = f"{existing_remark}\n{remark_value}" if existing_remark else remark_value
            else:
                updated_remark = existing_remark
            
            # Update the record in the database only if there's a change
            command_update = """
            UPDATE loto_new
            SET new_remark = ?, status = ?
            WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
            """
            c.execute(command_update, (updated_remark,"Postpone", v_loto_no, v_work_title, v_lock_date))
            conn.commit()

            # Delete the record from loto_overview table
            command_delete = """
            DELETE FROM loto_overview
            WHERE loto_no = ? AND work_title = ? AND lock_date = ?
            """
            c.execute(command_delete, (v_loto_no, v_work_title, v_lock_date))
            conn.commit()

    # transfer_data_completed()
    # Calculate the total lock days
    lock_date_obj = datetime.strptime(v_lock_date, '%d/%m/%y')
    completed_date_obj = datetime.strptime(date_str(1), '%d/%m/%y')
    # Calculate the difference in days
    total_days = (completed_date_obj - lock_date_obj).days
    print(f'Total lock days: {total_days}')

    # Stamp completed date to loto_completed table
    with conn:
        command_stamp = """
        UPDATE loto_completed
        SET completed_date = ?, total_lock_days = ?
        WHERE loto_no = ? AND work_title = ? AND lock_date = ?
        """
        c.execute(command_stamp, (date_str(1), total_days, v_loto_no, v_work_title, v_lock_date))
        conn.commit()


    if refresh_treeview_callback:
        refresh_treeview_callback()  # Refresh the Treeview to update the data table
    
    update_table_pending()
    # Destroy the GUI after updating
    postpone_button_in_overview_GUI.destroy()
    detail_overview_GUI.destroy()

def capture_table_to_pdf(treeview, file_name):
    # Set up the PDF document
    pdf = SimpleDocTemplate(file_name, pagesize=A4)
    elements = []
    
    # Table header
    data = [treeview.cget("columns")]
    
    # Add all rows of the Treeview to the data list
    for child in treeview.get_children():
        row = [treeview.item(child, "values")[i] for i in range(len(data[0]))]
        data.append(row)
    
    # Calculate the total number of rows (excluding the header)
    total_rows = len(treeview.get_children())

    # Create the table in the PDF
    table = Table(data)
    
    # Define table style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)
    
    # Get the current date
    current_date = datetime.now().strftime("%d/%m/%Y")

    # Add the table to elements and build the PDF
    elements.append(table)
    # Add total rows count text
    styles = getSampleStyleSheet()
    total_rows_text = Paragraph(
        f"Total lock box is: {total_rows} <font size=8 color=grey>    (as of: {current_date})</font>", styles['Normal']
    )
    elements.append(total_rows_text)
    
    # Build the PDF
    pdf.build(elements)
    
    print(f"PDF saved successfully as {file_name}")

def save_table_as_pdf(treeview):
    # Define the default directory and file name
    default_directory = resource_path("L:/4.4LO.T1/06-Operational_and_Record/6.56 LOTO/LOTOList")  # Replace with your desired path
    default_file_name = f"{datetime.now().strftime('%Y_%m_%d')}_LOTO_WorkList.pdf"
    
    # Construct the full path for the file
    file_path = os.path.join(default_directory, default_file_name)
    
    # Ensure the directory exists (optional)
    os.makedirs(default_directory, exist_ok=True)
    
    # Call the function to capture the table and save it as a PDF
    capture_table_to_pdf(treeview, file_path)
    
    # Open the PDF file after saving
    webbrowser.open(file_path)

## CLASS DROPDOWN
class input_field_dropdown(tk.Frame):
    instances = []  # Class variable to keep track of all instances
    def __init__(self, GUI, label, options, default_text, scaling_factor,textvariable,toggle_var=True,fg='grey',
                x_position=0,frame_width=0,widget_width=0):
        super().__init__(GUI, width=int((frame_width+430) * scaling_factor), height=int(30 * scaling_factor), background="#dcdad5")
        self.textvariable = textvariable
        self.original_values = sorted(options)  # Store a sorted copy of all options for the combobox
        self.default_text = default_text
        self.dropdown_id = None
        self.options = options
        self.label = label
        self.placeholder_active = True
        self.textvariable.trace("w", self.update_text_widget)
        self.fg = fg
        self.toggle_var = toggle_var
        self.x_position = x_position
        self.widget_width = widget_width

        # Label for the combobox
        self.L = ttk.Label(self, text=self.label, style="label2.TLabel")
        self.L.place(x=8 * scaling_factor, y=2 * scaling_factor)

        # Setup Text as Combobox
        self.text = tk.Text(self, font=FONT7, foreground=self.fg, highlightbackground="grey",
                                highlightcolor="grey", highlightthickness=1,
                                borderwidth=2, relief="flat", wrap="none")
        self.text.insert('1.0', default_text)
        self.text.place(x=((self.x_position+126) * scaling_factor), y=(1.1 * scaling_factor), width=int((self.widget_width+283) * scaling_factor), height=int(22 * scaling_factor))
        self.text.bind("<Button-1>",self.toplevel_popup)
        self.text.bind("<Tab>", focus_next_widget)  # Tab to next widget
        input_field_dropdown.instances.append(self)
        self.switch_editable()

    def dd_toplevel(self,event=None):
        self.dd_top = tk.Toplevel(self,background='#dcdad5')
        dd_top_h = int(150*scaling_factor)
        dd_top_w = int(250*scaling_factor)
        dd_size = center_windows(dd_top_w,dd_top_h)
        self.dd_top.title('Selection')
        self.dd_top.geometry(dd_size)
        self.dd_top.resizable(False,False)
        
        ### LABEL 
        l1 = ttk.Label(self.dd_top,text=self.label,style="label2.TLabel")
        l1.place(x=int(2*scaling_factor),y=int(10*scaling_factor))
        
        ### INPUT (Text)
        self.input1 = tk.Text(self.dd_top, font=FONT7, foreground='grey', highlightbackground="grey",
                                highlightcolor="grey", highlightthickness=1,
                                borderwidth=2, relief="flat", wrap="none")
        self.input1.insert('1.0', self.default_text)
        self.input1.place(x=int(2*scaling_factor),y=int(30*scaling_factor),width=dd_top_w-int(29*scaling_factor), height=int(22 * scaling_factor))
        self.dd_top.after(10, self.input1.focus_set)  # This delays the focus to input1
        self.input1.bind("<KeyRelease>", self.on_key_release)
        self.input1.bind("<FocusIn>", self.on_focus_in)
        self.input1.bind("<FocusOut>", self.on_focus_out)
        self.input1.bind("<KeyPress-Return>",lambda e: "break")

        ### DROP DOWN (Listbox)
        self.dropdown_list = tk.Listbox(self.dd_top,font=FONT7)
        self.dropdown_list.bind("<<ListboxSelect>>", self.on_select)
        self.update_listbox(self.original_values)

        ### DROP DOWN (Icon)
        self.dd_icon = create_resized_image('DD.png',int(14*scaling_factor),int(15*scaling_factor))
        self.dd_button = tk.Button(self.dd_top,image=self.dd_icon,command=self.show_dropdown)
        self.dd_button.config(width=int(16*scaling_factor),height=int(19 * scaling_factor))
        self.dd_button.place(x=int(225*scaling_factor),y=int(30*scaling_factor))

        ### BUTTON (CONFIRM & CLOSE)
        ## CREATE: FRAME for Button location
        self.dd_frame = tk.Frame(self.dd_top, background="#dcdad5", borderwidth=1, relief="flat")
        self.dd_frame.place(x=int(81*scaling_factor), y=int(112*scaling_factor),
                        width=int(163*scaling_factor), height=int(40*scaling_factor))
        # self.dd_button1 = ttk.Button(self.dd_frame, text="CONFIRM", style="Custom3.TButton",
        #                              command=self.fetch_dd_top_input)
        # self.dd_button1.pack(side=LEFT)
        self.dd_button2 = ttk.Button(self.dd_frame, text="CLOSE (X)", style="Custom3.TButton",
                                    command=self.close_dd_top)
        self.dd_button2.pack(side=RIGHT)
    
    def on_key_release(self, event):
        """Filter the Listbox based on the Text input."""
        search_term = self.input1.get('1.0', 'end-1c').strip().lower()
        if not search_term:
            self.dropdown_list.delete(0, tk.END)
            for option in self.options:
                self.dropdown_list.insert(tk.END, option)
        else:
            filtered_options = [item for item in self.original_values if search_term in item.lower()]
            self.update_listbox(filtered_options)
        self.show_dropdown()

    def update_listbox(self, options):
        """Updates the Listbox with the given options."""
        self.dropdown_list.delete(0, tk.END)
        for option in options:
            self.dropdown_list.insert(tk.END, option)

    def on_select(self, event):
        """Handle selection from the Listbox."""
        if self.dropdown_list.curselection():
            selected_option = self.dropdown_list.get(self.dropdown_list.curselection())
            self.input1.delete('1.0', 'end')
            self.input1.insert('1.0', selected_option)
            self.hide_dropdown()  # Hide the dropdown after an item is selected
            self.fetch_dd_top_input()
            self.dd_top.destroy()

    def on_focus_in(self, event):
        """Clear default text when gaining focus."""
        if self.input1.get('1.0', 'end-1c') == self.default_text:
            self.input1.delete('1.0', 'end')
            self.input1.config(foreground='black')

    def on_focus_out(self, event):
        """Reinsert default text if empty."""
        if not self.input1.get('1.0', 'end-1c').strip():
            self.input1.insert('1.0', self.default_text)
            self.input1.config(foreground='grey')

    def show_dropdown(self,event=None):
        self.dropdown_list.place(in_=self.input1, x=0, rely=1, relwidth=1.0, anchor="nw",
                                height=int(65*scaling_factor))
        self.dropdown_list.lift()
        # # Show dropdown for 2 seconds
        # if self.dropdown_id: # Cancel any old events
        #     self.dropdown_list.after_cancel(self.dropdown_id)
        # self.dropdown_id = self.dropdown_list.after(2000, self.hide_dropdown)

    def hide_dropdown(self):
        self.dropdown_list.place_forget()

    def fetch_dd_top_input(self):
        dd_input1 = (self.input1.get('1.0', 'end-1c'))
        self.text.delete('1.0','end')
        self.text.insert('1.0',dd_input1)
        self.text.config(foreground='Black')
        self.sync_text()
        self.close_dd_top()
    
    def close_dd_top(self):
        self.dd_top.destroy()
    
    def insert_placeholder(self):
        """ Insert placeholder text into the Text widget. """
        if self.placeholder_active:
            self.text.insert('end', self.default_text)
            self.text.config(foreground='grey')
        
    def update_text_widget(self, *args):
        current_text = self.textvariable.get()  # Get the current value from the textvariable
        if self.text.get("1.0", "end-1c") != current_text:  # Compare it to what's currently in the Text widget
            self.text.delete("1.0", "end")  # If different, clear the Text widget
            self.text.insert("end", current_text)  # Insert the new text from the textvariable

    def sync_text(self, event=None):
        sync_text = self.text.get('1.0','end-1c').strip()
        self.textvariable.set(sync_text)
    
    def switch_editable(self):
        if self.toggle_var == True:
            self.text.config(state='normal')
        else:
            self.text.config(state='disable')

    def toplevel_popup(self, event=None):
        if self.toggle_var == True:
            self.dd_toplevel()

## CLASS DROPDOWN for at Line break
class input_field_dropdown_linebreak(tk.Frame):
    instances = []  # Class variable to keep track of all instances
    def __init__(self, GUI, label, options, default_text, scaling_factor,textvariable,toggle_var=True,fg='grey',
                x_position=0,frame_width=0,widget_width=0):
        super().__init__(GUI, width=int((frame_width+430) * scaling_factor), height=int(30 * scaling_factor), background="#dcdad5")
        self.textvariable = textvariable
        self.original_values = sorted(options)  # Store a sorted copy of all options for the combobox
        self.default_text = default_text
        self.file_path = None
        self.dropdown_id = None
        self.options = options
        self.label = label
        self.placeholder_active = True
        self.textvariable.trace("w", self.update_text_widget)
        self.fg = fg
        self.toggle_var = toggle_var
        self.x_position = x_position
        self.widget_width = widget_width
        self.GUI = GUI

        # Label for the combobox
        self.L = ttk.Label(self, text=self.label, style="label2.TLabel")
        self.L.place(x=10 * scaling_factor, y=2 * scaling_factor)

        # Setup Text as Combobox
        self.text = tk.Text(self, font=FONT7, foreground=self.fg, highlightbackground="grey",
                                highlightcolor="grey", highlightthickness=1,
                                borderwidth=2, relief="flat", wrap="none")
        self.text.insert('1.0', default_text)
        self.text.place(x=((self.x_position+126) * scaling_factor), y=(1.1 * scaling_factor), width=int((self.widget_width+283) * scaling_factor), height=int(22 * scaling_factor))
        
        self.pdf_icon = create_resized_image('pdf2.png',int(11*scaling_factor),int(11*scaling_factor))
        self.pdf_but = tk.Button(self,image=self.pdf_icon,command=self.attach_pdf,
                                bg="#dcdad5",             # Background color
                                activebackground="#e0e0e0",# Background color when clicked or hovered
                                borderwidth=0,            # Width of the button's border
                                relief="raised",          # Type of border effect (flat, raised, sunken, groove, ridge)
                                highlightthickness=2,      # Thickness of highlight border when focused
                                highlightbackground="#cccccc",  # Color of the highlight border
                                highlightcolor="#ff0000",  # Color of the highlight border when the button is focused
                                )
        self.pdf_but.config(width=int(11*scaling_factor),height=int(11*scaling_factor))
        self.pdf_but.place(x=int(92*scaling_factor),y=int(4*scaling_factor))
        
        self.check_icon = create_resized_image('check.png',int(11*scaling_factor),int(11*scaling_factor))
        self.check_but = tk.Button(self,image=self.check_icon,command=self.attach_pdf,
                                bg="#dcdad5",             # Background color
                                activebackground="#e0e0e0",# Background color when clicked or hovered
                                borderwidth=0,            # Width of the button's border
                                relief="raised",          # Type of border effect (flat, raised, sunken, groove, ridge)
                                highlightthickness=2,      # Thickness of highlight border when focused
                                highlightbackground="#cccccc",  # Color of the highlight border
                                highlightcolor="#ff0000",  # Color of the highlight border when the button is focused
                                )
        self.check_but.config(width=int(11*scaling_factor),height=int(11*scaling_factor))
        
        # Bind function
        self.text.bind("<Button-1>",self.toplevel_popup)
        self.text.bind("<Tab>", focus_next_widget)  # Tab to next widget
        input_field_dropdown_linebreak.instances.append(self)
        self.switch_editable()

    def attach_pdf(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if self.file_path:
            self.check_but.place(x=int(107*scaling_factor),y=int(4*scaling_factor))
            self.GUI.focus_set()

    def dd_toplevel(self,event=None):
        self.dd_top = tk.Toplevel(self,background='#dcdad5')
        dd_top_h = int(150*scaling_factor)
        dd_top_w = int(250*scaling_factor)
        dd_size = center_windows(dd_top_w,dd_top_h)
        self.dd_top.title('Selection')
        self.dd_top.geometry(dd_size)
        self.dd_top.resizable(False,False)
        
        ### LABEL 
        l1 = ttk.Label(self.dd_top,text=self.label,style="label2.TLabel")
        l1.place(x=int(2*scaling_factor),y=int(10*scaling_factor))
        
        ### INPUT (Text)
        self.input1 = tk.Text(self.dd_top, font=FONT7, foreground='grey', highlightbackground="grey",
                                highlightcolor="grey", highlightthickness=1,
                                borderwidth=2, relief="flat", wrap="none")
        self.input1.insert('1.0', self.default_text)
        self.input1.place(x=int(2*scaling_factor),y=int(30*scaling_factor),width=dd_top_w-int(29*scaling_factor), height=int(22 * scaling_factor))
        self.dd_top.after(10, self.input1.focus_set)  # This delays the focus to input1
        self.input1.bind("<KeyRelease>", self.on_key_release)
        self.input1.bind("<FocusIn>", self.on_focus_in)
        self.input1.bind("<FocusOut>", self.on_focus_out)
        self.input1.bind("<KeyPress-Return>",lambda e: "break")

        ### DROP DOWN (Listbox)
        self.dropdown_list = tk.Listbox(self.dd_top,font=FONT7)
        self.dropdown_list.bind("<<ListboxSelect>>", self.on_select)
        self.update_listbox(self.original_values)

        ### DROP DOWN (Icon)
        self.dd_icon = create_resized_image('DD.png',int(14*scaling_factor),int(15*scaling_factor))
        self.dd_button = tk.Button(self.dd_top,image=self.dd_icon,command=self.show_dropdown)
        self.dd_button.config(width=int(16*scaling_factor),height=int(19 * scaling_factor))
        self.dd_button.place(x=int(225*scaling_factor),y=int(30*scaling_factor))

        ### BUTTON (CONFIRM & CLOSE)
        ## CREATE: FRAME for Button location
        self.dd_frame = tk.Frame(self.dd_top, background="#dcdad5", borderwidth=1, relief="flat")
        self.dd_frame.place(x=int(81*scaling_factor), y=int(112*scaling_factor),
                        width=int(163*scaling_factor), height=int(40*scaling_factor))
        # self.dd_button1 = ttk.Button(self.dd_frame, text="CONFIRM", style="Custom3.TButton",
        #                              command=self.fetch_dd_top_input)
        # self.dd_button1.pack(side=LEFT)
        self.dd_button2 = ttk.Button(self.dd_frame, text="CLOSE (X)", style="Custom3.TButton",
                                    command=self.close_dd_top)
        self.dd_button2.pack(side=RIGHT)

    def on_key_release(self, event):
        """Filter the Listbox based on the Text input."""
        search_term = self.input1.get('1.0', 'end-1c').strip().lower()
        if not search_term:
            self.dropdown_list.delete(0, tk.END)
            for option in self.options:
                self.dropdown_list.insert(tk.END, option)
        else:
            filtered_options = [item for item in self.original_values if search_term in item.lower()]
            self.update_listbox(filtered_options)
        self.show_dropdown()

    def update_listbox(self, options):
        """Updates the Listbox with the given options."""
        self.dropdown_list.delete(0, tk.END)
        for option in options:
            self.dropdown_list.insert(tk.END, option)

    def on_select(self, event):
        """Handle selection from the Listbox."""
        if self.dropdown_list.curselection():
            selected_option = self.dropdown_list.get(self.dropdown_list.curselection())
            self.input1.delete('1.0', 'end')
            self.input1.insert('1.0', selected_option)
            self.hide_dropdown()  # Hide the dropdown after an item is selected
            self.fetch_dd_top_input()
            self.dd_top.destroy()

    def on_focus_in(self, event):
        """Clear default text when gaining focus."""
        if self.input1.get('1.0', 'end-1c') == self.default_text:
            self.input1.delete('1.0', 'end')
            self.input1.config(foreground='black')

    def on_focus_out(self, event):
        """Reinsert default text if empty."""
        if not self.input1.get('1.0', 'end-1c').strip():
            self.input1.insert('1.0', self.default_text)
            self.input1.config(foreground='grey')

    def show_dropdown(self,event=None):
        self.dropdown_list.place(in_=self.input1, x=0, rely=1, relwidth=1.0, anchor="nw",
                                height=int(65*scaling_factor))
        self.dropdown_list.lift()
        # Show dropdown for 2 seconds
        # if self.dropdown_id: # Cancel any old events
        #     self.dropdown_list.after_cancel(self.dropdown_id)
        # self.dropdown_id = self.dropdown_list.after(2000, self.hide_dropdown)

    def hide_dropdown(self):
        self.dropdown_list.place_forget()

    def fetch_dd_top_input(self):
        dd_input1 = (self.input1.get('1.0', 'end-1c'))
        self.text.delete('1.0','end')
        self.text.insert('1.0',dd_input1)
        self.text.config(foreground='Black')
        self.sync_text()
        self.close_dd_top()
    
    def close_dd_top(self):
        self.dd_top.destroy()
    
    def insert_placeholder(self):
        """ Insert placeholder text into the Text widget. """
        if self.placeholder_active:
            self.text.insert('end', self.default_text)
            self.text.config(foreground='grey')
        
    def update_text_widget(self, *args):
        current_text = self.textvariable.get()  # Get the current value from the textvariable
        if self.text.get("1.0", "end-1c") != current_text:  # Compare it to what's currently in the Text widget
            self.text.delete("1.0", "end")  # If different, clear the Text widget
            self.text.insert("end", current_text)  # Insert the new text from the textvariable

    def sync_text(self, event=None):
        sync_text = self.text.get('1.0','end-1c').strip()
        self.textvariable.set(sync_text)
    
    def switch_editable(self):
        if self.toggle_var == True:
            self.text.config(state='normal')
        else:
            self.text.config(state='disable')

    def toplevel_popup(self, event=None):
        if self.toggle_var == True:
            self.dd_toplevel()

    def get_file_path(self):
        return self.file_path

## CLASS FULL LENGHT
class input_field_title(tk.Frame):
    instances = []
    def __init__(self,GUI,label,textvariable,placeholder,toggle_var = True,fg='grey'):
        super().__init__(GUI,width=int(430*scaling_factor),height=int(30*scaling_factor), background="#dcdad5")
        self.L = ttk.Label(self,text=label,style="label2.TLabel")
        self.L.place(x=8*scaling_factor,y=2*scaling_factor)
        self.textvariable = textvariable
        self.textvariable.trace("w", self.update_text_widget)
        self.toggle_var = toggle_var
        self.fg = fg
        self.E1 = tk.Text(self, height=2, wrap="none", font=FONT7, 
                        borderwidth=1, relief="flat", highlightthickness=1, 
                        highlightbackground="grey", highlightcolor="grey")
        self.E1.place(x=126 * scaling_factor, y=int(2*scaling_factor), width=int(283*scaling_factor), height=int(23*scaling_factor))

        # Binding to handle input and focus
        self.E1.bind("<Return>", lambda e: "break")  # Ignore Enter key to prevent new lines
        self.E1.bind("<Tab>", focus_next_widget)  # Tab to next widget
        self.E1.bind("<FocusIn>", on_focus_in)
        self.E1.bind("<FocusOut>", on_focus_out)
        self.E1.bind("<KeyRelease>", self.on_key_release)
        self.placeholder = placeholder
        self.placeholder_active = True
        self.insert_placeholder()
        input_field_title.instances.append(self)
        self.switch_editable()

        self.E1.bind('<FocusIn>', self.on_entry_click)
        self.E1.bind('<FocusOut>', self.on_focus_out)

    def update_text_widget(self, *args):
        current_text = self.textvariable.get()  # Get the current value from the textvariable
        if self.E1.get("1.0", "end-1c") != current_text:  # Compare it to what's currently in the Text widget
            self.E1.delete("1.0", "end")  # If different, clear the Text widget
            self.E1.insert("end", current_text)  # Insert the new text from the textvariable

    # Function: Fetch data from get() to textvariable by set()
    def on_key_release(self, event):
        self.textvariable.set(self.E1.get("1.0", "end-1c"))

    def insert_placeholder(self):
        """ Insert placeholder text into the Text widget. """
        if self.placeholder_active:
            self.E1.insert('end', self.placeholder)
            self.E1.config(foreground=self.fg)

    def on_entry_click(self, event):
        """ Clear placeholder on focus. """
        if self.toggle_var == True:
            if self.E1.get('1.0', 'end-1c').strip() == self.placeholder:
                self.E1.delete('1.0', 'end')
                self.E1.config(foreground='black')
        else:
            pass

    def on_focus_out(self, event):
        text_content = self.E1.get('1.0', 'end-1c').strip()
        if not text_content:
            self.placeholder_active = True
            self.insert_placeholder()
        else:
            self.placeholder_active = False

    def switch_editable(self):
        if self.toggle_var == True:
            self.E1.config(state='normal')
        else:
            self.E1.config(state='disable')

## CLASS FULL LENGHT with folder
class input_field_title_for_show(tk.Frame):
    instances = []
    def __init__(self,GUI,label,textvariable,placeholder,open_folder,toggle_var = True,fg='grey'):
        super().__init__(GUI,width=int(430*scaling_factor),height=int(30*scaling_factor), background="#dcdad5")
        self.L = ttk.Label(self,text=label,style="label2.TLabel")
        self.L.place(x=8*scaling_factor,y=2*scaling_factor)
        self.textvariable = textvariable
        self.textvariable.trace("w", self.update_text_widget)
        self.open_folder = open_folder
        # print(f'open_folder in init is {self.open_folder}')
        self.toggle_var = toggle_var
        self.fg = fg
        self.E1 = tk.Text(self, height=2, wrap="none", font=FONT7, 
                        borderwidth=1, relief="flat", highlightthickness=1, 
                        highlightbackground="grey", highlightcolor="grey")
        self.E1.place(x=126 * scaling_factor, y=int(2*scaling_factor), width=int(283*scaling_factor), height=int(23*scaling_factor))

        self.pdf_icon = create_resized_image('folder.png',int(11*scaling_factor),int(11*scaling_factor))
        self.pdf_but = tk.Button(self,image=self.pdf_icon,command=self.open_folder1,
                                bg="#dcdad5",             # Background color
                                activebackground="#e0e0e0",# Background color when clicked or hovered
                                borderwidth=0,            # Width of the button's border
                                relief="raised",          # Type of border effect (flat, raised, sunken, groove, ridge)
                                highlightthickness=2,      # Thickness of highlight border when focused
                                highlightbackground="#cccccc",  # Color of the highlight border
                                highlightcolor="#ff0000",  # Color of the highlight border when the button is focused
                                )
        self.pdf_but.config(width=int(11*scaling_factor),height=int(11*scaling_factor))
        self.pdf_but.place(x=int(75*scaling_factor),y=int(5*scaling_factor))

        # Binding to handle input and focus
        self.E1.bind("<Return>", lambda e: "break")  # Ignore Enter key to prevent new lines
        self.E1.bind("<Tab>", focus_next_widget)  # Tab to next widget
        self.E1.bind("<FocusIn>", on_focus_in)
        self.E1.bind("<FocusOut>", on_focus_out)
        self.E1.bind("<KeyRelease>", self.on_key_release)
        self.placeholder = placeholder
        self.placeholder_active = True
        self.insert_placeholder()
        input_field_title_for_show.instances.append(self)
        self.switch_editable()

        self.E1.bind('<FocusIn>', self.on_entry_click)
        self.E1.bind('<FocusOut>', self.on_focus_out)
        
    def open_folder1(self):
        if os.path.isdir(self.open_folder):
            folder_location = self.open_folder
        else:
            folder_location = os.path.dirname(self.open_folder)
        # print(f'folder location in class "input_field_title_for_show" is {folder_location}')
        if os.path.isdir(folder_location):
            subprocess.Popen(f'explorer {os.path.realpath(folder_location)}')

    def update_text_widget(self, *args):
        current_text = self.textvariable.get()  # Get the current value from the textvariable
        if self.E1.get("1.0", "end-1c") != current_text:  # Compare it to what's currently in the Text widget
            self.E1.delete("1.0", "end")  # If different, clear the Text widget
            self.E1.insert("end", current_text)  # Insert the new text from the textvariable

    # Function: Fetch data from get() to textvariable by set()
    def on_key_release(self, event):
        self.textvariable.set(self.E1.get("1.0", "end-1c"))

    def insert_placeholder(self):
        """ Insert placeholder text into the Text widget. """
        if self.placeholder_active:
            self.E1.insert('end', self.placeholder)
            self.E1.config(foreground=self.fg)

    def on_entry_click(self, event):
        """ Clear placeholder on focus. """
        if self.toggle_var == True:
            if self.E1.get('1.0', 'end-1c').strip() == self.placeholder:
                self.E1.delete('1.0', 'end')
                self.E1.config(foreground='black')
        else:
            pass

    def on_focus_out(self, event):
        text_content = self.E1.get('1.0', 'end-1c').strip()
        if not text_content:
            self.placeholder_active = True
            self.insert_placeholder()
        else:
            self.placeholder_active = False

    def switch_editable(self):
        if self.toggle_var == True:
            self.E1.config(state='normal')
        else:
            self.E1.config(state='disable')

## CLASS FOR NUMERIC
class input_field_numeric(tk.Frame):
    instances = []
    def __init__(self, GUI, label, textvariable, default_text,toggle_var = True,fg='grey'):
        super().__init__(GUI, width=int(430 * scaling_factor), height=int(166 * scaling_factor), background="#dcdad5")
        self.pack_propagate(False)
        self.textvariable = textvariable
        self.toggle_var = toggle_var
        self.fg = fg

        self.L = ttk.Label(self, text=label, style="label2.TLabel")
        self.L.place(x=8 * scaling_factor, y=2 * scaling_factor)

        # Setting up the Text widget to behave like a single-line entry
        self.E1 = tk.Text(self, height=1, wrap='none', font=FONT7,
                        borderwidth=2, relief='flat', highlightthickness=1,
                        highlightbackground='grey', highlightcolor='grey', undo=True)
        self.E1.place(x=126 * scaling_factor, y=0, width=int(283*scaling_factor), height=int(23*scaling_factor))

        self.default_text = default_text
        self.placeholder_active = True
        self.insert_placeholder()
        input_field_numeric.instances.append(self)
        self.switch_editable()

        self.E1.bind('<FocusIn>', self.on_entry_click)
        self.E1.bind('<FocusOut>', self.on_focus_out)
        self.E1.bind('<KeyPress>', self.validate_input)
        self.E1.bind("<Tab>", focus_next_widget)  # Tab to next widget

    def insert_placeholder(self):
        """ Insert placeholder text into the Text widget. """
        if self.placeholder_active and not self.E1.get('1.0', 'end-1c').strip():
            self.E1.insert('end', self.default_text)
            self.E1.config(foreground=self.fg)

    def validate_input(self, event):
        content = event.widget.get("1.0", "end-1c")
        if event.char.isdigit() or event.keysym in ('BackSpace', 'Left', 'Right', 'Delete'):
            if self.placeholder_active:
                self.E1.delete('1.0', 'end')
                self.E1.config(foreground='black')
                self.placeholder_active = False
            return True
        return 'break'

    def on_entry_click(self, event):
        if self.toggle_var == True:
            if self.E1.get('1.0', 'end-1c').strip() == self.default_text:
                self.E1.delete('1.0', 'end')
                self.E1.config(foreground='black')
        else:
            pass

    def on_focus_out(self, event):
        text_content = self.E1.get('1.0', 'end-1c').strip()
        if not text_content:
            self.placeholder_active = True
            self.insert_placeholder()
        else:
            self.placeholder_active = False
            self.textvariable.set(text_content)

    def switch_editable(self):
        if self.toggle_var == True:
            self.E1.config(state='normal')
        else:
            self.E1.config(state='disable')

## CLASS FOR NUMERIC AND DATE
class input_field_date(tk.Frame):
    instances = []
    def __init__(self, GUI, label, textvariable, placeholder,toggle_var = True,fg='grey'):
        super().__init__(GUI, width=int(430 * scaling_factor), height=int(166 * scaling_factor), background="#dcdad5")
        self.pack_propagate(False)
        self.textvariable = textvariable
        self.L = ttk.Label(self, text=label, style="label2.TLabel")
        self.L.place(x=8 * scaling_factor, y=2 * scaling_factor)
        self.toggle_var = toggle_var
        self.fg = fg

        # Setting up the Text widget to behave like a single-line entry
        self.E1 = tk.Text(self, height=1, wrap='none', font=FONT7,
                        borderwidth=2, relief='flat', highlightthickness=1,
                        highlightbackground='grey', highlightcolor='grey', undo=True)
        self.E1.place(x=126 * scaling_factor, y=0, width=int(283*scaling_factor), height=int(23*scaling_factor))

        self.placeholder = placeholder
        self.placeholder_active = True
        self.insert_placeholder()
        input_field_date.instances.append(self)
        self.switch_editable()
        self.E1.bind('<FocusIn>', self.on_entry_click)
        self.E1.bind('<FocusOut>', self.on_focus_out)
        self.E1.bind('<KeyPress>', self.validate_input)
        self.E1.bind("<Tab>", focus_next_widget)  # Tab to next widget

    def insert_placeholder(self):
        """ Insert placeholder text into the Text widget. """
        if self.placeholder_active and not self.E1.get('1.0', 'end-1c').strip():
            self.E1.insert('end', self.placeholder)
            self.E1.config(foreground=self.fg)

    def validate_input(self, event):
        content = self.E1.get("1.0", "end-1c").strip()
        if event.keysym in ('BackSpace', 'Left', 'Right', 'Delete'):
            # Allow navigation and deletion keys without altering the input.
            return True
        if event.char.isdigit():
            # Allow up to 8 digits (DDMMYYYY)
            numeric_content = content.replace("/", "")
            if len(numeric_content) >= 6:
                return 'break'  # Prevent more than 8 digits
            
            # Clear the placeholder if it is still active.
            if self.placeholder_active:
                self.E1.delete('1.0', 'end')
                self.E1.config(foreground='black')
                self.placeholder_active = False
            
            # Insert the digit
            self.E1.insert("end", event.char)
            
            # Auto-insert slashes after DD and MM
            if len(numeric_content) in {1, 3}:
                self.E1.insert("end", "/")
            
            return 'break'  # Prevent further Tkinter processing to avoid double input
        return 'break'  # Block any non-digit character inputs

    def on_entry_click(self, event):
        if self.toggle_var == True:
            if self.E1.get('1.0', 'end-1c').strip() == self.placeholder:
                self.E1.delete('1.0', 'end')
                self.E1.config(foreground='black')
        else:
            pass
    def on_focus_out(self, event):
        text_content = self.E1.get('1.0', 'end-1c').strip()
        if not text_content:
            self.placeholder_active = True
            self.insert_placeholder()
        else:
            self.placeholder_active = False
            self.textvariable.set(text_content)

    def switch_editable(self):
        if self.toggle_var == True:
            self.E1.config(state='normal')
        else:
            self.E1.config(state='disable')

## CLASS FOR NUMERIC AND Tel No.
class input_field_telephone(tk.Frame):
    instances = []
    def __init__(self, GUI, label, textvariable, default_text,toggle_var = True,fg='grey'):
        super().__init__(GUI, width=int(430 * scaling_factor), height=int(166 * scaling_factor), background="#dcdad5")
        self.pack_propagate(False)
        self.textvariable = textvariable
        self.toggle_var = toggle_var
        self.fg = fg

        self.L = ttk.Label(self, text=label, style="label2.TLabel")
        self.L.place(x=8 * scaling_factor, y=2 * scaling_factor)

        # Setting up the Text widget to behave like a single-line entry
        self.E1 = tk.Text(self, height=1, wrap='none', font=FONT7,
                        borderwidth=2, relief='flat', highlightthickness=1,
                        highlightbackground='grey', highlightcolor='grey', undo=True)
        self.E1.place(x=126 * scaling_factor, y=0, width=int(283*scaling_factor), height=int(23*scaling_factor))

        self.default_text = default_text
        self.placeholder_active = True
        self.insert_placeholder()
        input_field_telephone.instances.append(self)
        self.switch_editable()
        self.E1.bind('<FocusIn>', self.on_entry_click)
        self.E1.bind('<FocusOut>', self.on_focus_out)
        self.E1.bind('<KeyPress>', self.validate_input)
        self.E1.bind("<Tab>", focus_next_widget)  # Tab to next widget

    def insert_placeholder(self):
        """ Insert placeholder text into the Text widget. """
        if self.placeholder_active and not self.E1.get('1.0', 'end-1c').strip():
            self.E1.insert('end', self.default_text)
            self.E1.config(foreground=self.fg)

    def validate_input(self, event):
        content = self.E1.get("1.0", "end-1c").strip()
        if event.keysym in ('BackSpace', 'Left', 'Right', 'Delete'):
            # Allow navigation and deletion keys without altering the input.
            return True
        if event.char.isdigit():
            # Allow up to 10 digits (xxx-xxx-xxxx)
            numeric_content = content.replace("-", "")
            if len(numeric_content) >= 10:
                return 'break'  # Prevent more than 10 digits
            
            # Clear the placeholder if it is still active.
            if self.placeholder_active:
                self.E1.delete('1.0', 'end')
                self.E1.config(foreground='black')
                self.placeholder_active = False
            
            # Insert the digit
            self.E1.insert("end", event.char)
            
            # Auto-insert slashes after DD and MM
            if len(numeric_content) in {2, 5}:
                self.E1.insert("end", "-")
            
            return 'break'  # Prevent further Tkinter processing to avoid double input
        return 'break'  # Block any non-digit character inputs

    def on_entry_click(self, event):
        if self.toggle_var == True:
            if self.E1.get('1.0', 'end-1c').strip() == self.default_text:
                self.E1.delete('1.0', 'end')
                self.E1.config(foreground='black')
        else:
            pass

    def on_focus_out(self, event):
        text_content = self.E1.get('1.0', 'end-1c').strip()
        if not text_content:
            self.placeholder_active = True
            self.insert_placeholder()
        else:
            self.placeholder_active = False
            self.textvariable.set(text_content)

    def switch_editable(self):
        if self.toggle_var == True:
            self.E1.config(state='normal')
        else:
            self.E1.config(state='disable')

## CLASS FOR TEXT WITH SCROLL BAR
class input_field_remark:
    instances = []
    def __init__(self, master, font, scaling_factor, placeholder, y_position,textvariable,toggle_var = True,fg='grey'):
        self.master = master
        self.font = font
        self.scaling_factor = scaling_factor
        self.placeholder = placeholder
        self.y_position = y_position
        self.placeholder_active = True
        self.textvariable = textvariable
        self.toggle_var = toggle_var
        self.fg = fg
        self.create_widgets()
        self.place_widgets()
        self.configure_bindings()
        input_field_remark.instances.append(self)
        self.switch_editable()

    def create_widgets(self):
        """Creates the Text widget and its scrollbar."""
        self.text_widget = tk.Text(self.master, height=int(4.5 * self.scaling_factor),
                                font=self.font, highlightbackground="grey",
                                highlightcolor="grey", highlightthickness=1,
                                borderwidth=2, relief="flat", wrap="none")
        self.scrollbar = tk.Scrollbar(self.master, command=self.text_widget.yview)

    def place_widgets(self):
        """Places the Text widget and the scrollbar in the master widget."""
        self.text_widget.place(x=int(156 * self.scaling_factor), y=self.y_position,
                            width=int(283 * self.scaling_factor), height=int(55 * self.scaling_factor))

    def configure_bindings(self):
        """Configures bindings for the Text widget."""
        self.text_widget.config(yscrollcommand=self.scrollbar.set)
        self.text_widget.bind("<FocusIn>", self.on_focus_in)
        self.text_widget.bind("<FocusOut>", self.on_focus_out)
        self.insert_placeholder()

    def on_focus_in(self, event):
        """Clears the placeholder text when the widget gains focus."""
        if self.toggle_var:
            text_content = self.text_widget.get('1.0', 'end-1c')
            if self.placeholder_active and text_content == self.placeholder:
                self.text_widget.delete('1.0', 'end')
                self.text_widget.config(foreground='black')
                self.placeholder_active = False

    def on_focus_out(self, event):
        """Reinserts the placeholder if the field is empty."""
        text_content = self.text_widget.get('1.0', 'end-1c').strip()
    
        # If the text is empty, reinsert the placeholder
        if not text_content:
            self.placeholder_active = True
            self.insert_placeholder()
        else:
            # If there is text, set the textvariable
            self.textvariable.set(text_content)
            self.placeholder_active = False  # Mark placeholder as inactive if actual text is entered

    def insert_placeholder(self):
        """Inserts placeholder text into the Text widget."""
        if self.placeholder_active:
            self.text_widget.insert('end', self.placeholder)
            self.text_widget.config(foreground=self.fg)

    def get_text(self):
        """Returns the current text from the Text widget."""
        return self.text_widget.get('1.0', 'end-1c')

    def switch_editable(self):
        if self.toggle_var == True:
            self.text_widget.config(state='normal')
        else:
            self.text_widget.config(state='disable')

    def destroy(self):
        """Destroys all widgets created by this instance."""
        if self.text_widget:
            self.text_widget.destroy()
        if self.scrollbar:
            self.scrollbar.destroy()

class input_field_remark_click_toplevel:
    instances = []
    def __init__(self, master, font, scaling_factor, placeholder, y_position,textvariable,toggle_var = True,fg='grey'):
        self.master = master
        self.font = font
        self.scaling_factor = scaling_factor
        self.placeholder = placeholder
        self.y_position = y_position
        self.placeholder_active = True
        self.textvariable = textvariable
        self.toggle_var = toggle_var
        self.fg = fg
        self.create_widgets()
        self.place_widgets()
        self.configure_bindings()
        input_field_remark.instances.append(self)
        self.switch_editable()

    def create_widgets(self):
        """Creates the Text widget and its scrollbar."""
        self.text_widget = tk.Text(self.master, height=int(4.5 * self.scaling_factor),
                                font=self.font, highlightbackground="grey",
                                highlightcolor="grey", highlightthickness=1,
                                borderwidth=2, relief="flat", wrap="none")
        self.scrollbar = tk.Scrollbar(self.master, command=self.text_widget.yview)

    def place_widgets(self):
        """Places the Text widget and the scrollbar in the master widget."""
        self.text_widget.place(x=int(156 * self.scaling_factor), y=self.y_position,
                            width=int(283 * self.scaling_factor), height=int(55 * self.scaling_factor))

    def configure_bindings(self):
        """Configures bindings for the Text widget."""
        self.text_widget.config(yscrollcommand=self.scrollbar.set)
        self.text_widget.bind("<FocusIn>", self.on_focus_in)
        self.text_widget.bind("<FocusOut>", self.on_focus_out)
        if not self.toggle_var:
            self.text_widget.bind("<Button-1>", self.open_magnified_view)
        self.insert_placeholder()

    def open_magnified_view(self, event):
        """Opens a Toplevel window with a magnified Text widget."""
        # Create a new Toplevel window
        self.magnified_window = tk.Toplevel(self.master)
        self.magnified_window.title("Remark view")
        self.windowsize = center_windows(int(400*scaling_factor),int(200*scaling_factor))
        self.magnified_window.geometry(self.windowsize)  # Adjust the size as needed
        self.magnified_window.transient(self.master)  # Keep it above the main window

        # Create a larger Text widget in the Toplevel window
        magnified_text = tk.Text(self.magnified_window, font=self.font, height=10, width=50,
        highlightbackground="grey",highlightcolor="grey", highlightthickness=1,borderwidth=2, relief="flat", wrap="none")
        magnified_text.pack(expand=True, fill='both', padx=10, pady=10)

        # Insert the current text from the main Text widget into the magnified Text widget
        magnified_text.insert('1.0', self.get_text())
        magnified_text.config(state='disabled')  # Make it read-only if desired

    def on_focus_in(self, event):
        """Clears the placeholder text when the widget gains focus."""
        if self.toggle_var:
            text_content = self.text_widget.get('1.0', 'end-1c')
            if self.placeholder_active and text_content == self.placeholder:
                self.text_widget.delete('1.0', 'end')
                self.text_widget.config(foreground='black')
                self.placeholder_active = False

    def on_focus_out(self, event):
        """Reinserts the placeholder if the field is empty."""
        text_content = self.text_widget.get('1.0', 'end-1c').strip()
    
        # If the text is empty, reinsert the placeholder
        if not text_content:
            self.placeholder_active = True
            self.insert_placeholder()
        else:
            # If there is text, set the textvariable
            self.textvariable.set(text_content)
            self.placeholder_active = False  # Mark placeholder as inactive if actual text is entered

    def insert_placeholder(self):
        """Inserts placeholder text into the Text widget."""
        if self.placeholder_active:
            self.text_widget.insert('end', self.placeholder)
            self.text_widget.config(foreground=self.fg)

    def get_text(self):
        """Returns the current text from the Text widget."""
        return self.text_widget.get('1.0', 'end-1c')

    def switch_editable(self):
        if self.toggle_var == True:
            self.text_widget.config(state='normal')
        else:
            self.text_widget.config(state='disable')

    def destroy(self):
        """Destroys all widgets created by this instance."""
        if self.text_widget:
            self.text_widget.destroy()
        if self.scrollbar:
            self.scrollbar.destroy()

## CLASS FOR PDF
class input_field_pdf(tk.Frame):
    def __init__(self,GUI,label_text,x_pos,y_pos,textvariable):
        super().__init__(GUI, width=int(400 * scaling_factor), height=int(30 * scaling_factor), background="#dcdad5")
        self.pack_propagate(False)
        self.file_path = None
        self.file_name = None
        self.GUI = GUI
        self.label_text = label_text
        # 'P&ID Markup:'
        self.L = ttk.Label(GUI,text=self.label_text,style="label2.TLabel")
        self.L.place(x=x_pos,y=y_pos)

        self.file_path_name = ttk.Label(GUI,text='',font=FONT8,foreground= "#2d7ad6",cursor="hand2")
        self.file_path_name.place(x=x_pos+int(114*scaling_factor),y=y_pos)

        self.pdf_icon = create_resized_image('pdf2.png',int(11*scaling_factor),int(11*scaling_factor))
        self.pdf_but = tk.Button(GUI,image=self.pdf_icon,command=self.attach_pdf,
                                bg="#dcdad5",             # Background color
                                activebackground="#e0e0e0",# Background color when clicked or hovered
                                borderwidth=0,            # Width of the button's border
                                relief="raised",          # Type of border effect (flat, raised, sunken, groove, ridge)
                                highlightthickness=2,      # Thickness of highlight border when focused
                                highlightbackground="#cccccc",  # Color of the highlight border
                                highlightcolor="#ff0000",  # Color of the highlight border when the button is focused
                                )
        self.pdf_but.config(width=int(11*scaling_factor),height=int(11*scaling_factor))
        self.pdf_but.place(x=x_pos+int(81*scaling_factor),y=y_pos+int(3*scaling_factor))
        
        self.check_icon = create_resized_image('check.png',int(11*scaling_factor),int(11*scaling_factor))
        self.check_but = tk.Button(self,image=self.check_icon,command=self.attach_pdf,
                                bg="#dcdad5",             # Background color
                                activebackground="#e0e0e0",# Background color when clicked or hovered
                                borderwidth=0,            # Width of the button's border
                                relief="raised",          # Type of border effect (flat, raised, sunken, groove, ridge)
                                highlightthickness=2,      # Thickness of highlight border when focused
                                highlightbackground="#cccccc",  # Color of the highlight border
                                highlightcolor="#ff0000",  # Color of the highlight border when the button is focused
                                )
        self.check_but.config(width=int(11*scaling_factor),height=int(11*scaling_factor))
        
        self.textvariable = textvariable

    def attach_pdf(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if self.file_path:
            # print(f'file path is OPEN::{self.file_path}')
            self.file_name, self.file_extension  = os.path.splitext(os.path.basename(self.file_path))  # Extract the file name from the path
            max_length = 40
            if len(self.file_name) > max_length:
                # Keep the start and end of the file name, and truncate the middle
                truncated_name = self.file_name[:max_length // 2] + '...' + self.file_name[-(max_length // 2):]
                self.file_name = truncated_name + self.file_extension
            else:
                self.file_name = self.file_name + self.file_extension
            
            self.file_path_name.config(text=self.file_name)
            self.textvariable.set(self.file_path)
            self.file_path_name.bind("<Button-1>", lambda e:webbrowser.open(self.file_path))
            self.check_but.place(x=int(96*scaling_factor),y=int(4*scaling_factor))
            self.GUI.focus_set()
    
    def clear_file_name(self):
        self.file_path_name.config(text='')
        self.file_path = None
        self.file_name = None

## CLASS FOR PDF Show
class pdf_show(tk.Frame):
    def __init__(self,GUI,labeltext,x_pos,y_pos,textvariable):
        super().__init__(GUI, width=int(400 * scaling_factor), height=int(30 * scaling_factor), background="#dcdad5")
        self.pack_propagate(False)
        self.file_path = None
        self.file_name = None
        self.GUI = GUI
        self.labeltext = labeltext
        # Ensure textvariable is a StringVar
        if isinstance(textvariable, tk.StringVar):
            self.textvariable = textvariable
        else:
            # If it's just a string, wrap it in a StringVar
            self.textvariable = tk.StringVar(value=textvariable)

        self.L = ttk.Label(GUI,text=self.labeltext,style="label2.TLabel")
        self.L.place(x=x_pos,y=y_pos)

        self.file_path_name = ttk.Label(GUI,text='',font=FONT8,foreground= "#2d7ad6",cursor="hand2")
        self.file_path_name.place(x=x_pos+int(114*scaling_factor),y=y_pos)

        self.pdf_to_show()

    def pdf_to_show(self):
        self.file_path = self.textvariable.get()
        if self.file_path:
            self.file_name, self.file_extension  = os.path.splitext(os.path.basename(self.file_path))  # Extract the file name from the path
            max_length = 40
            if len(self.file_name) > max_length:
                # Keep the start and end of the file name, and truncate the middle
                truncated_name = self.file_name[:max_length // 2] + '...' + self.file_name[-(max_length // 2):]
                self.file_name = truncated_name + self.file_extension
            else:
                self.file_name = self.file_name + self.file_extension
            
            self.file_path_name.config(text=self.file_name)
            self.textvariable.set(self.file_path)
            self.file_path_name.bind("<Button-1>", lambda e:webbrowser.open(self.file_path))
            self.GUI.focus_set()
    
    def destroy(self):
        self.file_path_name.config(text='')
        self.file_path = None
        self.file_name = None

## CLASS FOR CREATE AND COPY FILE
class create_folder_copy_file:
    def __init__(self, folder_date, folder_area, folder_work_title, 
                file_location_pdf, file_location_override,file_location_linebreak):
        self.folder_date = folder_date
        self.folder_area = folder_area
        self.folder_work_title = folder_work_title
        self.file_location_pdf = file_location_pdf
        self.file_location_override = file_location_override
        self.file_location_linebreak = file_location_linebreak
        # CREATE: The folder name from Work tile, Date and Area
        self.folder_name = f"{self.folder_date}_{self.folder_area}_{self.folder_work_title}"
        self.new_folder_path = os.path.join(folder_path, self.folder_name)

    def create_folder(self):
        # Construct the full folder path
        # new_folder_path = os.path.join(folder_path, self.folder_name)
        # Try to create the new folder
        try:
            os.makedirs(self.new_folder_path, exist_ok=True)
            # messagebox.showinfo("Success", f"Folder created: {new_folder_path}")
        except OSError as e:
            # messagebox.showerror("Error", f"Could not create folder: {e}")
            0
            return

    def transfer_pdf(self):
        # Location file for transfer
        try:
            shutil.copy(self.file_location_pdf, self.new_folder_path)
        except OSError as e:
            # messagebox.showerror("Error", f"Could not rename file: {e}")
            0
        return

    def transfer_override(self):
        # Location file for transfer
        try:
            shutil.copy(self.file_location_override, self.new_folder_path)
        except OSError as e:
            # messagebox.showerror("Error", f"Could not rename file: {e}")
            0
        return

    def transfer_linebreak(self):
        # Location file for transfer
        try:
            shutil.copy(self.file_location_linebreak, self.new_folder_path)
        except OSError as e:
            # messagebox.showerror("Error", f"Could not rename file: {e}")
            0
        return

    def rename_pdf(self):
        # FUNCTION: Get file name
        file_name_pdf = os.path.basename(self.file_location_pdf)
        # FUNCTION: Modify file name
        mod_name = f'{self.folder_work_title}_P&ID Markup_Updated_{self.folder_date}'
        # FUNCTION: Extract '.pdf' from file name
        new_file_name_pdf = mod_name + os.path.splitext(file_name_pdf)[1]
        # CREATE: New file path (New file .pdf name)
        new_file_path_pdf = os.path.join(self.new_folder_path,new_file_name_pdf)

        try:
            os.rename(os.path.join(self.new_folder_path,file_name_pdf),new_file_path_pdf)
        except OSError as e:
            # messagebox.showerror("Error", f"Could not rename file: {e}")
            0
        return new_file_path_pdf
    
    def rename_override(self):
        # FUNCTION: Get file name
        file_name_override = os.path.basename(self.file_location_override)
        # FUNCTION: Modify file name
        mod_name = f'{self.folder_work_title}_Override list_Updated_{self.folder_date}'
        # FUNCTION: Extract '.pdf' from file name
        new_file_name_override = mod_name + os.path.splitext(file_name_override)[1]
        # CREATE: New file path (New file .pdf name)
        new_file_path_override = os.path.join(self.new_folder_path,new_file_name_override)

        try:
            os.rename(os.path.join(self.new_folder_path,file_name_override),new_file_path_override)
        except OSError as e:
            # messagebox.showerror("Error", f"Could not rename file: {e}")
            0
        return new_file_path_override
    
    def rename_linebreak(self):
        # FUNCTION: Get file name
        file_name_linebreak = os.path.basename(self.file_location_linebreak)
        # FUNCTION: Modify file name
        mod_name = f'{self.folder_work_title}_Line break_Updated_{self.folder_date}'
        # FUNCTION: Extract '.pdf' from file name
        new_file_name_linebreake = mod_name + os.path.splitext(file_name_linebreak)[1]
        # CREATE: New file path (New file .pdf name)
        new_file_path_override = os.path.join(self.new_folder_path,new_file_name_linebreake)

        try:
            os.rename(os.path.join(self.new_folder_path,file_name_linebreak),new_file_path_override)
        except OSError as e:
            # messagebox.showerror("Error", f"Could not rename file: {e}")
            0
        return new_file_path_override

## CLASS COPY FILE FOR UPDATE WIDGET
class copy_rename_file_for_update_widget:
    def __init__(self,file_location_pdf_new, file_location_override_new, folder_location_input):
        self.file_location_pdf_new = file_location_pdf_new
        self.file_location_override_new = file_location_override_new
        self.folder_location_input = folder_location_input
        if os.path.isdir(self.folder_location_input):
            self.folder_location = self.folder_location_input
        else:
            self.folder_location = os.path.dirname(self.folder_location_input)

    def testprint(self):
        print(f'folder_location_input: {self.folder_location_input}')
        print(f'folder_location: {self.folder_location}')
        print(f'file_location_pdf_new: {self.file_location_pdf_new}')

    def transfer_pdf(self):
        # Location file for transfer
        print(f'transfer_pdf activate')
        try:
                            #From this place ----> To this place
            shutil.copy(self.file_location_pdf_new, self.folder_location)
        except OSError as e:
            # messagebox.showerror("Error", f"Could not rename file: {e}")
            0
        return

    def transfer_override(self):
        # Location file for transfer
        print(f'transfer_override activate')
        try:
            shutil.copy(self.file_location_override_new, self.folder_location)
        except OSError as e:
            # messagebox.showerror("Error", f"Could not rename file: {e}")
            0
        return

    def rename_pdf(self):
        # FUNCTION: Get file name
        target_word = "_P&ID Markup"
        found_files = []
        self.testprint()
         # List all files in the directory
        all_files = os.listdir(self.folder_location)

        # Check if the directory is empty
        if not all_files:
            print("The folder is empty, proceeding with a default file name.")
            total_files_found = 0
            # Extract the last part of the folder_location_input path
            last_segment = os.path.basename(self.folder_location_input)
            # Split by underscores and take the part after the second one
            work_file_name_pdf = last_segment.split('_', 2)[-1]
        else:
            # Search for files containing the target word
            for file in all_files:
                if target_word in file:
                    found_files.append(file)

        if found_files:
            total_files_found = len(found_files)
            print(f"Total files found: {total_files_found}")
            work_file_name_pdf_full = found_files[0]
            work_file_name_pdf = work_file_name_pdf_full.split(target_word)[0]
            print(f"Found file: {work_file_name_pdf}")
            # print(f'folder_location: {self.folder_location}')
        else:
            print("No file found, proceeding with renaming")
            total_files_found = 0
            # Extract the last part of the folder_location_input path
            last_segment = os.path.basename(self.folder_location_input)
            # Split by underscores and take the part after the second one
            work_file_name_pdf = last_segment.split('_', 2)[-1]  # Gets everything after the second underscore

        # print(f'file_location_pdf_new: {self.file_location_pdf_new}')
        file_basename_pdf = os.path.basename(self.file_location_pdf_new)
        print(f"File basename: {file_basename_pdf}")
        # FUNCTION: Modify file name
        mod_name = f'{work_file_name_pdf}_P&ID Markup_Updated_{date_str(2)}_Rev{total_files_found}'
        # FUNCTION: Extract '.pdf' from file name and combine with new name
        new_file_name_pdf = mod_name + os.path.splitext(file_basename_pdf)[1]
        print(f"New file name: {new_file_name_pdf}")
        # CREATE: New file path (New file .pdf name)
        original_file_path_pdf = os.path.join(self.folder_location,file_basename_pdf)
        # print(f"Original file path: {original_file_path_pdf}")
        new_file_path_pdf = os.path.join(self.folder_location,new_file_name_pdf)
        # print(f"New file path: {new_file_path_pdf}")

        try:
            os.rename(original_file_path_pdf,new_file_path_pdf)
            print("Rename successful")
        except OSError as e:
            messagebox.showerror("Error", f"Could not rename file: {e}")
            0
        return new_file_path_pdf
    
    def rename_override(self):
                # FUNCTION: Get file name
        target_word = "_Override list"
        found_files = []
        self.testprint()
         # List all files in the directory
        all_files = os.listdir(self.folder_location)

        # Check if the directory is empty
        if not all_files:
            print("The folder is empty, proceeding with a default file name.")
            total_files_found = 0
            # Extract the last part of the folder_location_input path
            last_segment = os.path.basename(self.folder_location_input)
            # Split by underscores and take the part after the second one
            work_file_name_override = last_segment.split('_', 2)[-1]
        else:
            # Search for files containing the target word
            for file in all_files:
                if target_word in file:
                    found_files.append(file)

        if found_files:
            # Get the count of found files
            total_files_found = len(found_files)
            print(f"Total files found: {total_files_found}")
            work_file_name_override_full = found_files[0]
            work_file_name_override = work_file_name_override_full.split(target_word)[0]
            print(f"Found file: {work_file_name_override}")
        else:
           print("No file found, proceeding with renaming")
           total_files_found = 0
            # Extract the last part of the folder_location_input path
           last_segment = os.path.basename(self.folder_location_input)
            # Split by underscores and take the part after the second one
           work_file_name_override = last_segment.split('_', 2)[-1]  # Gets everything after the second underscore
        # print(f'file_location_pdf_new: {self.file_location_override_new}')

        file_basename_override = os.path.basename(self.file_location_override_new)
        print(f"File basename: {file_basename_override}")
        # FUNCTION: Modify file name
        mod_name = f'{work_file_name_override}_Override list_Updated_{date_str(2)}_Rev{total_files_found}'
        # FUNCTION: Extract '.pdf' from file name and combine with new name
        new_file_name_override = mod_name + os.path.splitext(file_basename_override)[1]
        print(f"New file name: {new_file_name_override}")
        # CREATE: New file path (New file .pdf name)
        original_file_path_override = os.path.join(self.folder_location,file_basename_override)
        # print(f"Original file path: {original_file_path_override}")
        new_file_path_override = os.path.join(self.folder_location,new_file_name_override)
        # print(f"New file path: {new_file_path_override}")

        try:
            os.rename(original_file_path_override,new_file_path_override)
            print("Rename successful")
        except OSError as e:
            # messagebox.showerror("Error", f"Could not rename file: {e}")
            0
        return new_file_path_override

## CLASS FOR Push notification via Email
class pust_notify_via_email:
    asew = scaling_factor
    
## CLASS FOR APPROVE BUTTON (TEXT WITH SCROLL BAR)
class input_field_remark_for_approve_button():
    instances = []
    def __init__(self, master, font, scaling_factor, placeholder, y_position,textvariable,fg='grey'):
        self.master = master
        self.font = font
        self.scaling_factor = scaling_factor
        self.placeholder = placeholder
        self.y_position = y_position
        self.placeholder_active = True
        self.textvariable = textvariable
        self.fg = fg
        self.create_widgets()
        self.place_widgets()
        self.configure_bindings()
        input_field_remark_for_approve_button.instances.append(self)

    def create_widgets(self):
        """Creates the Text widget and its scrollbar."""
        self.text_widget = tk.Text(self.master, height=int(4.5 * self.scaling_factor),
                                font=self.font, highlightbackground="grey",
                                highlightcolor="grey", highlightthickness=1,
                                borderwidth=2, relief="flat", wrap="none")
        self.scrollbar = tk.Scrollbar(self.master, command=self.text_widget.yview)

    def place_widgets(self):
        """Places the Text widget and the scrollbar in the master widget."""
        self.text_widget.place(x=int(111 * self.scaling_factor), y=self.y_position,
                            width=int(244 * self.scaling_factor), height=int(55 * self.scaling_factor))

    def configure_bindings(self):
        """Configures bindings for the Text widget."""
        self.text_widget.config(yscrollcommand=self.scrollbar.set)
        self.text_widget.bind("<FocusIn>", self.on_focus_in)
        self.text_widget.bind("<FocusOut>", self.on_focus_out)
        self.insert_placeholder()

    def on_focus_in(self, event):
        """Clears the placeholder text when the widget gains focus."""
        text_content = self.text_widget.get('1.0', 'end-1c')
        if self.placeholder_active and text_content == self.placeholder:
            self.text_widget.delete('1.0', 'end')
            self.text_widget.config(foreground='black')
            self.placeholder_active = False

    def on_focus_out(self, event):
        """Reinserts the placeholder if the field is empty."""
        text_content = self.text_widget.get('1.0', 'end-1c').strip()
    
        # If the text is empty, reinsert the placeholder
        if not text_content:
            self.placeholder_active = True
            self.insert_placeholder()
        else:
            # If there is text, set the textvariable
            self.textvariable.set(text_content)
            self.placeholder_active = False  # Mark placeholder as inactive if actual text is entered

    def insert_placeholder(self):
        """Inserts placeholder text into the Text widget."""
        if self.placeholder_active:
            self.text_widget.insert('end', self.placeholder)
            self.text_widget.config(foreground=self.fg)

    def get_text(self):
        """Returns the current text from the Text widget."""
        return self.text_widget.get('1.0', 'end-1c')
        
## CLASS FOR PDF
class pdf_new_for_update_button(tk.Frame):
    def __init__(self,GUI,label_text,x_pos,y_pos,textvariable):
        super().__init__(GUI, width=int(350 * scaling_factor), height=int(30 * scaling_factor), background="#dcdad5")
        self.pack_propagate(False)
        self.file_path = None
        self.file_name = None
        self.GUI = GUI
        self.label_text = label_text
        # 'P&ID Markup:'
        self.L = ttk.Label(GUI,text=self.label_text,style="label2.TLabel")
        self.L.place(x=x_pos,y=y_pos)

        self.file_path_name = ttk.Label(GUI,text='',font=FONT8,foreground= "#2d7ad6",cursor="hand2")
        self.file_path_name.place(x=x_pos+int(114*scaling_factor),y=y_pos+int(1*scaling_factor))

        self.pdf_icon = create_resized_image('pdf2.png',int(11*scaling_factor),int(11*scaling_factor))
        self.pdf_but = tk.Button(GUI,image=self.pdf_icon,command=self.attach_pdf,
                                bg="#dcdad5",             # Background color
                                activebackground="#e0e0e0",# Background color when clicked or hovered
                                borderwidth=0,            # Width of the button's border
                                relief="raised",          # Type of border effect (flat, raised, sunken, groove, ridge)
                                highlightthickness=2,      # Thickness of highlight border when focused
                                highlightbackground="#cccccc",  # Color of the highlight border
                                highlightcolor="#ff0000",  # Color of the highlight border when the button is focused
                                )
        self.pdf_but.config(width=int(11*scaling_factor),height=int(11*scaling_factor))
        self.pdf_but.place(x=x_pos+int(81*scaling_factor),y=y_pos+int(3*scaling_factor))
        
        self.check_icon = create_resized_image('check.png',int(11*scaling_factor),int(11*scaling_factor))
        self.check_but = tk.Button(self,image=self.check_icon,command=self.attach_pdf,
                                bg="#dcdad5",             # Background color
                                activebackground="#e0e0e0",# Background color when clicked or hovered
                                borderwidth=0,            # Width of the button's border
                                relief="raised",          # Type of border effect (flat, raised, sunken, groove, ridge)
                                highlightthickness=2,      # Thickness of highlight border when focused
                                highlightbackground="#cccccc",  # Color of the highlight border
                                highlightcolor="#ff0000",  # Color of the highlight border when the button is focused
                                )
        self.check_but.config(width=int(11*scaling_factor),height=int(11*scaling_factor))
        
        self.textvariable = textvariable     

    def attach_pdf(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if self.file_path:
            # print(f'file path is OPEN::{self.file_path}')
            self.file_name, self.file_extension  = os.path.splitext(os.path.basename(self.file_path))  # Extract the file name from the path
            max_length = 30
            if len(self.file_name) > max_length:
                # Keep the start and end of the file name, and truncate the middle
                truncated_name = self.file_name[:max_length // 2] + '...' + self.file_name[-(max_length // 2):]
                self.file_name = truncated_name + self.file_extension
            else:
                self.file_name = self.file_name + self.file_extension
            
            self.file_path_name.config(text=self.file_name)
            self.textvariable.set(self.file_path)
            self.file_path_name.bind("<Button-1>", lambda e:webbrowser.open(self.file_path))
            self.check_but.place(x=int(96*scaling_factor),y=int(4*scaling_factor))
            self.GUI.focus_set()
    
    def clear_file_name(self):
        self.file_path_name.config(text='')
        self.file_path = None
        self.file_name = None  

## CLASS FOR APPROVE BUTTON (TEXT WITH SCROLL BAR)
class input_field_remark_for_update_button():
    instances = []
    def __init__(self, master, font, scaling_factor, placeholder, y_position,textvariable,fg='grey'):
        self.master = master
        self.font = font
        self.scaling_factor = scaling_factor
        self.placeholder = placeholder
        self.y_position = y_position
        self.placeholder_active = True
        self.textvariable = textvariable
        self.fg = fg
        self.create_widgets()
        self.place_widgets()
        self.configure_bindings()
        input_field_remark_for_update_button.instances.append(self)

    def create_widgets(self):
        """Creates the Text widget and its scrollbar."""
        self.text_widget = tk.Text(self.master, height=int(4.5 * self.scaling_factor),
                                font=self.font, highlightbackground="grey",
                                highlightcolor="grey", highlightthickness=1,
                                borderwidth=2, relief="flat", wrap="none")
        self.scrollbar = tk.Scrollbar(self.master, command=self.text_widget.yview)

    def place_widgets(self):
        """Places the Text widget and the scrollbar in the master widget."""
        self.text_widget.place(x=int(111 * self.scaling_factor), y=self.y_position,
                            width=int(262 * self.scaling_factor), height=int(55 * self.scaling_factor))

    def configure_bindings(self):
        """Configures bindings for the Text widget."""
        self.text_widget.config(yscrollcommand=self.scrollbar.set)
        self.text_widget.bind("<FocusIn>", self.on_focus_in)
        self.text_widget.bind("<FocusOut>", self.on_focus_out)
        self.insert_placeholder()

    def on_focus_in(self, event):
        """Clears the placeholder text when the widget gains focus."""
        text_content = self.text_widget.get('1.0', 'end-1c')
        if self.placeholder_active and text_content == self.placeholder:
            self.text_widget.delete('1.0', 'end')
            self.text_widget.config(foreground='black')
            self.placeholder_active = False

    def on_focus_out(self, event):
        """Reinserts the placeholder if the field is empty."""
        text_content = self.text_widget.get('1.0', 'end-1c').strip()
    
        # If the text is empty, reinsert the placeholder
        if not text_content:
            self.placeholder_active = True
            self.insert_placeholder()
        else:
            # If there is text, set the textvariable
            self.textvariable.set(text_content)
            self.placeholder_active = False  # Mark placeholder as inactive if actual text is entered

    def insert_placeholder(self):
        """Inserts placeholder text into the Text widget."""
        if self.placeholder_active:
            self.text_widget.insert('end', self.placeholder)
            self.text_widget.config(foreground=self.fg)

    def get_text(self):
        """Returns the current text from the Text widget."""
        return self.text_widget.get('1.0', 'end-1c')
    
################################################# OVERVIEW TAB ################################################# 
# CREATE: the first tab (Overview) and add a frame to it
overview_page = ttk.Frame(notebook)
notebook.add(overview_page, text="Overview")

# CREATE: Place frame0 and frame1 to Overview tab
frame0 = tk.Frame(overview_page, background="#dcdad5", borderwidth=1, relief="flat")
frame0.place(x=0, y=0, width=int(1045*scaling_factor), height=int(620*scaling_factor))

frame1 = tk.Frame(overview_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#b4b4b4", highlightthickness=2)
frame1.place(x=int(20*scaling_factor), y=int(50*scaling_factor), width=int(895*scaling_factor), height=int(520*scaling_factor))

frame2 = tk.Frame(overview_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#b4b4b4", highlightthickness=2)
frame2.place(x=int(20*scaling_factor), y=int(570*scaling_factor), width=int(895*scaling_factor), height=int(25*scaling_factor))

frame3 = tk.Frame(overview_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#dcdad5", highlightthickness=2)
frame3.place(x=int(20*scaling_factor), y=int(600*scaling_factor), width=int(60*scaling_factor), height=int(25*scaling_factor))

frame4 = tk.Frame(overview_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#dcdad5", highlightthickness=2)
frame4.place(x=int(1025*scaling_factor), y=int(605*scaling_factor), width=int(25*scaling_factor), height=int(25*scaling_factor))

################### "NEW" BUTTON (TOP LEVEL)
def create_new_loto_toplevel():
    # CREATE: new_loto_GUI Toplevel
    new_loto_GUI, NewLoto_x, NewLoto_y = create_new_window('New LOTO work')

    # CONFIGURE: label1 (Main)
    configure_label_style()

    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(new_loto_GUI,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(new_loto_GUI, text="Work detail",style="label1.TLabel")
    label1.place(x=int(20*scaling_factor),y=int(13*scaling_factor))
    line1_x1 = int(16*scaling_factor)
    line1_y1 = int(25*scaling_factor)
    line1_x2 = int(463*scaling_factor)
    line1_y2 = int(490*scaling_factor)
    line1.create_rectangle(line1_x1,line1_y1,line1_x2,line1_y2,fill='#dcdad5',width=1,outline='#a9a7a3')
    line1.create_rectangle(line1_x1+scaling_factor,line1_y1+scaling_factor,
                        line1_x2-scaling_factor,line1_y2-scaling_factor,
                        fill='#dcdad5',width=1,outline='#f8f2ea')
    
    ## CREATE: FRAME
    frame3 = tk.Frame(new_loto_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(265*scaling_factor), y=int(495*scaling_factor), width=200*scaling_factor, height=40*scaling_factor)
    
    ## CREATE: VARIABLE AND ENTRY BY CLASS
    ### CREATE: WORK TITLE ENTRY

    #### FUNCTION: Loop for indicate hieght each row
    topic_x = int(30*scaling_factor)
    entry_1 = [int(40*scaling_factor)]
    current_ent = 0
    for i in range(1,12):
        current_ent = entry_1[i-1]+int(27*scaling_factor)
        entry_1.append(current_ent)
    ############ FUNCTION: Loop for indicate hieght each row

    ### CREATE: WORK TITLE ENTRY
    v_work_title = create_work_title_entry(new_loto_GUI, topic_x, entry_1)

    ### CREATE: DEPARTMENT ENTRY
    v_department = create_incharge_entry(new_loto_GUI, topic_x, entry_1)

    ### CREATE: OWNER ENTRY
    v_owner = create_owner_entry(new_loto_GUI, topic_x, entry_1)

    # ### CREATE: INTERNAL PHONE ENTRY CUT OFF
    # v_internalphone = create_internal_phone_entry(new_loto_GUI, topic_x, entry_1)

    ### CREATE: TELEPHONE ENTRY
    #### CREATE: GUIDLINE TEXT
    v_telephone = create_telephone_entry(new_loto_GUI, topic_x, entry_1)
    ### CREATE: AREA ENTRY
    v_area = create_working_area_entry(new_loto_GUI, topic_x, entry_1)
    ### CREATE: EQUIPMENT ENTRY
    v_equipment = create_equipment_entry(new_loto_GUI, topic_x, entry_1)
    ### CREATE: START DATE ENTRY
    v_lock_date = create_lock_date_entry(new_loto_GUI, topic_x, entry_1)
    ### CREATE: LOTO No. ENTRY
    v_loto_no = create_loto_entry(new_loto_GUI, topic_x, entry_1)
    ### CREATE: TOTAL LOCK KEYS ENTRY
    v_loto_keys = create_total_lock_keys_entry(new_loto_GUI, topic_x, entry_1)
    
    ### CREATE: P&ID MARKUP ENTRY
    v_pid_pdf, pdf1 = create_pdf_entry(new_loto_GUI, entry_1)

    ### CREATE: OVERRIDE ENTRY
    v_override,ovrd = create_override_entry(new_loto_GUI, entry_1)

    ############ CREATE: REMARK ENTRY
    ### CREATE: REMARK ENTRY WITH SCROLL BAR
    v_remark = create_remark_entry(new_loto_GUI, entry_1)

    #### FUNCTION: Loop for indicate hieght each row
    entry_2 = [int(395*scaling_factor)]
    current_ent = 0
    for i in range(1,3):
        current_ent = entry_2[i-1]+int(26*scaling_factor)
        entry_2.append(current_ent)
    ############ FUNCTION: Loop for indicate hieght each row

    ### CREATE: PREPARE BY ENTRY
    v_prepare = create_prepare_entry(new_loto_GUI, topic_x, entry_2)
    ### CREATE: VERYFY BY ENTRY
    v_verify = create_verify_entry(new_loto_GUI, topic_x, entry_2)
    ### CREATE: APPROVE BY ENTRY
    v_approve,E14_instance = create_approve_entry_for_new_loto(new_loto_GUI, topic_x, entry_2)
    
    # CREATE: Button "CLEAR", "SUBMIT" and "CANCEL"
    button_y = 501

    # CONFIGURE Variable

    # CREATE: Save data to DB loto_new
    def savetodb():
        if get_form_values() == None:
            pass
        else:
            work_title, incharge_dept, owner, telephone, area, equipment, lock_date, loto_no, loto_keys, pid_pdf, override, remark, prepare, verify, approve = get_form_values()
            logid = str(int(datetime.now().strftime('%y%m%d%H%M%S')))
            folder_date = date_str(2)
            linebreak_filepath = E14_instance.get_file_path()
            create_copy_instance = create_folder_copy_file(folder_date, area, work_title,pid_pdf,override,linebreak_filepath)
            create_copy_instance.create_folder()
            time.sleep(1)
            if pid_pdf:
                create_copy_instance.transfer_pdf()
                pid_pdf = create_copy_instance.rename_pdf()
            time.sleep(1)
            if override:
                create_copy_instance.transfer_override()
                override = create_copy_instance.rename_override()
            time.sleep(1)
            if linebreak_filepath:
                create_copy_instance.transfer_linebreak()
                linebreak_filepath = create_copy_instance.rename_linebreak()
            insert_new_loto(logid,work_title,incharge_dept,owner,telephone,area,
                            equipment,lock_date,loto_no,loto_keys,pid_pdf,override,remark,prepare,verify,approve)
            update_table_pending()
            # clear_all_entries()
            new_loto_GUI.destroy()
            show_message('Message',f'The work "{work_title}" has been created successfully.')
            set_focus_on_tab(1)
        
    def get_form_values():
        work_title = v_work_title.get()
        incharge_dept = v_department.get()
        owner = v_owner.get()
        # internal_phone = v_internalphone.get()
        telephone = v_telephone.get()
        area = v_area.get()
        equipment = v_equipment.get()
        lock_date = v_lock_date.get()
        loto_no = v_loto_no.get()
        loto_keys = v_loto_keys.get()
        pid_pdf = v_pid_pdf.get()
        override = v_override.get()
        remark0 = v_remark.get()
        if remark0:
            remark = date_str(3) + '\n' + remark0
        else:
            remark = remark0
        prepare = v_prepare.get()
        verify = v_verify.get()
        approve = v_approve.get()
        # Create a list of values to check
        form_values = [
            work_title, incharge_dept, owner, telephone, 
            area, equipment, lock_date, loto_no, loto_keys, pid_pdf, 
            override, remark, prepare, verify, approve
        ]

        # Check if all of the form values are empty
        if all(value == "" for value in form_values):
            show_message('Error','Please fill in at Work title, Lock box no. and Lock date')
            new_loto_GUI.focus_set()
            return None
        elif work_title=="" or loto_no=="" or lock_date=="":
            show_message('Error','Please fill in at Work title, Lock box no. and Lock date')
            new_loto_GUI.focus_set()
            return None
        else:
            # Return the form values if not all fields are empty
            return work_title, incharge_dept, owner, telephone, area, equipment, lock_date, loto_no, loto_keys, pid_pdf, override, remark, prepare, verify, approve

    def clear_all_entries():
        pdf1.clear_file_name()
        ovrd.clear_file_name()
        for instance in input_field_dropdown.instances:
            instance.text.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()    
        
        for instance in input_field_title.instances:
            instance.E1.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()
        
        for instance in input_field_numeric.instances:
            instance.E1.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()
        
        for instance in input_field_date.instances:
            instance.E1.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()

        for instance in input_field_telephone.instances:
            instance.E1.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()
        
        for instance in input_field_remark.instances:
            instance.text_widget.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()
    
    button1 = ttk.Button(new_loto_GUI, text="CLEAR", style="Custom2.TButton",command=clear_all_entries)
    button1.place(x=16*scaling_factor,y=button_y*scaling_factor)
    button2 = ttk.Button(frame3, text="SUBMIT", style="Custom2.TButton",command=savetodb)
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE (X)", style="Custom2.TButton",command=new_loto_GUI.destroy)
    # button3 = ttk.Button(frame3, text="CLOSE (X)", style="Custom2.TButton",command=copytofolder)
    button3.pack(side=RIGHT)

    new_loto_GUI.mainloop()

def create_approve_entry(new_loto_GUI, topic_x, entry_2, default_text = 'ex.Kritsakon.P', toggle_var = True, fg='grey'):
    v_approve = StringVar()
    E14 = input_field_dropdown(GUI=new_loto_GUI,label='Approve by:',options=sectionmgr_list,textvariable=v_approve,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E14.place(x=topic_x,y=entry_2[2])
    return v_approve

def create_approve_entry_for_new_loto(new_loto_GUI, topic_x, entry_2, default_text = 'ex.Kritsakon.P', toggle_var = True, fg='grey'):
    v_approve = StringVar()
    E14 = input_field_dropdown_linebreak(GUI=new_loto_GUI,label='Approve by:',options=sectionmgr_list,textvariable=v_approve,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E14.place(x=topic_x,y=entry_2[2])
    return v_approve, E14  

def create_verify_entry(new_loto_GUI, topic_x, entry_2, default_text = 'ex.Boonchoo.J', toggle_var = True, fg='grey'):
    v_verify = StringVar()
    E13 = input_field_dropdown(GUI=new_loto_GUI,label='Verify by:',options=lomember_list,textvariable=v_verify,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E13.place(x=topic_x,y=entry_2[1])
    return v_verify

def create_prepare_entry(new_loto_GUI, topic_x, entry_2 , default_text = 'ex.Thanayod.W', toggle_var = True, fg='grey'):
    v_prepare = StringVar()
    E12 = input_field_dropdown(GUI=new_loto_GUI,label='Prepare by:',options=lomember_list,textvariable=v_prepare,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E12.place(x=topic_x,y=entry_2[0])
    return v_prepare

def create_remark_entry(new_loto_GUI, entry_1, default_text = "***Remark entry***", toggle_var = True, fg='grey'):
    label4 = ttk.Label(new_loto_GUI,text='Remark:',style="label2.TLabel")
    label4.place(x=40*scaling_factor,y=entry_1[11])
    v_remark = StringVar()
    input_field_remark(master=new_loto_GUI,font=FONT7,scaling_factor=scaling_factor,toggle_var=toggle_var,textvariable=v_remark,
                    placeholder=default_text,y_position=entry_1[11],fg=fg)      
    return v_remark

def create_remark_entry_for_update_widget(new_loto_GUI, entry_1, default_text = "***Remark entry***", toggle_var = True, fg='grey'):
    label4 = ttk.Label(new_loto_GUI,text='Remark:',style="label2.TLabel")
    label4.place(x=40*scaling_factor,y=entry_1[11])
    v_remark = StringVar()
    text_remark = input_field_remark_click_toplevel(master=new_loto_GUI,font=FONT7,scaling_factor=scaling_factor,toggle_var=toggle_var,textvariable=v_remark,
                    placeholder=default_text,y_position=entry_1[11],fg=fg)      
    return text_remark

def create_override_entry(new_loto_GUI, entry_1):
    v_override = StringVar()
    ovrd = input_field_pdf(GUI=new_loto_GUI,label_text='Override list:',x_pos=int(40*scaling_factor),y_pos=entry_1[10]+int(scaling_factor),textvariable=v_override)
    ovrd.place(x=int(40*scaling_factor),y=entry_1[10])
    return v_override,ovrd

# FUNCTION: To show Override list File in work detail when double click in Overview or Pending tab
def create_overide_show(new_loto_GUI, entry_1,ovrd_url):
    ovrd_place = pdf_show(GUI=new_loto_GUI,labeltext='Override list:',x_pos=int(40*scaling_factor),y_pos=entry_1[10],textvariable=ovrd_url)
    ovrd_place.place(x=int(40*scaling_factor),y=entry_1[10])
    return ovrd_place

def create_pdf_entry(new_loto_GUI, entry_1):
    v_pid_pdf = StringVar()
    pdf1 = input_field_pdf(GUI=new_loto_GUI,label_text='P&ID Markup:',x_pos=int(40*scaling_factor),y_pos=entry_1[9]+int(2*scaling_factor),textvariable=v_pid_pdf)
    # pdf1 location for clear file name
    pdf1.place(x=int(40*scaling_factor),y=entry_1[9])
    return v_pid_pdf,pdf1
    
# FUNCTION: To show PDF File in work detail when double click in Overview or Pending tab
def create_pdf_show(new_loto_GUI, entry_1,pdf_url):
    pdf_place = pdf_show(GUI=new_loto_GUI,labeltext='P&ID Markup:',x_pos=int(40*scaling_factor),y_pos=entry_1[9],textvariable=pdf_url)
    pdf_place.place(x=int(40*scaling_factor),y=entry_1[9])
    return pdf_place

def create_total_lock_keys_entry(new_loto_GUI, topic_x, entry_1, default_text='5', toggle_var = True, fg='grey'):
    v_loto_keys = StringVar()
    E11 = input_field_numeric(GUI=new_loto_GUI,label='Total lock keys:',textvariable=v_loto_keys,default_text=default_text,toggle_var=toggle_var,fg=fg)
    E11.place(x=topic_x,y=entry_1[8])
    return v_loto_keys

def create_loto_entry(new_loto_GUI, topic_x, entry_1, default_text='10', toggle_var = True, fg='grey'):
    v_loto_no = StringVar()
    E10 = input_field_numeric(GUI=new_loto_GUI,label= 'Lock box No:',textvariable=v_loto_no,default_text=default_text,toggle_var=toggle_var,fg=fg)
    E10.place(x=topic_x,y=entry_1[7])
    return v_loto_no

def create_lock_date_entry(new_loto_GUI, topic_x, entry_1, default_text = date_str(1), toggle_var = True, fg='grey'):
    v_lock_date = StringVar()
    E8 = input_field_date(GUI=new_loto_GUI,label='Lock date:',textvariable=v_lock_date,placeholder=default_text,toggle_var=toggle_var,fg=fg)
    E8.place(x=topic_x,y=entry_1[6])
    return v_lock_date

def create_equipment_entry(new_loto_GUI, topic_x, entry_1, default_text = 'Select Machine or Equipment list', toggle_var = True, fg='grey'):
    v_equipment = StringVar()
    E7 = input_field_dropdown(GUI=new_loto_GUI,label='Machine/Equipment:',options=machine_list,textvariable=v_equipment,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E7.place(x=topic_x,y=entry_1[5])
    return v_equipment

def create_working_area_entry(new_loto_GUI, topic_x, entry_1, default_text = 'Select Area list', toggle_var = True, fg='grey'):
    v_area = StringVar()
    E6 = input_field_dropdown(GUI=new_loto_GUI,label='Working area:',textvariable=v_area,options=area_list,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E6.place(x=topic_x,y=entry_1[4])
    return v_area

def create_telephone_entry(new_loto_GUI, topic_x, entry_1, default_text = '091-234-5678', toggle_var = True, fg='grey'):
    v_telephone = StringVar()
    E5 = input_field_telephone(GUI=new_loto_GUI,label='Telephone no:',textvariable=v_telephone,default_text=default_text,toggle_var=toggle_var,fg=fg)
    E5.place(x=topic_x,y=entry_1[3])
    return v_telephone

def create_owner_entry(new_loto_GUI, topic_x, entry_1, default_text = 'Select Owner list', toggle_var = True, fg='grey'):
    v_owner = StringVar()
    E3 = input_field_dropdown(GUI=new_loto_GUI,label='Owner:',options=owner_list,textvariable=v_owner,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E3.place(x=topic_x,y=entry_1[2])
    return v_owner

def create_incharge_entry(new_loto_GUI, topic_x, entry_1, default_text = 'Select Department list', toggle_var = True, fg='grey'):
    v_department = StringVar()
    E2 = input_field_dropdown(GUI=new_loto_GUI,label='In charge by:',textvariable=v_department,options=incharge_list,
            default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E2.place(x=topic_x,y=entry_1[1])
    return v_department

def create_work_title_entry(new_loto_GUI, topic_x, entry_1, default_text = 'Isolate HP Pump A for Overhaul', toggle_var = True, fg='grey'):
    v_work_title = StringVar()
    E1 = input_field_title(GUI=new_loto_GUI,label='Work Title:',textvariable=v_work_title,placeholder=default_text,toggle_var=toggle_var,fg=fg)
    E1.place(x=topic_x,y=entry_1[0])
    return v_work_title

def create_work_title_show(new_loto_GUI, topic_x, entry_1, open_folder, default_text = 'Isolate HP Pump A for Overhaul',
                            toggle_var = True, fg='grey'):
    v_work_title = StringVar()
    E1 = input_field_title_for_show(GUI=new_loto_GUI,label='Work Title:',textvariable=v_work_title,
                    placeholder=default_text,open_folder=open_folder,toggle_var=toggle_var,fg=fg)
    E1.place(x=topic_x,y=entry_1[0])
    return v_work_title

def configure_label_style():
    style.configure('label1.TLabel',background="#dcdad5", foreground='#4f4f4f', font=FONT5)
    style.configure('label2.TLabel',background="#dcdad5", foreground='#4f4f4f', font=FONT6)
    style.configure("TEntry",padding=3)

def create_new_window(title_name):
    # title_name= New LOTO work
    new_loto_GUI = tk.Toplevel(background='#dcdad5')
    NewLoto_x = int(480*scaling_factor)
    NewLoto_y = int(550*scaling_factor)
    win2size = center_windows(NewLoto_x,NewLoto_y)
    new_loto_GUI.geometry(win2size)
    new_loto_GUI.title(title_name) 
    new_loto_GUI.resizable(False, False)
    return new_loto_GUI,NewLoto_x,NewLoto_y

# CONFIGURE: LABEL1
style.configure('Custom1.TLabel',background="#dcdad5", foreground='#4f4f4f', font=FONT3)

# CREATE: Label under the table
label1 = ttk.Label(frame2, text=f"Total active LOTO : {total_loto}",style='Custom1.TLabel')
label1.pack(side='right')
date_today = date_str(1)
label3 = ttk.Label(frame2,text=f"Today : {date_today}",style='Custom1.TLabel')
label3.pack(side='left')
label4 = ttk.Label(frame3,text=f"V.{rev}",style='Custom1.TLabel')
label4.pack()
refresh_icon = create_resized_image('refresh2.png',int(15*scaling_factor),int(15*scaling_factor))
refresh_but = tk.Button(frame4,image=refresh_icon,command=refresh_treeview,
                                bg="#dcdad5",             # Background color
                                activebackground="#e0e0e0",# Background color when clicked or hovered
                                borderwidth=0,            # Width of the button's border
                                relief="raised",          # Type of border effect (flat, raised, sunken, groove, ridge)
                                highlightthickness=2,      # Thickness of highlight border when focused
                                highlightbackground="#cccccc",  # Color of the highlight border
                                highlightcolor="#ff0000",  # Color of the highlight border when the button is focused
                                )
refresh_but.pack()


# CONFIGURE: LABEL2
style.configure('Custom2.TLabel',background="#dcdad5", foreground='#4f4f4f', font=FONT4)

# CREATE: Label upper the table
label2 = ttk.Label(frame0, text="LOTO List",style='Custom2.TLabel')
label2.place(x=17*scaling_factor, y=16*scaling_factor)

# CREATE: TABLE CREATE
header = ['LOTO No.','Work Description','Incharge','Effective date','Status']
header_w1 = int(90*scaling_factor)
header_w2 = int(440*scaling_factor)
header_w3 = int(130*scaling_factor)
header_w4 = int(130*scaling_factor)
header_w5 = int(95*scaling_factor)

headerw = [header_w1,header_w2,header_w3,header_w4,header_w5]
loto_datalist = ttk.Treeview(frame1,columns=header,show='headings',height=10)
loto_datalist.pack(fill='y',expand=True)
loto_datalist.bind("<Double-1>", on_row_double_click_overview)

# CONFIGURE: TABLE CONFIGURE
style = ttk.Style()
style.configure('Treeview.Heading',padding=(5*scaling_factor,5*scaling_factor),font=FONT2,foreground='#4f4f4f')
style.configure('Treeview',rowheight=int(23*scaling_factor),font = FONT3)
loto_datalist.tag_configure('evenrow', background="#ffffff")
loto_datalist.tag_configure('oddrow', background="#F1F0E8")

# CREATE: HEADER TABLE CREATE
for h,w in zip(header,headerw):
    loto_datalist.heading(h,text=h, command=lambda _col=h: treeview_sort_column(loto_datalist, _col, False))
    loto_datalist.column(h,width=w,anchor='center')

# FUNCTION: Sort value by click at the Column header
def treeview_sort_column(treeview, col, reverse):
    # Get data from the Treeview
    data = [(treeview.set(child, col), child) for child in treeview.get_children('')]

    if col == 'Effective date':
        data.sort(key=lambda t: datetime.strptime(t[0], "%d/%m/%y"), reverse=reverse)
    else:

    # Sort data numerically or alphabetically
        try:
            data.sort(key=lambda t: float(t[0]), reverse=reverse)  # Sort by numbers
        except ValueError:
            data.sort(key=lambda t: t[0], reverse=reverse)  # Sort by strings

    # Rearrange rows in sorted order
    for index, (val, item) in enumerate(data):
        treeview.move(item, '', index)

    # Reverse the sort direction for the next click
    treeview.heading(col, command=lambda: treeview_sort_column(treeview, col, not reverse))

    # Update row colors for alternating background
    for index, item in enumerate(treeview.get_children('')):
        tag = 'evenrow' if index % 2 == 0 else 'oddrow'
        treeview.item(item, tags=(tag,))

# CREATE: COLUMN WIDTH DISABLE RESIZABLE
def disable_column_resize(event):
    if loto_datalist.identify_region(event.x, event.y) == "separator":
        return "break"  # This stops the event from propagating further
loto_datalist.bind('<Button-1>', disable_column_resize)

# CREATE: Button "New" and "Print"
button1 = ttk.Button(frame0, text="NEW", style="Custom1.TButton",cursor='hand2',command=create_new_loto_toplevel)
button1.place(x=925*scaling_factor,y=50*scaling_factor)
button2 = ttk.Button(frame0, text="PRINT", style="Custom1.TButton",cursor='hand2',command=lambda: save_table_as_pdf(loto_datalist))
button2.place(x=925*scaling_factor,y=93*scaling_factor)


################################################# OVERVIEW TAB ################################################# 

#==============================================================================================================#

################################################# PENDING TAB ################################################## 
# CREATE: the first tab (PENDING) and add a frame to it
pending_page = ttk.Frame(notebook)
notebook.add(pending_page, text="Pending")

# CREATE: Place frame0 and frame1 to Overview tab
## Overivew frame
frame0_p = tk.Frame(pending_page, background="#dcdad5", borderwidth=1, relief="flat")
frame0_p.place(x=0, y=0, width=int(1045*scaling_factor), height=int(620*scaling_factor))

## Top frame
frame1_p = tk.Frame(pending_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#b4b4b4", highlightthickness=1)
frame1_p.place(x=int(20*scaling_factor), y=int(50*scaling_factor), width=int(1007*scaling_factor), height=int(520*scaling_factor))

## Bottom frame
frame2_p = tk.Frame(pending_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#b4b4b4", highlightthickness=2)
frame2_p.place(x=int(20*scaling_factor), y=int(570*scaling_factor), width=int(1007*scaling_factor), height=int(25*scaling_factor))

## 3rd and 4th frame
frame3_p = tk.Frame(pending_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#dcdad5", highlightthickness=2)
frame3_p.place(x=int(20*scaling_factor), y=int(600*scaling_factor), width=int(60*scaling_factor), height=int(25*scaling_factor))

frame4_p = tk.Frame(pending_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#dcdad5", highlightthickness=2)
frame4_p.place(x=int(1025*scaling_factor), y=int(605*scaling_factor), width=int(25*scaling_factor), height=int(25*scaling_factor))

# CREATE: Label
label2_p = ttk.Label(frame0_p, text="Pending List",style='Custom2.TLabel')
label2_p.place(x=17*scaling_factor, y=16*scaling_factor)

# CREATE: Label under the table
label1_p = ttk.Label(frame2_p, text=f"Total active LOTO : {total_loto_p}",style='Custom1.TLabel')
label1_p.pack(side='right')
date_today = date_str(1)
label3_p = ttk.Label(frame2_p,text=f"Today : {date_today}",style='Custom1.TLabel')
label3_p.pack(side='left')
label4_p = ttk.Label(frame3_p,text=f"V.{rev}",style='Custom1.TLabel')
label4_p.pack()
refresh_icon_p = create_resized_image('refresh2.png',int(15*scaling_factor),int(15*scaling_factor))
refresh_but_p = tk.Button(frame4_p,image=refresh_icon_p,command=refresh_treeview,
                                bg="#dcdad5",             # Background color
                                activebackground="#e0e0e0",# Background color when clicked or hovered
                                borderwidth=0,            # Width of the button's border
                                relief="raised",          # Type of border effect (flat, raised, sunken, groove, ridge)
                                highlightthickness=2,      # Thickness of highlight border when focused
                                highlightbackground="#cccccc",  # Color of the highlight border
                                highlightcolor="#ff0000",  # Color of the highlight border when the button is focused
                                )
refresh_but_p.pack()

# CREATE: TABLE
header_p = ['LOTO No.','Work Description','Department','Owner','Prepared by','Created date','Status']
header_p_w1 = int(80*scaling_factor)
header_p_w2 = int(385*scaling_factor)
header_p_w3 = int(115*scaling_factor)
header_p_w4 = int(105*scaling_factor)
header_p_w5 = int(115*scaling_factor)
header_p_w6 = int(100*scaling_factor)
header_p_w7 = int(100*scaling_factor)
headerw_p = [header_p_w1,header_p_w2,header_p_w3,header_p_w4,header_p_w5,header_p_w6,header_p_w7]
loto_datalist_p = ttk.Treeview(frame1_p,columns=header_p,show='headings',height=10)
loto_datalist_p.pack(fill='y',expand=True)
loto_datalist_p.bind("<Double-1>", on_row_double_click_pending)

# CONFIGURE: TABLE CONFIGURE
style = ttk.Style()
style.configure('Treeview.Heading',padding=(5*scaling_factor,5*scaling_factor),font=FONT2,foreground='#4f4f4f')
style.configure('Treeview',rowheight=int(23*scaling_factor),font = FONT3)
loto_datalist_p.tag_configure('evenrow', background="#ffffff")
loto_datalist_p.tag_configure('oddrow', background="#F1F0E8")

# CREATE: HEADER TABLE CREATE
for h,w in zip(header_p,headerw_p):
    loto_datalist_p.heading(h,text=h, command=lambda _col=h: treeview_sort_column(loto_datalist_p, _col, False))
    loto_datalist_p.column(h,width=w,anchor='center')

# FUNCTION: Sort value by click at the Column header

# CREATE: COLUMN WIDTH DISABLE RESIZABLE
def disable_column_resize(event):
    if loto_datalist_p.identify_region(event.x, event.y) == "separator":
        return "break"  # This stops the event from propagating further
loto_datalist_p.bind('<Button-1>', disable_column_resize)


################################################# PENDING TAB ################################################## 

#==============================================================================================================#

################################################# COMPLETED TAB ################################################## 
# CREATE: the first tab (Completed) and add a frame to it
completed_page = ttk.Frame(notebook)
notebook.add(completed_page, text="Completed")

# CREATE: Place frame0 and frame1 to Completed tab
## Completed frame
frame0_c = tk.Frame(completed_page, background="#dcdad5", borderwidth=1, relief="flat")
frame0_c.place(x=0, y=0, width=int(1045*scaling_factor), height=int(620*scaling_factor))

## Top frame
frame1_c = tk.Frame(completed_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#b4b4b4", highlightthickness=1)
frame1_c.place(x=int(20*scaling_factor), y=int(50*scaling_factor), width=int(1007*scaling_factor), height=int(520*scaling_factor))

## Bottom frame
frame2_c = tk.Frame(completed_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#b4b4b4", highlightthickness=2)
frame2_c.place(x=int(20*scaling_factor), y=int(570*scaling_factor), width=int(1007*scaling_factor), height=int(25*scaling_factor))

## 3rd and 4th frame
frame3_c = tk.Frame(completed_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#dcdad5", highlightthickness=2)
frame3_c.place(x=int(20*scaling_factor), y=int(600*scaling_factor), width=int(60*scaling_factor), height=int(25*scaling_factor))

frame4_c = tk.Frame(completed_page, background="#dcdad5", borderwidth=1, relief="flat",highlightbackground="#dcdad5", highlightthickness=2)
frame4_c.place(x=int(1025*scaling_factor), y=int(605*scaling_factor), width=int(25*scaling_factor), height=int(25*scaling_factor))

# CREATE: Label
label2_c = ttk.Label(frame0_c, text="Completed List",style='Custom2.TLabel')
label2_c.place(x=17*scaling_factor, y=16*scaling_factor)

# CREATE: Label under the table
label1_c = ttk.Label(frame2_c, text=f"Total LOTO : {total_loto_c}",style='Custom1.TLabel')
label1_c.pack(side='right')
date_today = date_str(1)
label3_c = ttk.Label(frame2_c,text=f"Today : {date_today}",style='Custom1.TLabel')
label3_c.pack(side='left')
label4_c = ttk.Label(frame3_c,text=f"V.{rev}",style='Custom1.TLabel')
label4_c.pack()
refresh_icon_c = create_resized_image('refresh2.png',int(15*scaling_factor),int(15*scaling_factor))
refresh_but_c = tk.Button(frame4_c,image=refresh_icon_c,command=refresh_treeview,
                                bg="#dcdad5",             # Background color
                                activebackground="#e0e0e0",# Background color when clicked or hovered
                                borderwidth=0,            # Width of the button's border
                                relief="raised",          # Type of border effect (flat, raised, sunken, groove, ridge)
                                highlightthickness=2,      # Thickness of highlight border when focused
                                highlightbackground="#cccccc",  # Color of the highlight border
                                highlightcolor="#ff0000",  # Color of the highlight border when the button is focused
                                )
refresh_but_c.pack()

# CREATE: TABLE
header_c = ['LOTO No.','Work Description','Incharge','Effective date','End date','Total days','Status']
header_c_w1 = int(85*scaling_factor)
header_c_w2 = int(370*scaling_factor)
header_c_w3 = int(115*scaling_factor)
header_c_w4 = int(108*scaling_factor)
header_c_w5 = int(108*scaling_factor)
header_c_w6 = int(108*scaling_factor)
header_c_w7 = int(108*scaling_factor)

headerw_c = [header_c_w1,header_c_w2,header_c_w3,header_c_w4,header_c_w5,header_c_w6,header_c_w7]
loto_datalist_c = ttk.Treeview(frame1_c,columns=header_c,show='headings',height=10)
loto_datalist_c.pack(fill='y',expand=True)
loto_datalist_c.bind("<Double-1>", on_row_double_click_completed)

# CONFIGURE: TABLE CONFIGURE
style = ttk.Style()
style.configure('Treeview.Heading',padding=(5*scaling_factor,5*scaling_factor),font=FONT2,foreground='#4f4f4f')
style.configure('Treeview',rowheight=int(23*scaling_factor),font = FONT3)
loto_datalist_c.tag_configure('evenrow', background="#ffffff")
loto_datalist_c.tag_configure('oddrow', background="#F1F0E8")


# CREATE: HEADER TABLE CREATE
for h,w in zip(header_c,headerw_c):
    loto_datalist_c.heading(h,text=h)
    loto_datalist_c.column(h,width=w,anchor='center')

# CREATE: COLUMN WIDTH DISABLE RESIZABLE
def disable_column_resize(event):
    if loto_datalist_c.identify_region(event.x, event.y) == "separator":
        return "break"  # This stops the event from propagating further
loto_datalist_c.bind('<Button-1>', disable_column_resize)


################################################# COMPLETED TAB ################################################## 

update_table_overview()
update_table_pending()
update_table_completed()
root.mainloop()
