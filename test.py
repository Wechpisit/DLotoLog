import tkinter as tk
import webbrowser
import os
import shutil
import logging  # Added for logging
from tkinter import ttk, filedialog, PhotoImage
from tkinter import *
from tkinter import messagebox
from datetime import datetime
from PIL import Image, ImageTk
import ctypes
from ctypes import windll
import sqlite3

# Enable high DPI awareness for better scaling
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("loto_project_debug.log"),
        logging.StreamHandler()
    ]
)

# Initialize database path and connection
DIRECTORY = "C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/LNG Project/2024/2.LOTO Project"
DB_NAME = "loto_data.db"
DATABASE_PATH = os.path.join(DIRECTORY, DB_NAME)

# Establish connection to the database
conn = sqlite3.connect(DATABASE_PATH)
c = conn.cursor()

# Function to create required tables if they don't exist
def setup_database():
    """Sets up the required tables in the database."""
    c.execute(""" CREATE TABLE IF NOT EXISTS loto_overview (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    loto_no TEXT,
                    work_title TEXT,
                    owner TEXT,
                    lock_date TEXT,
                    status TEXT)""")
    
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
    conn.commit()
    logging.info("Database tables are set up or confirmed as existing.")

# Call setup to create tables
setup_database()

# Insert data into loto_overview table
def insert_data(loto_no, work_title, owner, telephone):
    """Inserts a new record into the loto_overview table."""
    with conn:
        c.execute('INSERT INTO loto_overview VALUES (?, ?, ?, ?, ?, ?)', (None, loto_no, work_title, owner, telephone, 'new'))
        conn.commit()
        logging.debug(f"Inserted data into loto_overview: {loto_no}, {work_title}, {owner}, {telephone}")

# Retrieve all data from loto_overview table
def view_data():
    """Fetches all records from the loto_overview table."""
    with conn:
        c.execute('SELECT * FROM loto_overview')
        result = c.fetchall()
        logging.debug("Fetched data from loto_overview.")
        return result

# Retrieve records from loto_new with specific statuses
def view_data_new():
    """Fetches records from the loto_new table where status is 'Waiting' or 'Rejected'."""
    with conn:
        c.execute("""SELECT new_loto_no, new_work_title, new_incharge_dept, new_owner, new_prepare, new_lock_date, status
                     FROM loto_new
                     WHERE status = 'Waiting' OR status = 'Rejected'""")
        result = c.fetchall()
        logging.debug("Fetched new waiting or rejected data from loto_new.")
        return result

