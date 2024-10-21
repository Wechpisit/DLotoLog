import tkinter as tk
import webbrowser
import os
import shutil
import datetime
import ast
import subprocess
from tkinter import ttk,filedialog,PhotoImage
from tkinter import *
from tkinter import messagebox
from tkinter.font import Font
from datetime import datetime
from tkcalendar import Calendar, DateEntry 
from tkinter import font as tkFont
from DB_loto import *
from PIL import Image, ImageTk
import ctypes
from ctypes import windll
ctypes.windll.shcore.SetProcessDpiAwareness(1)
import sqlite3



# DESCRIPTION: Select the Folder to create DB
directory =  "C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/LNG Project/2024/2.LOTO Project"
db_name = "loto_data.db"
database_path = os.path.join(directory,db_name)

# DESCRIPTION: Create CONNECTION to the DB (sqlite3-)atabase
conn = sqlite3.connect(database_path)

# DESCRIPTION: Create CURSOR for do database operation
c = conn.cursor()

# DESCRIPTION: Create table loto_overview
c.execute(""" CREATE TABLE IF NOT EXISTS loto_overview (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    loto_no TEXT,
                    work_title TEXT,
                    owner TEXT,
                    lock_date TEXT,
                    status TEXT)""")

# DESCRIPTION: Insert data to loto_overview table
def insert_data(loto_no,work_title,owner,telephone):
    # CREATE
    with conn:
        command =  'INSERT INTO loto_overview VALUES (?,?,?,?,?,?)'
        c.execute(command,(None,loto_no,work_title,owner,telephone,'new'))
    conn.commit() # Save database

# def testins():
    ################################ DESCRIPTION: TEST INSERT DATA
    insert_data('1','Isolate Valve Tie-in to GSP#7','Project','45259')
    insert_data('21','Isolate for stopping leak of portable water supply to EWS','MT.Mech','45372')
    insert_data('45','Isolate manual valve chlorine dosing bay D','MT.Mech','45415')
    insert_data('18','Isolating for investigation Junction box In-tank pump 3B','MT.Mech','45461')
    insert_data('23','Isolate CWG for Glass house 2','Project','45500')
    insert_data('26','Drain HP Pump E for overhaul work','LO','45512')
    insert_data('29','Isolate LNG-1128 for overhaul HP Pump E','LO','45515')
    ################################ DESCRIPTION: TEST INSERT DATA

