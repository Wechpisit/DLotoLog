import os
import sqlite3
import sys
import json
from tkinter import messagebox

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

def connect_to_database(db_path):
    if not os.path.exists(db_path):  # Check if the database file exists
        messagebox.showerror("Network Error", "Please try to connect to the L: drive. or check 10.232.104.130")
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