# Insert data into loto_new table
def insert_new_loto(log_id, new_work_title, new_incharge_dept, new_owner, new_telephone, new_area, new_equipment, new_lock_date, new_loto_no, new_loto_keys, new_pid_pdf, new_override_list, new_remark, new_prepare, new_verify, new_approve):
    """Inserts a new record into the loto_new table."""
    with conn:
        c.execute('INSERT INTO loto_new VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                  (None, log_id, new_work_title, new_incharge_dept, new_owner, new_telephone, new_area, new_equipment, new_lock_date, new_loto_no, new_loto_keys, new_pid_pdf, new_override_list, new_remark, new_prepare, new_verify, new_approve, 'Waiting'))
        conn.commit()
        logging.debug(f"Inserted new record into loto_new for work_title: {new_work_title}")

# Transfer data from loto_new to loto_overview if conditions are met
def transfer_data():
    """Transfers records from loto_new to loto_overview where status is 'Active' or 'Onsite' and no duplicates."""
    with conn:
        c.execute("""
            INSERT INTO loto_overview (loto_no, work_title, owner, lock_date, status)
            SELECT new_loto_no, new_work_title, new_incharge_dept, new_lock_date, status
            FROM loto_new 
            WHERE status IN ('Active', 'Onsite')
            AND (new_loto_no, new_work_title, new_incharge_dept, new_lock_date) NOT IN (
                SELECT loto_no, work_title, owner, lock_date FROM loto_overview
            )
        """)
        conn.commit()
        logging.info("Data successfully transferred from loto_new to loto_overview.")

# Set DPI Awareness for better scaling on high-DPI displays
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# Configure window and basic application setup
root = tk.Tk()
root.title("LOTO-LOT1")
root.resizable(False, False)

def get_scaling_factor():
    """Returns the scaling factor based on system DPI settings."""
    user32 = ctypes.windll.user32
    dpi = user32.GetDpiForSystem()
    scaling = dpi / 96
    logging.debug(f"Scaling factor determined: {scaling}")
    return scaling

scaling_factor = get_scaling_factor()

# Base and adjusted dimensions
base_width, base_height = 1050, 650
adjusted_width, adjusted_height = int(base_width * scaling_factor), int(base_height * scaling_factor)

# Set default folder path
folder_path = 'C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/LNG Project/2024/2.LOTO Project'
logging.debug(f"Default folder path set: {folder_path}")

# Center the window
def center_windows(w, h):
    """Centers the window on the screen based on dimensions."""
    ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (ws - w) // 2, (hs - h) // 2 - 30
    logging.debug(f"Centered window size and position calculated: {w}x{h} at {x}, {y}")
    return f'{w}x{h}+{x}+{y}'

root.geometry(center_windows(adjusted_width, adjusted_height))

def date_str(select):
    """Returns formatted date strings based on selection."""
    a = datetime.now()
    formats = {
        1: a.strftime("%d/%m/%y"),
        2: a.strftime("%Y%m%d"),
        3: a.strftime("%d/%m/%y %H:%M"),
    }
    date_value = formats.get(select, "")
    logging.debug(f"Date string generated: {date_value} for selection {select}")
    return date_value

# Focus configuration for input fields
def on_focus_in(event):
    logging.debug("Widget gained focus; highlighting border.")
    event.widget.config(highlightbackground="#5f87aa", highlightcolor="#5f87aa", highlightthickness=2)

def on_focus_out(event):
    logging.debug("Widget lost focus; resetting border.")
    event.widget.config(highlightbackground="grey", highlightcolor="grey", highlightthickness=1)

def focus_next_widget(event):
    """Focuses the next widget in the tab order."""
    logging.debug("Moving focus to the next widget in tab order.")
    event.widget.tk_focusNext().focus()
    return "break"

# Configure window icon
def set_window_icon(root):
    """Sets the application icon if available."""
    icon_path = "IconProgram1.ico"
    try:
        icon_image = Image.open(icon_path)
        root.iconphoto(True, ImageTk.PhotoImage(icon_image))
        logging.info(f"Window icon set from {icon_path}")
    except FileNotFoundError:
        logging.error(f"Icon file {icon_path} not found. Continuing without icon.")

set_window_icon(root)

def create_resized_image(path, width, height):
    """Resizes and returns a PhotoImage object."""
    try:
        original_image = Image.open(path)
        resized_image = original_image.resize((width, height))
        logging.info(f"Resized image from {path} to {width}x{height}")
        return ImageTk.PhotoImage(resized_image)
    except FileNotFoundError:
        logging.error(f"Image file {path} not found.")
        return None

# Font configuration
def font_setup():
    """Configures and returns the fonts for the application."""
    logging.debug("Font setup initialized.")
    return (
        tk.font.Font(family='Tahoma', size=9),
        tk.font.Font(family='Tahoma', size=10, weight='bold'),
        tk.font.Font(family='Tahoma', size=10),
        tk.font.Font(family='Tahoma', size=18, weight='bold'),
        tk.font.Font(family='Tahoma', size=14, weight='bold'),
        tk.font.Font(family='Tahoma', size=9),
        tk.font.Font(family='Tahoma', size=9),
        tk.font.Font(family='Tahoma', size=9),
    )

FONT1, FONT2, FONT3, FONT4, FONT5, FONT6, FONT7, FONT8 = font_setup()

# Set up theme and styles
style = ttk.Style(root)
style.theme_use("clam")
logging.debug("Clam theme applied to style.")

def configure_widget_style(scaling_factor, FONT1, style):
    """Configures custom styles for widgets."""
    pad_x1, pad_y1 = int(4 * scaling_factor), int(3 * scaling_factor)
    style.configure("Custom1.TNotebook.Tab", font=FONT1)
    style.map("Custom1.TNotebook.Tab",
        background=[("selected", "lightblue")],
        foreground=[("selected", "Black")],
        focuscolor=[("selected", "lightblue")])
    logging.debug("Custom style configured for notebook tabs.")
    
configure_widget_style(scaling_factor, FONT1, style)

# Add TAB to the GUI
notebook = ttk.Notebook(root, style="Custom1.TNotebook")
notebook.pack(expand=True, fill="both")
logging.debug("Main notebook tab created.")

# Set focus on a specific TAB
def set_focus_on_tab(index):
    """Sets focus to the tab at the given index."""
    notebook.select(index)
    logging.debug(f"Tab focus set to index: {index}")

# Configure button styles
def configure_button_styles(scaling_factor, style):
    """Configures the styles for buttons based on scaling factor."""
    style.configure("Custom1.TButton", 
                    font=("tahoma", 10),  
                    padding=(int(12 * scaling_factor), int(8 * scaling_factor)), 
                    focuscolor='none')  
    style.configure("Custom2.TButton", 
                    font=("tahoma", 9),  
                    padding=(int(8 * scaling_factor), int(5 * scaling_factor)), 
                    focuscolor='none')  
    style.configure("Custom3.TButton", 
                    font=("tahoma", 8),  
                    padding=(int(4 * scaling_factor), int(5 * scaling_factor)), 
                    focuscolor='none')
    logging.debug("Button styles configured based on scaling factor.")

configure_button_styles(scaling_factor, style)  

# Configure combobox styles
style.configure("Custom.TCombobox", arrowsize=25)  # Adjust the size of the dropdown arrow
logging.debug("Combobox style configured.")

# Show a message box
def show_message(title, message):
    """Displays a message box with the given title and message."""
    logging.info(f"Showing message box - {title}: {message}")
    messagebox.showinfo(title, message)

# Set up lists for Dropdown
def list_setup():
    """Sets up lists for dropdown selections used in various fields."""
    incharge_list = [
        'MT.Mech', 'MT.Ins', 'MT.Elec', 'ED.Mech', 'ED.Ins', 'ED.Elec', 
        'ED.Process', 'Project', 'LO.', 'ED.', 'PI'
    ]

    owner_list = [
        'Jutharat.P', 'Chanida.H', 'Pajaree.L', 'Kittipong.V', 'Amporn.T',
        'Somchai.R', 'Witawit.P', 'Phaksunee.In', 'Chanchai.S', 'Jedsada.M',
        'Chalermpon.K', 'Siriwan.K', 'Dan.S', 'Pimjai.I', 'Gunthon.U', 'Wirasak.B',
        'Panuphot.P', 'Nugul.J', 'Parinya.Y', 'Seksan.S', 'Kritsakon.P', 'Jakkrit.C',
        'Nattagorn.R', 'Preeyaporn.S', 'Taipob.K', 'Sarawut.S', 'Yutasart.P', 'Sarayut.K',
        'Nopparat.J', 'Wisud.D', 'Dhosapol.S', 'Natthakorn.S', 'Kittituch.L', 'Tanisorn.S',
        'Piyapong.P', 'Weerayut.P', 'Rapeepan.W', 'Phissara.W', 'Issarush.K', 'Phaopan.T',
        'Teerayut.S', 'Rungroj.S', 'Narunard.H', 'Boonlert.S', 'Chatdanai.B', 'Maytungkorn.S',
        'Rachanon.Y', 'Artit.K', 'Anusorn.N', 'Nutrada.S', 'Pornthep.D', 'Pornthep.L',
        'Dumrongsak.J', 'Wanchai.J', 'Maythika.S', 'Wachirasak.L', 'Sirapong.W', 'Wisit.O',
        'Warin.I', 'Chomphoonuch.W', 'Kitipoom.T', 'Mongkol.S', 'Phuekpon.S', 'Kittipong.P',
        'Kittisak.T', 'Noppanan.T', 'Rattikool.P', 'Narupon.K', 'Ukrit.C', 'Teerasak.S',
        'Wimmalak.R', 'Isarah.P', 'Rinrada.K', 'Sakda.P', 'Amaris.U', 'Kittiwat.R', 'Visarn.K',
        'Kosin.S', 'Ronnaporn.K', 'Krit.Y', 'Wiwid.B', 'Weerachon.S', 'Hirun.U', 'Kanate.Th',
        'Ratchapon.P', 'Thanongsak.K', 'Eakkarin.B', 'Kittiwat.Ro', 'Weerawat.N', 'Korakot.C',
        'Suphamit.K', 'Tharadon.J', 'Naret.N', 'Chidsanupong.V', 'Suttipat.V', 'Sasiwan.M',
        'Worapon.P', 'Mutitaporn.P', 'Nattanich.B', 'Thanaphorn.T', 'Puttiporn.J', 'Piyanut.M',
        'Witthawat.K', 'Siriwit.P', 'Piyachai.M', 'Jantakan.P', 'Siwakan.K', 'Nuttanan.P',
        'Teepakorn.R', 'Thanaporn.S', 'Nadthanakorn.K', 'Thatsapong.S', 'Chintara.R', 'Tanchanok.W',
        'Siriphop.J', 'Sukritta.J', 'Chalermchat.C', 'Worapong.S', 'Yolada.O', 'Pakin.A',
        'Panyawat.L', 'Nateetorn.A', 'Jirayu.J', 'Kornpong.V', 'Tanawat.T', 'Nasrada.S', 'Mintra.M',
        'Nattakorn.B', 'Suphachai.C', 'Phuradech.M', 'Kamonchanok.J', 'Kriangkrai.A', 'Natthawut.C',
        'Pitchayut.P', 'Vichaiprat.S', 'Wechpisit.S', 'Palathip.S', 'Jirapon.P', 'Pacharapol.J',
        'Surasak.D', 'Trin.J', 'Sanya.R', 'Naruepol.L', 'Puttachat.T', 'Narisara.P', 'Sarit.J',
        'Kodchakorn.W', 'Sirawit.S', 'Saransak.N', 'Natnicha.L', 'Thut.B', 'Peeranut.N', 'Soravit.C',
        'Koragoch.T', 'Sukrit.I', 'Theerawit.J', 'Saranya.W', 'Napak.W', 'Warunyoo.W', 'Karan.B',
        'Papawich.P', 'Prolamath.P', 'Natchaiyot.W', 'Kridsakorn.S', 'Pornphun.C', 'Khathawut.B',
        'Thapanee.M', 'Nara.T', 'Chanitpak.A', 'Dhana.P', 'Tritep.O', 'Suphachot.P', 'Arnonnat.C',
        'Natchapol.H', 'Jakkrit.S', 'Wuttipat.W', 'Khemmachat.P', 'Tossapol.K', 'Suwicha.N',
        'Alongkorn.K', 'Amorntep.S', 'Boonchoo.J', 'Kiangkai.C', 'Supanat.T', 'Narudech.S',
        'Thanasak.S', 'Weerapong.L', 'Peeranut.S', 'Jetsadakorn.B', 'Siravit.C', 'Poramane.C',
        'Natcharikan.P', 'Nopphakao.C', 'Ativit.P', 'Phichate.N', 'Thonthan.J', 'Raviwat.T',
        'Phanuwat.J', 'Sudaphorn.Y', 'Supachai.Y', 'Anurak.S', 'Danuwat.B', 'Phuangpayom.S',
        'Surachai.U', 'Chayathorn.C', 'Warayus.S', 'Siripop.P', 'Thanayod.W', 'Nawi.T',
        'Thanatchaporn.K', 'Sarawut.Bo', 'Jenjira.R', 'Sittichok.C', 'Komtanut.C', 'Raiwin.N',
        'Ratatummanoon.S', 'Thitithanu.B', 'Chinnakrit.M', 'Thanadon.T', 'Nutchana.N', 'Veeraphat.K',
        'Chatchaiwat.R', 'Nawin.S', 'Wichanath.P', 'Thitapa.C', 'Warut.T'
    ]

    sectionmgr_list = [
        'Yutasart.P', 'Kritsakon.P', 'Piyapong.P', 'Sarayut.K', 'Dumrongsak.J', 'Kittiwat.Ro'
    ]

    lomember_list = [
        'Parinya.Y', 'Kritsakon.P', 'Sarawut.S', 'Yutasart.P', 'Sarayut.K', 
        'Tanisorn.S', 'Piyapong.P', 'Weerayut.P', 'Rachanon.Y', 'Artit.K', 
        'Dumrongsak.J', 'Mongkol.S', 'Kittiwat.Ro', 'Weerawat.N', 'Naret.N', 
        'Suttipat.V', 'Jantakan.P', 'Phuradech.M', 'Wechpisit.S', 'Palathip.S',
        'Koragoch.T', 'Saranya.W', 'Suphachot.P', 'Jakkrit.S', 'Wuttipat.W',
        'Boonchoo.J', 'Thanasak.S', 'Nopphakao.C', 'Thanayod.W', 'Sittichok.C',
        'Komtanut.C', 'Chinnakrit.M', 'Thanadon.T', 'Veeraphat.K', 'Nawin.S'
    ]

    area_list = [
        'HP Pump', 'BOG Compressor', 'SOG Compressor', 'Recondenser', 'BOG Suction drum', 
        'Truck load', 'LNG Tank', 'Drain pump', 'ORV', 'IA / N2 ', 'Sanitary', 'Metering',
        'Chlorination', 'Seawater pump', 'Seawater intake', 'Jetty Berth1', 'Jetty Berth2',
        'Jetty Berth3', 'LNG Sampling', 'Firewater pump', 'ORC', 'GTG', 'WHRU', 'IFV',
        'CWG Pump', 'IPG IA', 'Admin building', 'Canteen building', 'GIS I', 'GIS II',
        'Fire station', 'Maintenance workshop', 'LAB', 'Warehouse', 'AIB Building',
        'CCR Building', 'Main Substation', 'IPG Substation', 'JCR Building',
        'Jetty Substation', 'Truck load admin', 'Truck load control room', 'Potable water',
        'Service water'
    ]

    machine_list = [
        'HP Pump A', 'HP Pump B', 'HP Pump C', 'HP Pump D', 'HP Pump E', 'HP Pump F', 'HP Pump G', 'HP Pump H', 'HP Pump I', 'HP Pump J', 'HP Pump K',
        'BOG Compressor A', 'BOG Compressor B', 'BOG Compressor C', 'BOG Compressor D', 'SOG Compressor A', 'SOG Compressor B',
        'Seawater pump A', 'Seawater pump B', 'Seawater pump C', 'Seawater pump D', 'Seawater pump E',
        'ORV A', 'ORV B', 'ORV C', 'ORV D', 'ORV E', 'ORV F', 'ORV G', 'ORV H', 'ORV I', 'ORV J',
        'Truck bay A', 'Truck bay B', 'Truck bay C', 'Truck bay D', 'Metering A', 'Metering B', 'Metering C', 'Metering D', 'Metering E',
        'Intank pump  1A', 'Intank pump  1B', 'Intank pump  1C', 'Intank pump  2A', 'Intank pump  2B', 'Intank pump  2C',
        'Intank pump  3A', 'Intank pump  3B', 'Intank pump  3C', 'Intank pump  4A', 'Intank pump  4B', 'Intank pump  4C',
        'LNG Tank 1', 'LNG Tank 2', 'LNG Tank 3', 'LNG Tank 4', 'IA Comp A', 'IA Comp B', 'IA Air dryer A', 'IA Air dryer B',
        'Drain pump', 'Electrolyzer A', 'Electrolyzer B', 'Booster pump A', 'Booster pump B', 'Dosing pump A', 'Dosing pump B',
        'Dosing pump C', 'Air Blower A', 'Air Blower B', 'IFV A', 'IFV B', 'Warm water pump A', 'Warm water pump B', 'Warm water pump C',
        'Warm water pump D', 'Warm water pump E', 'IPG water pump A', 'IPG water pump B', 'IPG water pump C', 'IPG water pump D',
        'IPG water pump E', 'HVAC water pump A', 'HVAC water pump B', 'HVAC water pump C', 'HVAC water pump D', 'HVAC water pump E',
        'GTG A', 'GTG B', 'WHRU A', 'WHRU B', 'ORC', 'ORC Seal oil system', 'ORC Lube oil system', 'CEMs', 'CYP Pump A', 'CYP Pump B',
        'IPG IA Comp A', 'IPG IA Comp B', 'IPG IA Air dryer A', 'IPG IA Air dryer B', 'Hot oil pump A', 'Hot oil pump B', 'WHRU-A Seal fan A',
        'WHRU-A Seal fan B', 'WHRU-B Seal fan A', 'WHRU-B Seal fan B', 'Truck bay A', 'Truck bay B', 'Truck bay C', 'Truck bay D',
        'Unloading arm', 'Jetty platform', 'MD', 'BD', 'Hydrualic oil pump', 'Fire truck', 'Deluge valve', 'Fire extinguisher',
        'B.1 MLA "A"', 'B.1 MLA "B"', 'B.1 MLA "C"', 'B.1 MLA "D"', 'B.2 MLA "E"',
        'B.2 MLA "F"', 'B.2 MLA "G"', 'B.2 MLA "H"', 'B.2 MLA "I"', 'DFBS A', 'DFBS B', 'DFBS C',
        'DFBS D', 'DFBS E', 'Wash water pump A', 'Wash water pump B', 'Wash water pump C', 'Service water pump A', 'Service water pump B',
        'Potable water pump A', 'Potable water pump B'
    ]

    email_list = {
        'Parinya.Y': 'parinya.y@pttlng.com', 'Kritsakon.P': 'kritsakon.p@pttlng.com',
        'Sarawut.S': 'sarawut.s@pttlng.com', 'Yutasart.P': 'yutasart.p@pttlng.com',
        'Sarayut.K': 'sarayut.k@pttlng.com', 'Tanisorn.S': 'tanisorn.s@pttlng.com',
        'Piyapong.P': 'piyapong.p@pttlng.com', 'Weerayut.P': 'weerayut.p@pttlng.com',
        'Rachanon.Y': 'rachanon.y@pttlng.com', 'Artit.K': 'artit.k@pttlng.com',
        'Dumrongsak.J': 'dumrongsak.j@pttlng.com', 'Mongkol.S': 'mongkol.s@pttlng.com',
        'Kittiwat.Ro': 'kittiwat.ro@pttlng.com', 'Weerawat.N': 'weerawat.n@pttlng.com',
        'Naret.N': 'naret.n@pttlng.com', 'Suttipat.V': 'suttipat.v@pttlng.com',
        'Jantakan.P': 'jantakan.p@pttlng.com', 'Phuradech.M': 'phuradech.m@pttlng.com',
        'Wechpisit.S': 'wechpisit.s@pttlng.com', 'Palathip.S': 'palathip.s@pttlng.com',
        'Koragoch.T': 'koragoch.t@pttlng.com', 'Saranya.W': 'saranya.w@pttlng.com',
        'Suphachot.P': 'suphachot.p@pttlng.com', 'Jakkrit.S': 'jakkrit.s@pttlng.com',
        'Wuttipat.W': 'wuttipat.w@pttlng.com', 'Boonchoo.J': 'boonchoo.j@pttlng.com',
        'Thanasak.S': 'Thanasak.s@pttlng.com', 'Nopphakao.C': 'Nopphakao.c@pttlng.com',
        'Thanayod.W': 'thanayod.w@pttlng.com', 'Sittichok.C': 'sittichok.c@pttlng.com',
        'Komtanut.C': 'komtanut.c@pttlng.com', 'Chinnakrit.M': 'chinnakrit.m@pttlng.com',
        'Thanadon.T': 'thanadon.t@pttlng.com', 'Veeraphat.K': 'veeraphat.k@pttlng.com',
        'Nawin.S': 'nawin.s@pttlng.com'
    }

    logging.debug("Dropdown lists have been set up.")
    return incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list

# Unpacking lists and logging for debugging purposes
incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list = list_setup()
logging.info("Dropdown list variables initialized and ready for use.")

# Update table overview
def update_table_overview():
    global total_loto
    total_loto = 0
    loto_datalist.delete(*loto_datalist.get_children())
    transfer_data()
    data = view_data()
    
    for index, d in enumerate(data):
        d = list(d)
        del d[0]  # Remove ID
        status = d[4]
        tag = 'evenrow' if index % 2 == 0 else 'oddrow'
        
        if status in ('Active', 'Onsite'):
            loto_datalist.insert('', 'end', values=d, tags=(tag,))
            total_loto += 1
    
    label1.config(text=f"Total active LOTO : {total_loto}")
    logging.debug(f"Updated table overview: total active LOTO count is {total_loto}")

def refresh_treeview():
    logging.info("Refreshing treeview data")
    update_table_overview()
    update_table_pending()

# Update pending table
def update_table_pending():
    global total_loto_p
    total_loto_p = 0
    loto_datalist_p.delete(*loto_datalist_p.get_children())
    data = view_data_new()
    total_loto_p = len(data)
    
    for index, d in enumerate(data):
        d = list(d)
        tag = 'evenrow' if index % 2 == 0 else 'oddrow'
        loto_datalist_p.insert('', 'end', values=d, tags=tag)
    
    label1_p.config(text=f"Total active LOTO : {total_loto_p}")
    logging.debug(f"Updated pending table: total active LOTO count is {total_loto_p}")

def fetch_data_from_loto_new(loto_no, work_title, lock_date):
    result = add_data_to_popup(loto_no, work_title, lock_date)
    logging.debug(f"Fetched data for LOTO No: {loto_no}, Title: {work_title}, Date: {lock_date}")
    return result

# Display details on double-click
def on_row_double_click_overview(event):
    table_select = event.widget
    selected_item = table_select.selection()
    
    if not selected_item:
        messagebox.showinfo("Error", "No item selected.")
        return
    
    selected_item = selected_item[0]
    item_values = table_select.item(selected_item, "values")
    loto_no, work_title, lock_date = item_values[0], item_values[1], item_values[3]
    
    data_to_popup = fetch_data_from_loto_new(loto_no, work_title, lock_date)
    if not data_to_popup:
        logging.error("No data found for the selected item.")
        return
    
    detail_overview_GUI, NewLoto_x, NewLoto_y = create_new_window('Detail')
    configure_label_style()
    
    # Create Canvas and Frame
    line1 = tk.Canvas(detail_overview_GUI, width=NewLoto_x, height=NewLoto_y, background='#dcdad5')
    line1.pack()
    
    label1 = ttk.Label(detail_overview_GUI, text="Work detail", style="label1.TLabel")
    label1.place(x=int(20 * scaling_factor), y=int(13 * scaling_factor))
    line1.create_rectangle(16, 25, 463, 490, fill='#dcdad5', width=1, outline='#a9a7a3')
    
    frame3 = tk.Frame(detail_overview_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(265 * scaling_factor), y=int(495 * scaling_factor), width=200 * scaling_factor, height=40 * scaling_factor)
    
    # Add buttons
    ttk.Button(detail_overview_GUI, text="COMPLETED", style="Custom2.TButton", command=lambda: completed_button_for_overview(detail_overview_GUI, data_to_popup[9], data_to_popup[2], data_to_popup[8], refresh_gui3_data)).place(x=16 * scaling_factor, y=501 * scaling_factor)
    ttk.Button(frame3, text="UPDATE", style="Custom2.TButton", command=lambda: update_button_for_overview(detail_overview_GUI, data_to_popup[9], data_to_popup[2], data_to_popup[8], data_to_popup[11], refresh_gui3_data)).pack(side=LEFT)
    ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton", command=lambda: reject_button_for_pending(detail_overview_GUI, data_to_popup[9], data_to_popup[2], data_to_popup[8])).pack(side=RIGHT)
    
    # Position entries
    topic_x = int(30 * scaling_factor)
    entry_1 = [int(40 * scaling_factor)]
    
    for i in range(1, 12):
        entry_1.append(entry_1[i - 1] + int(27 * scaling_factor))
    
    logging.debug("Configured UI elements for detail overview.")

# Create entries with existing data
    create_work_title_show(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[2], open_folder=data_to_popup[11], 
                        toggle_var=False, fg='#4f4f4f')
    create_incharge_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[3], toggle_var=False, fg='#4f4f4f')
    create_owner_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[4], toggle_var=False, fg='#4f4f4f')
    create_working_area_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[6], toggle_var=False, fg='#4f4f4f')
    create_equipment_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[7], toggle_var=False, fg='#4f4f4f')
    create_lock_date_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[8], toggle_var=False, fg='#4f4f4f')
    create_loto_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[9], toggle_var=False, fg='#4f4f4f')
    create_total_lock_keys_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[10], toggle_var=False, fg='#4f4f4f')

    # Create PDF, Override, and Remark entries
    pdf_entry_GUI3 = create_pdf_show(detail_overview_GUI, entry_1, pdf_url=data_to_popup[11])
    override_entry_GUI3 = create_overide_show(detail_overview_GUI, entry_1, ovrd_url=data_to_popup[12])
    remark_entry_GUI3 = create_remark_entry_for_update_widget(detail_overview_GUI, entry_1, default_text=data_to_popup[13], toggle_var=False, fg='#4f4f4f')
    remark_entry_GUI3.text_widget.see(tk.END)
    # Function to refresh the GUI data
    def refresh_gui3_data(v_loto_no, v_work_title, v_lock_date):
        remark_entry_GUI3.destroy()
        override_entry_GUI3.destroy()
        pdf_entry_GUI3.destroy()
        
        updated_data = fetch_data_from_loto_new(v_loto_no, v_work_title, v_lock_date)
        if updated_data:
            new_remark = updated_data[0][13]  # Remark
            new_pdf = updated_data[0][11]     # PDF path
            new_override = updated_data[0][12]  # Override list
            
            # Update entries with the new data
            pdf_update = create_pdf_show(detail_overview_GUI, entry_1, pdf_url=new_pdf)
            override_update = create_overide_show(detail_overview_GUI, entry_1, ovrd_url=new_override)
            remark_update = create_remark_entry_for_update_widget(detail_overview_GUI, entry_1, default_text=new_remark, toggle_var=False, fg='#4f4f4f')
            remark_update.text_widget.see(tk.END)
        logging.info("GUI3 data refreshed.")

    # Loop to set positions for additional entries
    entry_2 = [int(395 * scaling_factor)]
    for i in range(1, 3):
        current_ent = entry_2[i - 1] + int(26 * scaling_factor)
        entry_2.append(current_ent)

    # Additional entries
    create_prepare_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[14], toggle_var=False, fg='#4f4f4f')
    create_verify_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[15], toggle_var=False, fg='#4f4f4f')
    create_approve_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[16], toggle_var=False, fg='#4f4f4f')

    return detail_overview_GUI