# DESCRIPTION: Feth data from loto_overview table to Show
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
        WHERE status = 'Waiting' OR status = 'Rejected'
        """
        c.execute(command)
        result = c.fetchall()
    return result

# DESCRIPTION: Create DB loto_new
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

# DESCRIPTION: Insert data to loto_new DB
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

# DESCRIPTION: Feth data from loto_new to loto_overview for show
def transfer_data():
    with conn:
        # command0 = """DELETE FROM loto_overview"""
        # c.execute(command0)
        command = """
        INSERT INTO loto_overview (loto_no, work_title, owner, lock_date, status) 
        SELECT new_loto_no, new_work_title, new_incharge_dept, new_lock_date, status
        FROM loto_new 
        WHERE status IN ('Active', 'Onsite')
        AND (new_loto_no, new_work_title, new_incharge_dept, new_lock_date) NOT IN (
        SELECT loto_no, work_title, owner, lock_date FROM loto_overview)
        """
        c.execute(command)
        print("data transfered")
    conn.commit()

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

def confirm_button_approve(GUI4, GUI3, v_loto_no, v_work_title, v_lock_date, v_remark, v_approve,state,refresh_callback=None):
    # print(f'v_loto_no: {v_loto_no}')
    # print(f'v_remark: {v_remark}')
    remark_value0 = v_remark.get()
    remark_value = date_str(3) + '\n' + remark_value0
    approve_value = v_approve.get()
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
            if current_status == "Waiting" or current_status == "Rejected":
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
    transfer_data()

    if refresh_callback:
        refresh_callback()

    print("GUI DESTROY")
    GUI4.destroy()
    GUI3.destroy()

def confirm_button_update(GUI4, GUI3,v_loto_no, v_work_title, v_lock_date, v_pdf_update, v_override_update, v_remark0,v_update0,state,refresh_callback=None):
    remark_value0 = v_remark0.get()
    v_update0 = v_update0.get()
    remark_value = date_str(3) + ' update by '+ v_update0 + '\n' + remark_value0
    pdf_value = v_pdf_update.get()
    override_value = v_override_update.get()
    
    print('working on the confirm_button_update')
    print(f'v_loto_no: {v_loto_no}')
    print(f'v_work_title: {v_work_title}')
    print(f'v_lock_date: {v_lock_date}')
    print(f'remark_value: {remark_value}')
    with conn:
        command_fetch = """
        SELECT new_pid_pdf, new_override_list, new_remark
        FROM loto_new
        WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
        """
        # print('working on the fetch')
        c.execute(command_fetch, (v_loto_no, v_work_title, v_lock_date))
        result = c.fetchone()
        print(f'result: {result}')

        if result:
            # Extract the data
            existing_pdf = result[0]  # This is the existing pdf url
            existing_override = result[1]  # This is the existing override url
            existing_remark = result[2]  # This is the existing existing_remark
  
            # 1. Add the new remark after the old one (on a new line)
            updated_remark = f"{existing_remark}\n{remark_value}" if existing_remark else remark_value
            # 2. Replace the old pdf with the new one
            if pdf_value:
                updated_pdf = pdf_value
            else:
                updated_pdf = existing_pdf
            # 3. Replace the old override with the new one
            if override_value:
                updated_override = override_value
            else:
                updated_override = existing_override

            print(f'updated_pdf: {updated_pdf}')
            print(f'updated_override: {updated_override}')

            # Update the record in the database
            command_update = """
            UPDATE loto_new
            SET new_pid_pdf = ?, new_override_list = ?, new_remark = ?
            WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
            """
            c.execute(command_update, (updated_pdf, updated_override, updated_remark, v_loto_no, v_work_title, v_lock_date))
            conn.commit()
        

def date_str(select):
    a = datetime.now()
    day_today = a.strftime("%d")
    month_today = a.strftime("%m")
    year_today = a.strftime("%y")
    date_today = day_today+'/'+month_today+'/'+year_today
    remark_date = date_today+' '+a.strftime("%H:%M")
    if select == 1:
        return date_today
    elif select == 3:
        return remark_date



# CREATE: the main application window
root = tk.Tk()
root.title("LOTO-LOT1")
root.resizable(False, False)

# CONFIGURE: Auto adjust size of windows program
# Function to get the scaling factor of the system
def get_scaling_factor():
    user32 = ctypes.windll.user32
    # Gets the DPI from the system; assuming 96 dpi is 100%
    dpi = user32.GetDpiForSystem()
    return dpi / 96  # Scaling factor

# Get the scaling factor
scaling_factor = get_scaling_factor()

# Define base dimensions (for 100% scaling)
base_width = 1050
base_height = 650

# Adjust dimensions based on the current scaling factor
adjusted_width = int(base_width * scaling_factor)
adjusted_height = int(base_height * scaling_factor)

# Folder location
folder_path = 'C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/LNG Project/2024/2.LOTO Project'

# Function to Adjust position of GUI Window
def center_windows(w,h):
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2) - 30
    return f'{w}x{h}+{x:.0f}+{y:.0f}'

win1size = center_windows(adjusted_width,adjusted_height)
root.geometry(win1size)

# Function Date string
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

# CONFIGURE: tk.Text INPUT 
def on_focus_in(event):
        event.widget.config(highlightbackground="#5f87aa", highlightcolor="#5f87aa", highlightthickness=2)
def on_focus_out(event):
        event.widget.config(highlightbackground="grey", highlightcolor="grey", highlightthickness=1)
def focus_next_widget(event):
    """Move focus to the next widget in the tab order."""
    event.widget.tk_focusNext().focus()
    return "break"

# CONFIGURE: Icon program
def set_window_icon(root):
    icon_path = Image.open("IconProgram1.ico")
    photo = ImageTk.PhotoImage(icon_path)
    root.iconphoto(True,photo)

set_window_icon(root)

# CONFIGURE: Resize image
def create_resized_image(path, width, height):
        # Load the image with Pillow
        original_image = Image.open(path)
        # Resize the image
        resized_image = original_image.resize((width, height))
        # Convert to PhotoImage
        return ImageTk.PhotoImage(resized_image)

# CONFIGURE: Font
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

# CONFIGURE: Set the theme to "clam" 
style = ttk.Style(root)
style.theme_use("clam")

# CONFIGURE: Styles for notebook tabs
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

# CREATE: a ttk notebook for tabs
notebook = ttk.Notebook(root, style="Custom1.TNotebook")
notebook.pack(expand=True, fill="both")

# CONFIGURE: Styles for BUTTON
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

# CONFIGURE: Style for Combobox
style.configure("Custom.TCombobox", arrowsize=25) # Adjust the size of the dropdown arrow

# FUNCTION: Show message box
def show_message(title, message):
    messagebox.showinfo(title, message)

# FUNCTION: Set focus on a specific tab
def set_focus_on_tab(index):
    notebook.select(index)

# CONFIGURE: LIST
def list_setup():
    incharge_list = ['MT.Mech','MT.Ins','MT.Elec','ED.Mech','ED.Ins','ED.Elec',
                 'ED.Process','Project','LO.','ED.','PI',
]

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
              'Chatchaiwat.R','Nawin.S','Wichanath.P','Thitapa.C','Warut.T'
]

    sectionmgr_list = ['Yutasart.P','Kritsakon.P','Piyapong.P','Sarayut.K','Dumrongsak.J','Kittiwat.Ro',
]

    lomember_list = ['Parinya.Y','Kritsakon.P','Sarawut.S','Yutasart.P','Sarayut.K',
                 'Tanisorn.S','Piyapong.P','Weerayut.P','Rachanon.Y','Artit.K',
                 'Dumrongsak.J','Mongkol.S','Kittiwat.Ro','Weerawat.N','Naret.N',
                 'Suttipat.V','Jantakan.P','Phuradech.M','Wechpisit.S','Palathip.S',
                 'Koragoch.T','Saranya.W','Suphachot.P','Jakkrit.S','Wuttipat.W',
                 'Boonchoo.J','Thanasak.S','Nopphakao.C','Thanayod.W','Sittichok.C',
                 'Komtanut.C','Chinnakrit.M','Thanadon.T','Veeraphat.K','Nawin.S'
]

    area_list = ['HP Pump','BOG Compressor','SOG Compressor','Recondenser','BOG Suction drum',
             'Truck load','LNG Tank','Drain pump','ORV','IA / N2 ','Sanitary','Metering',
             'Chlorination','Seawater pump','Seawater intake','Jetty Berth1','Jetty Berth2',
             'Jetty Berth3','LNG Sampling','Firewater pump','ORC','GTG','WHRU','IFV',
             'CWG Pump','IPG IA','Admin building','Canteen building','GIS I','GIS II',
             'Fire station','Maintenance workshop','LAB','Warehouse','AIB Building',
             'CCR Building','Main Substation','IPG Substation','JCR Building',
             'Jetty Substation','Truck load admin','Truck load control room','Potable water',
             'Service water'
]

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
                'Potable water pump A','Potable water pump B',
]

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
              'Nawin.S': 'nawin.s@pttlng.com',
}
    
    return incharge_list,owner_list,sectionmgr_list,lomember_list,area_list,machine_list, email_list

incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list = list_setup()

# CREATE: Function fetch data from DB and Refresh Table
total_loto = 0
def update_table_overview():
    global total_loto
    total_loto = 0
    loto_datalist.delete(*loto_datalist.get_children())
    transfer_data()
    data = view_data()
    for index, (d) in enumerate(data):
        d = list(d)
        del d[0]
        status = d[4]
        tag = 'evenrow' if index % 2 == 0 else 'oddrow'
        if status == 'Active' or status == 'Onsite':
            loto_datalist.insert('', 'end', values=d, tags=(tag,))
            total_loto += 1
    label1.config(text=f"Total active LOTO : {total_loto}")

def refresh_treeview():
    print("Refreshing treeview")
    update_table_overview()
    update_table_pending()

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
    # Get the selected item and its values
    selected_item = selected_item[0]
    item_values = table_select.item(selected_item, "values")
    v1 = item_values[0]
    v2 = item_values[1]
    v3 = item_values[3]
    data_to_popup = fetch_data_from_loto_new(v1,v2,v3)
    data_to_popup = list(data_to_popup[0])

    # Create a new Toplevel window
    GUI3,NewLoto_x,NewLoto_y = create_new_window('Detail')

    # CONFIGURE: label1 (Main)
    configure_label_style()

    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(GUI3,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(GUI3, text="Work detail",style="label1.TLabel")
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
    frame3 = tk.Frame(GUI3, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(265*scaling_factor), y=int(495*scaling_factor), width=200*scaling_factor, height=40*scaling_factor)

    ## CREATE: BUTTON
    button_y = 501
    button1 = ttk.Button(GUI3, text="COMPLETED", style="Custom2.TButton")
    button1.place(x=16*scaling_factor,y=button_y*scaling_factor)
    button2 = ttk.Button(frame3, text="UPDATE", style="Custom2.TButton",command=lambda: update_button(GUI3,data_to_popup[9],data_to_popup[2],
                                                                                                        data_to_popup[8]))
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton",command=lambda: reject_button(GUI3,data_to_popup[9],data_to_popup[2],
                                                                                                        data_to_popup[8]))
    button3.pack(side=RIGHT)

     #### FUNCTION: Loop for indicate hieght each row
    topic_x = int(30*scaling_factor)
    entry_1 = [int(40*scaling_factor)]
    current_ent = 0
    for i in range(1,12):
        current_ent = entry_1[i-1]+int(27*scaling_factor)
        entry_1.append(current_ent)

    # Create entries
    create_work_title_show(GUI3, topic_x, entry_1, default_text=data_to_popup[2], open_folder=data_to_popup[11], 
                           toggle_var=False,fg='#4f4f4f')
    create_incharge_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[3], toggle_var=False,fg='#4f4f4f')
    create_owner_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[4], toggle_var=False,fg='#4f4f4f')
    create_telephone_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[5], toggle_var=False,fg='#4f4f4f')
    create_working_area_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[6], toggle_var=False,fg='#4f4f4f')
    create_equipment_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[7], toggle_var=False,fg='#4f4f4f')
    create_lock_date_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[8], toggle_var=False,fg='#4f4f4f')
    create_loto_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[9], toggle_var=False,fg='#4f4f4f')
    create_total_lock_keys_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[10], toggle_var=False,fg='#4f4f4f')
    create_pdf_show(GUI3, entry_1, pdf_url=data_to_popup[11])
    create_overide_show(GUI3, entry_1, ovrd_url=data_to_popup[12])
    create_remark_entry(GUI3, entry_1, default_text=data_to_popup[13], toggle_var=False,fg='#4f4f4f')
    
    # FUNCTION: To open folder in work_title_show

    # Loop for indicating height of each row
    entry_2 = [int(395 * scaling_factor)]
    current_ent = 0
    for i in range(1, 3):
        current_ent = entry_2[i - 1] + int(26 * scaling_factor)
        entry_2.append(current_ent)

    # Create additional entries
    create_prepare_entry(GUI3, topic_x, entry_2, default_text=data_to_popup[14], toggle_var=False,fg='#4f4f4f')
    create_verify_entry(GUI3, topic_x, entry_2, default_text=data_to_popup[15], toggle_var=False,fg='#4f4f4f')
    create_approve_entry(GUI3, topic_x, entry_2, default_text=data_to_popup[16], toggle_var=False,fg='#4f4f4f')

    return GUI3
    GUI3.mainloop

def on_row_double_click_pending(event):
    # Get the treeview widget that triggered the event
    table_select = event.widget
    
    # Check if an item is selected in the table
    selected_item = table_select.selection()
    # Get the selected item and its values
    selected_item = selected_item[0]
    item_values = table_select.item(selected_item, "values")

    v1 = item_values[0]
    v2 = item_values[1]
    v3 = item_values[5]
    data_to_popup = fetch_data_from_loto_new(v1,v2,v3)
    data_to_popup = list(data_to_popup[0])
    # print(f'data_to_popup is : {data_to_popup}')


    # Create a new Toplevel window
    GUI3,NewLoto_x,NewLoto_y = create_new_window('Detail')

    # CONFIGURE: label1 (Main)
    configure_label_style()

    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(GUI3,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(GUI3, text="Work detail",style="label1.TLabel")
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
    frame3 = tk.Frame(GUI3, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(265*scaling_factor), y=int(495*scaling_factor), width=200*scaling_factor, height=40*scaling_factor)

    ## CREATE: BUTTON
    button2 = ttk.Button(frame3, text="APPROVE", style="Custom2.TButton",command=lambda: approve_button(GUI3,data_to_popup[9],data_to_popup[2],
                                                                                                        data_to_popup[8]))
    button2.pack(side=LEFT)

    button3 = ttk.Button(frame3, text="REJECT", style="Custom2.TButton",command=lambda: reject_button(GUI3,data_to_popup[9],data_to_popup[2],
                                                                                                        data_to_popup[8]))
    button3.pack(side=RIGHT)

     #### FUNCTION: Loop for indicate hieght each row
    topic_x = int(30*scaling_factor)
    entry_1 = [int(40*scaling_factor)]
    current_ent = 0
    for i in range(1,12):
        current_ent = entry_1[i-1]+int(27*scaling_factor)
        entry_1.append(current_ent)

    # Create entries
    create_work_title_show(GUI3, topic_x, entry_1, default_text=data_to_popup[2], open_folder=data_to_popup[11], 
                           toggle_var=False,fg='#4f4f4f')
    create_incharge_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[3], toggle_var=False,fg='#4f4f4f')
    create_owner_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[4], toggle_var=False,fg='#4f4f4f')
    # create_internal_phone_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[5], toggle_var=False,fg='#4f4f4f')
    create_telephone_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[5], toggle_var=False,fg='#4f4f4f')
    create_working_area_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[6], toggle_var=False,fg='#4f4f4f')
    create_equipment_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[7], toggle_var=False,fg='#4f4f4f')
    create_lock_date_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[8], toggle_var=False,fg='#4f4f4f')
    create_loto_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[9], toggle_var=False,fg='#4f4f4f')
    create_total_lock_keys_entry(GUI3, topic_x, entry_1, default_text=data_to_popup[10], toggle_var=False,fg='#4f4f4f')
    create_pdf_show(GUI3, entry_1, pdf_url=data_to_popup[11])
    create_overide_show(GUI3, entry_1, ovrd_url=data_to_popup[12])
    create_remark_entry(GUI3, entry_1, default_text=data_to_popup[13], toggle_var=False,fg='#4f4f4f')

    # Loop for indicating height of each row
    entry_2 = [int(395 * scaling_factor)]
    current_ent = 0
    for i in range(1, 3):
        current_ent = entry_2[i - 1] + int(26 * scaling_factor)
        entry_2.append(current_ent)

    # Create additional entries
    create_prepare_entry(GUI3, topic_x, entry_2, default_text=data_to_popup[14], toggle_var=False,fg='#4f4f4f')
    create_verify_entry(GUI3, topic_x, entry_2, default_text=data_to_popup[15], toggle_var=False,fg='#4f4f4f')
    create_approve_entry(GUI3, topic_x, entry_2, default_text=data_to_popup[16], toggle_var=False,fg='#4f4f4f')

    return GUI3
    GUI3.mainloop

def create_approve_reject_window(title_name,size_x,size_y,parent=None):
    GUI2 = tk.Toplevel(parent, background='#dcdad5')
    NewLoto_x = int(size_x*scaling_factor)
    NewLoto_y = int(size_y*scaling_factor)
    win2size = center_windows(NewLoto_x,NewLoto_y)
    GUI2.geometry(win2size)
    GUI2.title(title_name) 
    GUI2.resizable(False, False)
    return GUI2,NewLoto_x,NewLoto_y

def approve_button(parent_window, v_loto_no, v_work_title, v_lock_date):
    GUI4,NewLoto_x,NewLoto_y  = create_approve_reject_window('Approve',380,200,parent=parent_window)
    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(GUI4,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(GUI4, text="Approve detail",style="label1.TLabel")
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
    frame3 = tk.Frame(GUI4, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(NewLoto_x-(216*scaling_factor)), y=int(NewLoto_y-(45*scaling_factor)), width=200*scaling_factor, height=40*scaling_factor)
    ## CREATE: BUTTON
    button2 = ttk.Button(frame3, text="CONFIRM", style="Custom2.TButton",command=lambda: confirm_button_approve(GUI4,parent_window, v_loto_no, v_work_title, 
                                                                                                                v_lock_date, v_remark0, 
                                                                                                                v_approve0,state=True,refresh_callback=refresh_treeview))
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton",command=GUI4.destroy)
    button3.pack(side=RIGHT)
    ## CREATE: LABEL FOR REMARK
    label_remark = ttk.Label(GUI4,text='Remark:',style="label2.TLabel")
    label_remark.place(x=28*scaling_factor,y=45*scaling_factor)
    ## CREATE: REMARK ENTRY
    v_remark0 = StringVar()
    default_text = "***Remark entry***"
    approve_remark(GUI4,font=FONT7,scaling_factor=scaling_factor,textvariable=v_remark0,
                            placeholder=default_text,fg='grey',y_position=(45*scaling_factor))
    ## CREATE: APPROVE LABEL AND ENTRY
    v_approve0 = StringVar()
    default_text = "ex.Kritsakon.P"
    E14 = ET2(GUI=GUI4,label='Approve by:',options=sectionmgr_list,textvariable=v_approve0,
              default_text=default_text,scaling_factor=scaling_factor,toggle_var=True,fg='Grey',
              x_position=-34,frame_width=-90,widget_width=-39)
    E14.place(x=18*scaling_factor,y=110*scaling_factor)

def reject_button(parent_window, v_loto_no, v_work_title, v_lock_date):
    GUI5,NewLoto_x,NewLoto_y  = create_approve_reject_window('Reject',380,200,parent=parent_window)
    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(GUI5,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(GUI5, text="Reject detail",style="label1.TLabel")
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
    frame3 = tk.Frame(GUI5, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(NewLoto_x-(216*scaling_factor)), y=int(NewLoto_y-(45*scaling_factor)), width=int(200*scaling_factor), height=int(40*scaling_factor))
    ## CREATE: BUTTON
    button2 = ttk.Button(frame3, text="CONFIRM", style="Custom2.TButton",command=lambda: confirm_button_approve(GUI5,parent_window, v_loto_no, v_work_title, 
                                                                                                                v_lock_date, v_remark0, 
                                                                                                                v_approve0,state=False,refresh_callback=refresh_treeview))
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton",command=GUI5.destroy)
    button3.pack(side=RIGHT)
    ## CREATE: LABEL FOR REMARK
    label_remark = ttk.Label(GUI5,text='Remark:',style="label2.TLabel")
    label_remark.place(x=28*scaling_factor,y=45*scaling_factor)
    ## CREATE: REMARK ENTRY
    v_remark0 = StringVar()
    default_text = "***Remark entry***"
    approve_remark(GUI5,font=FONT7,scaling_factor=scaling_factor,textvariable=v_remark0,
                            placeholder=default_text,fg='grey',y_position=(45*scaling_factor))
    ## CREATE: APPROVE LABEL AND ENTRY
    v_approve0 = StringVar()
    default_text = "ex.Kritsakon.P"
    E14 = ET2(GUI=GUI5,label='Reject by:',options=sectionmgr_list,textvariable=v_approve0,
              default_text=default_text,scaling_factor=scaling_factor,toggle_var=True,fg='Grey',
              x_position=-34,frame_width=-90,widget_width=-39)
    E14.place(x=18*scaling_factor,y=110*scaling_factor)

def update_button(parent_window, v_loto_no, v_work_title, v_lock_date):
    GUI4,NewLoto_x,NewLoto_y  = create_approve_reject_window('Update',400,270,parent=parent_window)
    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(GUI4,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(GUI4, text="Update work detail",style="label1.TLabel")
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
    frame3 = tk.Frame(GUI4, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(NewLoto_x-(216*scaling_factor)), y=int(NewLoto_y-(45*scaling_factor)), width=200*scaling_factor, height=40*scaling_factor)
    ## CREATE: BUTTON
    button2 = ttk.Button(frame3, text="CONFIRM", style="Custom2.TButton",command=lambda: confirm_button_update(GUI4,parent_window, v_loto_no, v_work_title, 
                                                                                                                v_lock_date,v_pdf_update,v_override_update, v_remark0, 
                                                                                                                v_update0,state=True,refresh_callback=refresh_treeview))
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton",command=GUI4.destroy)
    button3.pack(side=RIGHT)
    ## CREATE: PDF Entry
    v_pdf_update = StringVar()
    pdf_entry = pdf_update(GUI4,'P&ID Markup:',28*scaling_factor,45*scaling_factor,v_pdf_update)
    pdf_entry.place(x=28*scaling_factor,y=45*scaling_factor)
    ## CREATE: OVERRIDE Entry
    v_override_update = StringVar()
    override_entry = pdf_update(GUI4,'Override:',28*scaling_factor,80*scaling_factor,v_override_update)
    override_entry.place(x=28*scaling_factor,y=80*scaling_factor)
    ## CREATE: LABEL FOR REMARK
    label_remark = ttk.Label(GUI4,text='Remark:',style="label2.TLabel")
    label_remark.place(x=28*scaling_factor,y=115*scaling_factor)
    ## CREATE: REMARK ENTRY
    v_remark0 = StringVar()
    default_text = "***Remark entry***"
    remark_update(GUI4,font=FONT7,scaling_factor=scaling_factor,textvariable=v_remark0,
                            placeholder=default_text,fg='grey',y_position=(115*scaling_factor))
    ## CREATE: APPROVE LABEL AND ENTRY
    v_update0 = StringVar()
    default_text = "ex.Kritsakon.P"
    E14 = ET2(GUI=GUI4,label='Update by:',options=lomember_list,textvariable=v_update0,
              default_text=default_text,scaling_factor=scaling_factor,toggle_var=True,fg='Grey',
              x_position=-34,frame_width=-70,widget_width=-20)
    E14.place(x=18*scaling_factor,y=180*scaling_factor)

# CREATE: CLASS FOR ENTRY IN GUI2 TOPLEVEL AND OTHER
## CLASS HALF LENGHT 1st
class ET1(tk.Frame):
    def __init__(self,GUI,label,textvariable):
        super().__init__(GUI,width=(430*scaling_factor)/2,height=100*scaling_factor, background="#ffffff")
        self.L = ttk.Label(self,text=label,style="label2.TLabel")
        self.L.place(x=10*scaling_factor,y=2*scaling_factor)
        self.E1 = ttk.Entry(self,style="TEntry",width=35,textvariable=textvariable,font=FONT7)
        self.E1.place(x=137*scaling_factor, y=0)

## CLASS DROPDOWN
class ET2(tk.Frame):
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
        self.L.place(x=10 * scaling_factor, y=2 * scaling_factor)

        # Setup Text as Combobox
        self.text = tk.Text(self, font=FONT7, foreground=self.fg, highlightbackground="grey",
                                   highlightcolor="grey", highlightthickness=1,
                                   borderwidth=2, relief="flat", wrap="none")
        self.text.insert('1.0', default_text)
        self.text.place(x=((self.x_position+126) * scaling_factor), y=(1.1 * scaling_factor), width=int((self.widget_width+283) * scaling_factor), height=int(22 * scaling_factor))
        self.text.bind("<Button-1>",self.toplevel_popup)
        self.text.bind("<Tab>", focus_next_widget)  # Tab to next widget
        ET2.instances.append(self)
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
        self.dd_button1 = ttk.Button(self.dd_frame, text="CONFIRM", style="Custom3.TButton",
                                     command=self.fetch_dd_top_input)
        self.dd_button1.pack(side=LEFT)
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
        if self.dropdown_id: # Cancel any old events
            self.dropdown_list.after_cancel(self.dropdown_id)
        self.dropdown_id = self.dropdown_list.after(2000, self.hide_dropdown)

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
class ET2_linebreak(tk.Frame):
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
        ET2_linebreak.instances.append(self)
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
        self.dd_button1 = ttk.Button(self.dd_frame, text="CONFIRM", style="Custom3.TButton",
                                     command=self.fetch_dd_top_input)
        self.dd_button1.pack(side=LEFT)
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
        if self.dropdown_id: # Cancel any old events
            self.dropdown_list.after_cancel(self.dropdown_id)
        self.dropdown_id = self.dropdown_list.after(2000, self.hide_dropdown)

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
class ET3(tk.Frame):
    instances = []
    def __init__(self,GUI,label,textvariable,placeholder,toggle_var = True,fg='grey'):
        super().__init__(GUI,width=int(430*scaling_factor),height=int(30*scaling_factor), background="#dcdad5")
        self.L = ttk.Label(self,text=label,style="label2.TLabel")
        self.L.place(x=10*scaling_factor,y=2*scaling_factor)
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
        ET3.instances.append(self)
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
class ET3_folder(tk.Frame):
    instances = []
    def __init__(self,GUI,label,textvariable,placeholder,open_folder,toggle_var = True,fg='grey'):
        super().__init__(GUI,width=int(430*scaling_factor),height=int(30*scaling_factor), background="#dcdad5")
        self.L = ttk.Label(self,text=label,style="label2.TLabel")
        self.L.place(x=10*scaling_factor,y=2*scaling_factor)
        self.textvariable = textvariable
        self.textvariable.trace("w", self.update_text_widget)
        self.open_folder = open_folder
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
        ET3_folder.instances.append(self)
        self.switch_editable()

        self.E1.bind('<FocusIn>', self.on_entry_click)
        self.E1.bind('<FocusOut>', self.on_focus_out)
        
        
    def open_folder1(self):
        folder_location = os.path.dirname(self.open_folder)
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
class ET4(tk.Frame):
    instances = []
    def __init__(self, GUI, label, textvariable, default_text,toggle_var = True,fg='grey'):
        super().__init__(GUI, width=int(430 * scaling_factor), height=int(166 * scaling_factor), background="#dcdad5")
        self.pack_propagate(False)
        self.textvariable = textvariable
        self.toggle_var = toggle_var
        self.fg = fg

        self.L = ttk.Label(self, text=label, style="label2.TLabel")
        self.L.place(x=10 * scaling_factor, y=2 * scaling_factor)

        # Setting up the Text widget to behave like a single-line entry
        self.E1 = tk.Text(self, height=1, wrap='none', font=FONT7,
                          borderwidth=2, relief='flat', highlightthickness=1,
                          highlightbackground='grey', highlightcolor='grey', undo=True)
        self.E1.place(x=126 * scaling_factor, y=0, width=int(283*scaling_factor), height=int(23*scaling_factor))

        self.default_text = default_text
        self.placeholder_active = True
        self.insert_placeholder()
        ET4.instances.append(self)
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
class ET5(tk.Frame):
    instances = []
    def __init__(self, GUI, label, textvariable, placeholder,toggle_var = True,fg='grey'):
        super().__init__(GUI, width=int(430 * scaling_factor), height=int(166 * scaling_factor), background="#dcdad5")
        self.pack_propagate(False)
        self.textvariable = textvariable
        self.L = ttk.Label(self, text=label, style="label2.TLabel")
        self.L.place(x=10 * scaling_factor, y=2 * scaling_factor)
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
        ET5.instances.append(self)
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
class ET6(tk.Frame):
    instances = []
    def __init__(self, GUI, label, textvariable, default_text,toggle_var = True,fg='grey'):
        super().__init__(GUI, width=int(430 * scaling_factor), height=int(166 * scaling_factor), background="#dcdad5")
        self.pack_propagate(False)
        self.textvariable = textvariable
        self.toggle_var = toggle_var
        self.fg = fg

        self.L = ttk.Label(self, text=label, style="label2.TLabel")
        self.L.place(x=10 * scaling_factor, y=2 * scaling_factor)

        # Setting up the Text widget to behave like a single-line entry
        self.E1 = tk.Text(self, height=1, wrap='none', font=FONT7,
                          borderwidth=2, relief='flat', highlightthickness=1,
                          highlightbackground='grey', highlightcolor='grey', undo=True)
        self.E1.place(x=126 * scaling_factor, y=0, width=int(283*scaling_factor), height=int(23*scaling_factor))

        self.default_text = default_text
        self.placeholder_active = True
        self.insert_placeholder()
        ET6.instances.append(self)
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
class ET7:
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
        ET7.instances.append(self)
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

## CLASS FOR PDF
class pdf(tk.Frame):
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

## CLASS FOR CREATE AND COPY FILE
class CreateCopy:
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

## CLASS FOR Push notification via Email
class PushNotify:
    asew = scaling_factor
    
## CLASS FOR APPROVE BUTTON (TEXT WITH SCROLL BAR)
class approve_remark():
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
        approve_remark.instances.append(self)

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
class pdf_update(tk.Frame):
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
class remark_update():
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
        remark_update.instances.append(self)

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

################### "NEW" BUTTON (TOP LEVEL)
def NewLoto():
    # CREATE: GUI2 Toplevel
    GUI2, NewLoto_x, NewLoto_y = create_new_window('New LOTO work')

    # CONFIGURE: label1 (Main)
    configure_label_style()

    # CREATE: FORM
    ## CREATE: CANVAS
    line1 = tk.Canvas(GUI2,width=NewLoto_x,height=NewLoto_y,background='#dcdad5')
    line1.pack()
    ## CREATE: HEADLINE LABEL AND LINE
    label1 = ttk.Label(GUI2, text="Work detail",style="label1.TLabel")
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
    frame3 = tk.Frame(GUI2, background="#dcdad5", borderwidth=1, relief="flat")
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
    v_work_title = create_work_title_entry(GUI2, topic_x, entry_1)

    ### CREATE: DEPARTMENT ENTRY
    v_department = create_incharge_entry(GUI2, topic_x, entry_1)

    ### CREATE: OWNER ENTRY
    v_owner = create_owner_entry(GUI2, topic_x, entry_1)

    # ### CREATE: INTERNAL PHONE ENTRY CUT OFF
    # v_internalphone = create_internal_phone_entry(GUI2, topic_x, entry_1)

    ### CREATE: TELEPHONE ENTRY
    #### CREATE: GUIDLINE TEXT
    v_telephone = create_telephone_entry(GUI2, topic_x, entry_1)
    ### CREATE: AREA ENTRY
    v_area = create_working_area_entry(GUI2, topic_x, entry_1)
    ### CREATE: EQUIPMENT ENTRY
    v_equipment = create_equipment_entry(GUI2, topic_x, entry_1)
    ### CREATE: START DATE ENTRY
    v_lock_date = create_lock_date_entry(GUI2, topic_x, entry_1)
    ### CREATE: LOTO No. ENTRY
    v_loto_no = create_loto_entry(GUI2, topic_x, entry_1)
    ### CREATE: TOTAL LOCK KEYS ENTRY
    v_loto_keys = create_total_lock_keys_entry(GUI2, topic_x, entry_1)
    
    ### CREATE: P&ID MARKUP ENTRY
    v_pid_pdf, pdf1 = create_pdf_entry(GUI2, entry_1)

    ### CREATE: OVERRIDE ENTRY
    v_override,ovrd = create_override_entry(GUI2, entry_1)

    ############ CREATE: REMARK ENTRY
    ### CREATE: REMARK ENTRY WITH SCROLL BAR
    v_remark = create_remark_entry(GUI2, entry_1)

    #### FUNCTION: Loop for indicate hieght each row
    entry_2 = [int(395*scaling_factor)]
    current_ent = 0
    for i in range(1,3):
        current_ent = entry_2[i-1]+int(26*scaling_factor)
        entry_2.append(current_ent)
    ############ FUNCTION: Loop for indicate hieght each row

    ### CREATE: PREPARE BY ENTRY
    v_prepare = create_prepare_entry(GUI2, topic_x, entry_2)
    ### CREATE: VERYFY BY ENTRY
    v_verify = create_verify_entry(GUI2, topic_x, entry_2)
    ### CREATE: APPROVE BY ENTRY
    v_approve,E14_instance = create_approve_entry_2(GUI2, topic_x, entry_2)
    
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
            create_copy_instance = CreateCopy(folder_date, area, work_title,pid_pdf,override,linebreak_filepath)
            create_copy_instance.create_folder()
            if pid_pdf:
                create_copy_instance.transfer_pdf()
                pid_pdf = create_copy_instance.rename_pdf()
                
            if override:
                create_copy_instance.transfer_override()
                override = create_copy_instance.rename_override()

            if linebreak_filepath:
                create_copy_instance.transfer_linebreak()
                linebreak_filepath = create_copy_instance.rename_linebreak()

            insert_new_loto(logid,work_title,incharge_dept,owner,telephone,area,
                            equipment,lock_date,loto_no,loto_keys,pid_pdf,override,remark,prepare,verify,approve)
            update_table_pending()
            # clear_all_entries()
            GUI2.destroy()
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
            GUI2.focus_set()
            return None
        elif work_title=="" or loto_no=="" or lock_date=="":
            show_message('Error','Please fill in at Work title, Lock box no. and Lock date')
            GUI2.focus_set()
            return None
        else:
            # Return the form values if not all fields are empty
            return work_title, incharge_dept, owner, telephone, area, equipment, lock_date, loto_no, loto_keys, pid_pdf, override, remark, prepare, verify, approve

    def clear_all_entries():
        pdf1.clear_file_name()
        ovrd.clear_file_name()
        for instance in ET2.instances:
            instance.text.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()    
        
        for instance in ET3.instances:
            instance.E1.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()
        
        for instance in ET4.instances:
            instance.E1.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()
        
        for instance in ET5.instances:
            instance.E1.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()

        for instance in ET6.instances:
            instance.E1.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()
        
        for instance in ET7.instances:
            instance.text_widget.delete('1.0', 'end')
            instance.placeholder_active = True
            instance.insert_placeholder()
        
        
    # def copytofolder():
    #     work_title = v_work_title.get()
    #     area = v_area.get()
    #     create_copy_instance = CreateCopy(folder_date, area, work_title)
    #     create_copy_instance.create_folder()
    
    button1 = ttk.Button(GUI2, text="CLEAR", style="Custom2.TButton",command=clear_all_entries)
    button1.place(x=16*scaling_factor,y=button_y*scaling_factor)
    button2 = ttk.Button(frame3, text="SUBMIT", style="Custom2.TButton",command=savetodb)
    button2.pack(side=LEFT)
    button3 = ttk.Button(frame3, text="CLOSE (X)", style="Custom2.TButton",command=GUI2.destroy)
    # button3 = ttk.Button(frame3, text="CLOSE (X)", style="Custom2.TButton",command=copytofolder)
    button3.pack(side=RIGHT)

    GUI2.mainloop()

def create_approve_entry(GUI2, topic_x, entry_2, default_text = 'ex.Kritsakon.P', toggle_var = True, fg='grey'):
    v_approve = StringVar()
    E14 = ET2(GUI=GUI2,label='Approve by:',options=sectionmgr_list,textvariable=v_approve,
              default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E14.place(x=topic_x,y=entry_2[2])
    return v_approve

def create_approve_entry_2(GUI2, topic_x, entry_2, default_text = 'ex.Kritsakon.P', toggle_var = True, fg='grey'):
    v_approve = StringVar()
    E14 = ET2_linebreak(GUI=GUI2,label='Approve by:',options=sectionmgr_list,textvariable=v_approve,
              default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E14.place(x=topic_x,y=entry_2[2])
    return v_approve, E14  

def create_verify_entry(GUI2, topic_x, entry_2, default_text = 'ex.Boonchoo.J', toggle_var = True, fg='grey'):
    v_verify = StringVar()
    E13 = ET2(GUI=GUI2,label='Verify by:',options=lomember_list,textvariable=v_verify,
              default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E13.place(x=topic_x,y=entry_2[1])
    return v_verify

def create_prepare_entry(GUI2, topic_x, entry_2 , default_text = 'ex.Thanayod.W', toggle_var = True, fg='grey'):
    v_prepare = StringVar()
    E12 = ET2(GUI=GUI2,label='Prepare by:',options=lomember_list,textvariable=v_prepare,
              default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E12.place(x=topic_x,y=entry_2[0])
    return v_prepare

def create_remark_entry(GUI2, entry_1, default_text = "***Remark entry***", toggle_var = True, fg='grey'):
    label4 = ttk.Label(GUI2,text='Remark:',style="label2.TLabel")
    label4.place(x=40*scaling_factor,y=entry_1[11])
    v_remark = StringVar()
    text_remark = ET7(master=GUI2,font=FONT7,scaling_factor=scaling_factor,toggle_var=toggle_var,textvariable=v_remark,
                      placeholder=default_text,y_position=entry_1[11],fg=fg)      
    return v_remark

def create_override_entry(GUI2, entry_1):
    v_override = StringVar()
    ovrd = pdf(GUI=GUI2,label_text='Override list:',x_pos=int(40*scaling_factor),y_pos=entry_1[10]+int(scaling_factor),textvariable=v_override)
    ovrd.place(x=int(40*scaling_factor),y=entry_1[10])
    return v_override,ovrd

# FUNCTION: To show Overrid list File in work detail when double click in Overview or Pending tab
def create_overide_show(GUI2, entry_1,ovrd_url):
    ovrd_place = pdf_show(GUI=GUI2,labeltext='Override list:',x_pos=int(40*scaling_factor),y_pos=entry_1[10],textvariable=ovrd_url)
    ovrd_place.place(x=int(40*scaling_factor),y=entry_1[10])

def create_pdf_entry(GUI2, entry_1):
    v_pid_pdf = StringVar()
    pdf1 = pdf(GUI=GUI2,label_text='P&ID Markup:',x_pos=int(40*scaling_factor),y_pos=entry_1[9]+int(2*scaling_factor),textvariable=v_pid_pdf)
    # pdf1 location for clear file name
    pdf1.place(x=int(40*scaling_factor),y=entry_1[9])
    return v_pid_pdf,pdf1
    
# FUNCTION: To show PDF File in work detail when double click in Overview or Pending tab
def create_pdf_show(GUI2, entry_1,pdf_url):
    pdf_place = pdf_show(GUI=GUI2,labeltext='P&ID Markup:',x_pos=int(40*scaling_factor),y_pos=entry_1[9],textvariable=pdf_url)
    pdf_place.place(x=int(40*scaling_factor),y=entry_1[9])

def create_total_lock_keys_entry(GUI2, topic_x, entry_1, default_text='5', toggle_var = True, fg='grey'):
    v_loto_keys = StringVar()
    E11 = ET4(GUI=GUI2,label='Total lock keys:',textvariable=v_loto_keys,default_text=default_text,toggle_var=toggle_var,fg=fg)
    E11.place(x=topic_x,y=entry_1[8])
    return v_loto_keys

def create_loto_entry(GUI2, topic_x, entry_1, default_text='10', toggle_var = True, fg='grey'):
    v_loto_no = StringVar()
    E10 = ET4(GUI=GUI2,label= 'Lock box No:',textvariable=v_loto_no,default_text=default_text,toggle_var=toggle_var,fg=fg)
    E10.place(x=topic_x,y=entry_1[7])
    return v_loto_no

def create_lock_date_entry(GUI2, topic_x, entry_1, default_text = date_str(1), toggle_var = True, fg='grey'):
    v_lock_date = StringVar()
    E8 = ET5(GUI=GUI2,label='Lock date:',textvariable=v_lock_date,placeholder=default_text,toggle_var=toggle_var,fg=fg)
    E8.place(x=topic_x,y=entry_1[6])
    return v_lock_date

def create_equipment_entry(GUI2, topic_x, entry_1, default_text = 'Select Machine or Equipment list', toggle_var = True, fg='grey'):
    v_equipment = StringVar()
    E7 = ET2(GUI=GUI2,label='Machine/Equipment:',options=machine_list,textvariable=v_equipment,
             default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E7.place(x=topic_x,y=entry_1[5])
    return v_equipment

def create_working_area_entry(GUI2, topic_x, entry_1, default_text = 'Select Area list', toggle_var = True, fg='grey'):
    v_area = StringVar()
    E6 = ET2(GUI=GUI2,label='Working area:',textvariable=v_area,options=area_list,
             default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E6.place(x=topic_x,y=entry_1[4])
    return v_area

def create_telephone_entry(GUI2, topic_x, entry_1, default_text = '091-234-5678', toggle_var = True, fg='grey'):
    v_telephone = StringVar()
    E5 = ET6(GUI=GUI2,label='Telephone no:',textvariable=v_telephone,default_text=default_text,toggle_var=toggle_var,fg=fg)
    E5.place(x=topic_x,y=entry_1[3])
    return v_telephone

# def create_internal_phone_entry(GUI2, topic_x, entry_1, default_text = "8266", toggle_var = True, fg='grey'):
    v_internalphone = StringVar()
    E4 = ET4(GUI=GUI2,label='Internal phone no:',textvariable=v_internalphone,default_text=default_text,toggle_var=toggle_var,fg=fg)
    E4.place(x=topic_x,y=entry_1[3])
    return v_internalphone

def create_owner_entry(GUI2, topic_x, entry_1, default_text = 'Select Owner list', toggle_var = True, fg='grey'):
    v_owner = StringVar()
    E3 = ET2(GUI=GUI2,label='Owner:',options=owner_list,textvariable=v_owner,
             default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E3.place(x=topic_x,y=entry_1[2])
    return v_owner

def create_incharge_entry(GUI2, topic_x, entry_1, default_text = 'Select Department list', toggle_var = True, fg='grey'):
    v_department = StringVar()
    E2 = ET2(GUI=GUI2,label='In charge by:',textvariable=v_department,options=incharge_list,
             default_text=default_text,scaling_factor=scaling_factor,toggle_var=toggle_var,fg=fg)
    E2.place(x=topic_x,y=entry_1[1])
    return v_department

def create_work_title_entry(GUI2, topic_x, entry_1, default_text = 'Isolate HP Pump A for Overhaul', toggle_var = True, fg='grey'):
    v_work_title = StringVar()
    E1 = ET3(GUI=GUI2,label='Work Title:',textvariable=v_work_title,placeholder=default_text,toggle_var=toggle_var,fg=fg)
    E1.place(x=topic_x,y=entry_1[0])
    return v_work_title

def create_work_title_show(GUI2, topic_x, entry_1, open_folder, default_text = 'Isolate HP Pump A for Overhaul',
                            toggle_var = True, fg='grey'):
    v_work_title = StringVar()
    E1 = ET3_folder(GUI=GUI2,label='Work Title:',textvariable=v_work_title,
                    placeholder=default_text,open_folder=open_folder,toggle_var=toggle_var,fg=fg)
    E1.place(x=topic_x,y=entry_1[0])
    return v_work_title

def configure_label_style():
    style.configure('label1.TLabel',background="#dcdad5", foreground='#4f4f4f', font=FONT5)
    style.configure('label2.TLabel',background="#dcdad5", foreground='#4f4f4f', font=FONT6)
    style.configure("TEntry",padding=3)

def create_new_window(title_name):
    # title_name= New LOTO work
    GUI2 = tk.Toplevel(background='#dcdad5')
    NewLoto_x = int(480*scaling_factor)
    NewLoto_y = int(550*scaling_factor)
    win2size = center_windows(NewLoto_x,NewLoto_y)
    GUI2.geometry(win2size)
    GUI2.title(title_name) 
    GUI2.resizable(False, False)
    return GUI2,NewLoto_x,NewLoto_y

# CREATE: Button "New" and "Print"
button1 = ttk.Button(frame0, text="NEW", style="Custom1.TButton",cursor='hand2',command=NewLoto)
button1.place(x=925*scaling_factor,y=50*scaling_factor)
button2 = ttk.Button(frame0, text="PRINT", style="Custom1.TButton",cursor='hand2')
button2.place(x=925*scaling_factor,y=93*scaling_factor)

# CONFIGURE: LABEL1
style.configure('Custom1.TLabel',background="#dcdad5", foreground='#4f4f4f', font=FONT3)

# CREATE: Label under the table
label1 = ttk.Label(frame2, text=f"Total active LOTO : {total_loto}",style='Custom1.TLabel')
label1.pack(side='right')
date_today = date_str(1)
label3 = ttk.Label(frame2,text=f"Today : {date_today}",style='Custom1.TLabel')
label3.pack(side='left')

# CONFIGURE: LABEL2
style.configure('Custom2.TLabel',background="#dcdad5", foreground='#4f4f4f', font=FONT4)

# CREATE: Label upper the table
label2 = ttk.Label(frame0, text="LOTO List",style='Custom2.TLabel')
label2.place(x=17*scaling_factor, y=16*scaling_factor)

# CREATE: TABLE CREATE
header = ['LOTO No.','Work Description','Department','Effective date','Status']
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

# ______________________________________________________________________________________________________________
#=====================================<DOUBLE CLICK to Work detail>===============================================

# ______________________________________________________________________________________________________________



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

# CREATE: Label
label2_p = ttk.Label(frame0_p, text="Pending List",style='Custom2.TLabel')
label2_p.place(x=17*scaling_factor, y=16*scaling_factor)

# CREATE: Label under the table
label1_p = ttk.Label(frame2_p, text=f"Total active LOTO : {total_loto_p}",style='Custom1.TLabel')
label1_p.pack(side='right')
date_today = date_str(1)
label3_p = ttk.Label(frame2_p,text=f"Today : {date_today}",style='Custom1.TLabel')
label3_p.pack(side='left')

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

# CREATE: Label
label2_c = ttk.Label(frame0_c, text="Completed List",style='Custom2.TLabel')
label2_c.place(x=17*scaling_factor, y=16*scaling_factor)

# CREATE: Label under the table
label1_c = ttk.Label(frame2_c, text=f"Total active LOTO : {total_loto}",style='Custom1.TLabel')
label1_c.pack(side='right')
date_today = date_str(1)
label3_c = ttk.Label(frame2_c,text=f"Today : {date_today}",style='Custom1.TLabel')
label3_c.pack(side='left')

# CREATE: TABLE
header_c = ['LOTO No.','Work Description','Department','Effective date','Completed date','Total days']
header_c_w1 = int(90*scaling_factor)
header_c_w2 = int(400*scaling_factor)
header_c_w3 = int(135*scaling_factor)
header_c_w4 = int(135*scaling_factor)
header_c_w5 = int(135*scaling_factor)
header_c_w6 = int(108*scaling_factor)
headerw_c = [header_c_w1,header_c_w2,header_c_w3,header_c_w4,header_c_w5,header_c_w6]
loto_datalist_c = ttk.Treeview(frame1_c,columns=header_c,show='headings',height=10)
loto_datalist_c.pack(fill='y',expand=True)

# CONFIGURE: TABLE CONFIGURE
style = ttk.Style()
style.configure('Treeview.Heading',padding=(5*scaling_factor,5*scaling_factor),font=FONT2,foreground='#4f4f4f')
style.configure('Treeview',rowheight=int(23*scaling_factor),font = FONT3)
loto_datalist_p.tag_configure('evenrow', background="#ffffff")
loto_datalist_p.tag_configure('oddrow', background="#F1F0E8")

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
root.mainloop()