def on_row_double_click_pending(event=None):
    table_select = event.widget
    selected_item = table_select.selection()
    
    if not selected_item:
        messagebox.showinfo("Error", "No item selected.")
        return
    
    selected_item = selected_item[0]
    item_values = table_select.item(selected_item, "values")
    v1, v2, v3 = item_values[0], item_values[1], item_values[5]
    data_to_popup = fetch_data_from_loto_new(v1, v2, v3)
    data_to_popup = list(data_to_popup[0]) if data_to_popup else None
    
    if data_to_popup:
        detail_overview_GUI, NewLoto_x, NewLoto_y = create_new_window('Detail')
        configure_label_style()
        
        # Setup Canvas and Header
        line1 = tk.Canvas(detail_overview_GUI, width=NewLoto_x, height=NewLoto_y, background='#dcdad5')
        line1.pack()
        label1 = ttk.Label(detail_overview_GUI, text="Work detail", style="label1.TLabel")
        label1.place(x=int(20 * scaling_factor), y=int(13 * scaling_factor))
        line1.create_rectangle(16, 25, 463, 490, fill='#dcdad5', width=1, outline='#a9a7a3')
        
        frame3 = tk.Frame(detail_overview_GUI, background="#dcdad5", borderwidth=1, relief="flat")
        frame3.place(x=int(265 * scaling_factor), y=int(495 * scaling_factor), width=200 * scaling_factor, height=40 * scaling_factor)

        # Buttons for approval and rejection
        approve_button = ttk.Button(frame3, text="APPROVE", style="Custom2.TButton", command=lambda: approve_button_for_pending(detail_overview_GUI, data_to_popup[9], data_to_popup[2], data_to_popup[8]))
        approve_button.pack(side=LEFT)
        
        reject_button = ttk.Button(frame3, text="REJECT", style="Custom2.TButton", command=lambda: reject_button_for_pending(detail_overview_GUI, data_to_popup[9], data_to_popup[2], data_to_popup[8]))
        reject_button.pack(side=RIGHT)
    
    logging.debug("Created detail overview window for pending item.")
# FUNCTION: Loop to calculate height for each row
topic_x = int(30 * scaling_factor)
entry_1 = [int(40 * scaling_factor)]
for i in range(1, 12):
    entry_1.append(entry_1[i - 1] + int(27 * scaling_factor))

# Create GUI entries with pre-populated data
create_work_title_show(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[2], open_folder=data_to_popup[11], toggle_var=False, fg='#4f4f4f')
create_incharge_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[3], toggle_var=False, fg='#4f4f4f')
create_owner_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[4], toggle_var=False, fg='#4f4f4f')
create_telephone_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[5], toggle_var=False, fg='#4f4f4f')
create_working_area_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[6], toggle_var=False, fg='#4f4f4f')
create_equipment_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[7], toggle_var=False, fg='#4f4f4f')
create_lock_date_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[8], toggle_var=False, fg='#4f4f4f')
create_loto_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[9], toggle_var=False, fg='#4f4f4f')
create_total_lock_keys_entry(detail_overview_GUI, topic_x, entry_1, default_text=data_to_popup[10], toggle_var=False, fg='#4f4f4f')
create_pdf_show(detail_overview_GUI, entry_1, pdf_url=data_to_popup[11])
create_overide_show(detail_overview_GUI, entry_1, ovrd_url=data_to_popup[12])
create_remark_entry(detail_overview_GUI, entry_1, default_text=data_to_popup[13], toggle_var=False, fg='#4f4f4f')

# Loop to set height for additional rows
entry_2 = [int(395 * scaling_factor)]
for i in range(1, 3):
    entry_2.append(entry_2[i - 1] + int(26 * scaling_factor))

# Create additional entries for preparation, verification, and approval
create_prepare_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[14], toggle_var=False, fg='#4f4f4f')
create_verify_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[15], toggle_var=False, fg='#4f4f4f')
create_approve_entry(detail_overview_GUI, topic_x, entry_2, default_text=data_to_popup[16], toggle_var=False, fg='#4f4f4f')

# Function to create a new Toplevel window for approval or rejection
def create_approve_reject_window(title_name, size_x, size_y, parent=None):
    new_loto_GUI = tk.Toplevel(parent, background='#dcdad5')
    NewLoto_x = int(size_x * scaling_factor)
    NewLoto_y = int(size_y * scaling_factor)
    new_loto_GUI.geometry(center_windows(NewLoto_x, NewLoto_y))
    new_loto_GUI.title(title_name)
    new_loto_GUI.resizable(False, False)
    logging.info(f"{title_name} window created with size {NewLoto_x}x{NewLoto_y}")
    return new_loto_GUI, NewLoto_x, NewLoto_y

# Fetch data based on LOTO number, work title, and lock date
def add_data_to_popup(loto_no, work_title, lock_date):
    with conn:
        c.execute("SELECT * FROM loto_new WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?", 
                  (loto_no, work_title, lock_date))
        result = c.fetchall()
        logging.debug(f"Fetched data for LOTO No: {loto_no}, Work Title: {work_title}, Lock Date: {lock_date}")
    return result

# Approve button functionality in Pending GUI
def approve_button_for_pending(parent_window, v_loto_no, v_work_title, v_lock_date):
    approve_GUI, NewLoto_x, NewLoto_y = create_approve_reject_window('Approve', 380, 200, parent=parent_window)
    
    # Setup canvas and labels
    line1 = tk.Canvas(approve_GUI, width=NewLoto_x, height=NewLoto_y, background='#dcdad5')
    line1.pack()
    label1 = ttk.Label(approve_GUI, text="Approve detail", style="label1.TLabel")
    label1.place(x=int(20 * scaling_factor), y=int(13 * scaling_factor))
    line1.create_rectangle(16, 25, NewLoto_x - 17, NewLoto_y - 50, fill='#dcdad5', width=1, outline='#a9a7a3')
    
    # Button Frame and Buttons
    frame3 = tk.Frame(approve_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(NewLoto_x - 216 * scaling_factor), y=int(NewLoto_y - 45 * scaling_factor), width=200 * scaling_factor, height=40 * scaling_factor)
    
    ttk.Button(frame3, text="CONFIRM", style="Custom2.TButton", 
               command=lambda: confirm_button_approve(approve_GUI, parent_window, v_loto_no, v_work_title, v_lock_date, 
                                                      v_remark0, v_approve0, state=True, refresh_callback=refresh_treeview)).pack(side=LEFT)
    
    ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton", command=approve_GUI.destroy).pack(side=RIGHT)
    
    # Remark Entry
    v_remark0 = StringVar()
    input_field_remark_for_approve_button(approve_GUI, font=FONT7, scaling_factor=scaling_factor, 
                                          textvariable=v_remark0, placeholder="***Remark entry***", fg='grey', y_position=(45 * scaling_factor))
    
    # Approve By Entry (Dropdown)
    v_approve0 = StringVar()
    input_field_dropdown(GUI=approve_GUI, label='Approve by:', options=sectionmgr_list, textvariable=v_approve0, 
                         default_text="ex.Kritsakon.P", scaling_factor=scaling_factor, toggle_var=True, fg='Grey', 
                         x_position=-34, frame_width=-90, widget_width=-39).place(x=18 * scaling_factor, y=110 * scaling_factor)
    
    logging.info("Approve window and fields created.")
def confirm_button_approve(approve_button_in_pending_GUI, detail_overview_GUI, v_loto_no, v_work_title, v_lock_date, v_remark, v_approve, state, refresh_callback=None):
    """Updates database record based on approval or rejection and refreshes GUI."""
    remark_value0 = v_remark.get().strip()
    remark_value = f"{date_str(3)}\n{remark_value0}"
    approve_value = v_approve.get().strip()

    logging.debug(f"Starting confirm_button_approve for LOTO No: {v_loto_no}, Status: {'Active' if state else 'Rejected'}")
    
    with conn:
        # Fetch existing values
        c.execute("""
            SELECT new_remark, new_approve, status
            FROM loto_new
            WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
            """, (v_loto_no, v_work_title, v_lock_date))
        
        result = c.fetchone()
        if result:
            existing_remark, existing_approve, current_status = result
            if current_status in ["Waiting", "Rejected"]:
                updated_remark = f"{existing_remark}\n{remark_value}" if existing_remark else remark_value
                updated_approve = approve_value
                updated_status = "Active" if state else "Rejected"
                updated_lock_date = date_str(1)

                # Update the record
                c.execute("""
                    UPDATE loto_new
                    SET new_remark = ?, new_approve = ?, status = ?, new_lock_date = ?
                    WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
                    """, (updated_remark, updated_approve, updated_status, updated_lock_date, v_loto_no, v_work_title, v_lock_date))
                conn.commit()
                logging.info(f"Updated LOTO No: {v_loto_no} to Status: {updated_status}")

    # Transfer data and refresh the overview and pending tables if callback provided
    transfer_data()
    if refresh_callback:
        refresh_callback()
    
    logging.debug("Closing approval and detail windows")
    approve_button_in_pending_GUI.destroy()
    detail_overview_GUI.destroy()

def reject_button_for_pending(parent_window, v_loto_no, v_work_title, v_lock_date):
    """Creates a rejection window to add a remark and reject the pending LOTO."""
    reject_GUI, NewLoto_x, NewLoto_y = create_approve_reject_window('Reject', 380, 200, parent=parent_window)

    line1 = tk.Canvas(reject_GUI, width=NewLoto_x, height=NewLoto_y, background='#dcdad5')
    line1.pack()
    ttk.Label(reject_GUI, text="Reject detail", style="label1.TLabel").place(x=int(20 * scaling_factor), y=int(13 * scaling_factor))
    line1.create_rectangle(16, 25, NewLoto_x - 17, NewLoto_y - 50, fill='#dcdad5', width=1, outline='#a9a7a3')

    frame3 = tk.Frame(reject_GUI, background="#dcdad5", borderwidth=1, relief="flat")
    frame3.place(x=int(NewLoto_x - 216 * scaling_factor), y=int(NewLoto_y - 45 * scaling_factor), width=int(200 * scaling_factor), height=int(40 * scaling_factor))

    ttk.Button(frame3, text="CONFIRM", style="Custom2.TButton", 
               command=lambda: confirm_button_approve(reject_GUI, parent_window, v_loto_no, v_work_title, v_lock_date, v_remark0, v_approve0, state=False, refresh_callback=refresh_treeview)).pack(side=LEFT)
    
    ttk.Button(frame3, text="CLOSE(X)", style="Custom2.TButton", command=reject_GUI.destroy).pack(side=RIGHT)

    # Remark entry field
    v_remark0 = StringVar()
    input_field_remark_for_approve_button(reject_GUI, font=FONT7, scaling_factor=scaling_factor, textvariable=v_remark0, placeholder="***Remark entry***", fg='grey', y_position=(45 * scaling_factor))

    # Approver dropdown
    v_approve0 = StringVar()
    input_field_dropdown(GUI=reject_GUI, label='Reject by:', options=sectionmgr_list, textvariable=v_approve0, default_text="ex.Kritsakon.P", scaling_factor=scaling_factor, toggle_var=True, fg='Grey', x_position=-34, frame_width=-90, widget_width=-39).place(x=18 * scaling_factor, y=110 * scaling_factor)

    logging.info("Reject window and fields created.")

def update_button_for_overview(parent_window, v_loto_no, v_work_title, v_lock_date, v_folder_location, refresh_gui3_callback):
    """Creates the update window for editing work details and refreshing the overview."""
    update_window, NewLoto_x, NewLoto_y = create_approve_reject_window('Update', 400, 270, parent=parent_window)

    # Canvas and labels setup
    canvas = tk.Canvas(update_window, width=NewLoto_x, height=NewLoto_y, background='#dcdad5')
    canvas.pack()
    ttk.Label(update_window, text="Update work detail", style="label1.TLabel").place(x=int(20 * scaling_factor), y=int(13 * scaling_factor))
    canvas.create_rectangle(16, 25, NewLoto_x - 17, NewLoto_y - 50, fill='#dcdad5', width=1, outline='#a9a7a3')

    # Buttons frame
    button_frame = tk.Frame(update_window, background="#dcdad5", borderwidth=1, relief="flat")
    button_frame.place(x=int(NewLoto_x - 216 * scaling_factor), y=int(NewLoto_y - 45 * scaling_factor), width=200 * scaling_factor, height=40 * scaling_factor)
    
    # CONFIRM button
    ttk.Button(button_frame, text="CONFIRM", style="Custom2.TButton", command=lambda: confirm_button_update(
        update_window, parent_window, v_loto_no, v_work_title, v_lock_date,
        v_pdf_update, v_override_update, v_remark, v_update, True, v_folder_location,
        refresh_treeview_callback=refresh_treeview, refresh_gui3_callback=refresh_gui3_callback
    )).pack(side=LEFT)

    # CLOSE button
    ttk.Button(button_frame, text="CLOSE(X)", style="Custom2.TButton", command=update_window.destroy).pack(side=RIGHT)

    # Input fields for update details
    v_pdf_update = StringVar()
    pdf_entry = pdf_new_for_update_button(update_window, 'P&ID Markup:', 28 * scaling_factor, 45 * scaling_factor, v_pdf_update)
    pdf_entry.place(x=28 * scaling_factor, y=45 * scaling_factor)

    v_override_update = StringVar()
    override_entry = pdf_new_for_update_button(update_window, 'Override:', 28 * scaling_factor, 80 * scaling_factor, v_override_update)
    override_entry.place(x=28 * scaling_factor, y=80 * scaling_factor)

    # Remark label and entry field
    ttk.Label(update_window, text='Remark:', style="label2.TLabel").place(x=28 * scaling_factor, y=115 * scaling_factor)
    v_remark = StringVar()
    input_field_remark_for_update_button(update_window, font=FONT7, scaling_factor=scaling_factor, textvariable=v_remark, placeholder="***Remark entry***", fg='grey', y_position=(115 * scaling_factor))

    # Approver label and dropdown
    v_update = StringVar()
    input_field_dropdown(update_window, label='Update by:', options=lomember_list, textvariable=v_update, default_text="ex.Kritsakon.P", scaling_factor=scaling_factor, toggle_var=True, fg='Grey', x_position=-34, frame_width=-70, widget_width=-20).place(x=18 * scaling_factor, y=180 * scaling_factor)

    # Block execution until the window is closed
    update_window.wait_window()
    
    # Refresh GUI3 once the update window is closed
    if refresh_gui3_callback:
        refresh_gui3_callback(v_loto_no, v_work_title, v_lock_date)


def confirm_button_update(update_window, detail_overview_GUI, v_loto_no, v_work_title, v_lock_date, v_pdf_update, v_override_update, v_remark, v_update, state, v_folder_location, refresh_treeview_callback=None, refresh_gui3_callback=None):
    """Confirms and processes the update by modifying the database and refreshing the display."""
    # Get the updated values
    remark_value = f"{date_str(3)} updated by {v_update.get().strip()}\n{v_remark.get().strip()}"
    pdf_value = v_pdf_update.get().strip()
    override_value = v_override_update.get().strip()

    logging.debug(f"Confirming update for LOTO No: {v_loto_no}")

    # Initialize file handling class instance
    file_handler = copy_rename_file_for_update_widget(pdf_value, override_value, v_folder_location)

    with conn:
        # Fetch existing values
        c.execute("""
            SELECT new_pid_pdf, new_override_list, new_remark
            FROM loto_new
            WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
            """, (v_loto_no, v_work_title, v_lock_date))
        result = c.fetchone()
        
        if result:
            existing_pdf, existing_override, existing_remark = result

            # Prepare updated values
            updated_remark = f"{existing_remark}\n{remark_value}" if remark_value else existing_remark
            updated_pdf = file_handler.rename_pdf() if pdf_value else existing_pdf
            updated_override = file_handler.rename_override() if override_value else existing_override

            # File transfers for updated PDF/Override
            if pdf_value:
                file_handler.transfer_pdf()
            if override_value:
                file_handler.transfer_override()

            # Update the database record
            c.execute("""
                UPDATE loto_new
                SET new_pid_pdf = ?, new_override_list = ?, new_remark = ?
                WHERE new_loto_no = ? AND new_work_title = ? AND new_lock_date = ?
                """, (updated_pdf, updated_override, updated_remark, v_loto_no, v_work_title, v_lock_date))
            conn.commit()
            logging.info(f"Updated LOTO No: {v_loto_no} with PDF: {updated_pdf}, Override: {updated_override}")

    # Refresh callbacks
    if refresh_treeview_callback:
        refresh_treeview_callback()
    if refresh_gui3_callback:
        refresh_gui3_callback(v_loto_no, v_work_title, v_lock_date)

    # Close the update window
    update_window.destroy()
