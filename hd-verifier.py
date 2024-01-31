import os
import sys
import tkinter as tk
from tkinter import messagebox
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest
from enum import Enum

# pyrad workaround for Windows
import poll
poll.install()

import configparser
import os

def load_and_check_config():
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Check if required sections and options are present
    required = {
        'RADIUS': ['server', 'secret', 'timeout']
    }

    missing = {}
    for section, options in required.items():
        if not config.has_section(section):
            missing[section] = options
        else:
            for option in options:
                if not config.has_option(section, option):
                    if section not in missing:
                        missing[section] = []
                    missing[section].append(option)
    
    if missing:
        show_missing_config_dialog(missing)
        sys.exit()  # Exit the program

    return config

def show_missing_config_dialog(missing):
    message = (
        "Configuration file 'config.ini' is missing or incomplete.\n\n"
        "Please ensure that 'config.ini' is located in the same directory as the application.\n\n"
        "The following configuration is missing or incorrect:\n\n"
    )

    for section, options in missing.items():
        message += f"[{section}]\n"
        for option in options:
            message += f"{option} = \n"
    
    message += "\nExample configuration:\n"
    message += "[RADIUS]\nserver = example.com\nsecret = your_secret\ntimeout = 60"

    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showerror("Configuration Error", message)
    root.destroy()

# Load and check configuration
config = load_and_check_config()

# Configuration is correct, proceed with the application
RADIUS_SERVER_IP = config['RADIUS']['server']
RADIUS_SECRET = config['RADIUS']['secret'].encode('utf-8')
RADIUS_TIMEOUT = config['RADIUS'].getint('timeout')

# Define the dictionary data as a string
dict_data = """\
ATTRIBUTE   User-Name               1   string
ATTRIBUTE   User-Password           2   string
ATTRIBUTE   CHAP-Password           3   string
"""

# Write the dictionary data to a temporary file
dict_file_path = "temp_dictionary"
with open(dict_file_path, "w") as file:
    file.write(dict_data)

# Now, use this file path in the Dictionary object
radius_dict = Dictionary(dict_file_path)

# Clean up by deleting the temporary file
os.remove(dict_file_path)


# Define an Enum for RADIUS Response Codes
class RadiusResponseCodes(Enum):
    ACCESS_ACCEPT = 2
    ACCESS_REJECT = 3
    ACCESS_CHALLENGE = 11


def send_radius_request(username, otp):
    # Create a client object
    client = Client(
        server=RADIUS_SERVER_IP,
        secret=RADIUS_SECRET,
        dict=radius_dict,
        timeout=RADIUS_TIMEOUT,
        retries=1,
    )

    # Create a request packet
    req = client.CreateAuthPacket(code=AccessRequest, User_Name=username)
    req["User-Password"] = req.PwCrypt(otp)

    # Send the request and get the response
    try:
        response = client.SendPacket(req)
    except Exception as e:
        return f"Error: radius timeout? {e}"

    # Log the raw response for debugging
    print(f"Raw Response: {response} code {response.code}")

    # Use Enum for comparison
    if response.code == RadiusResponseCodes.ACCESS_ACCEPT.value:
        return "User ID Verified"
    elif response.code == RadiusResponseCodes.ACCESS_REJECT.value:
        return "User ID Verification Failed"
    elif response.code == RadiusResponseCodes.ACCESS_CHALLENGE.value:
        return "User ID Not Verified (Challenge)"
    else:
        return f"Error: Unexpected response code: {response.code}"


# Update your event handlers to use manage_notification
def on_submit():
    username = username_entry.get()
    otp = otp_entry.get()
    if not username or not otp:
        manage_notification("Please enter all required fields", "red")
    else:
        manage_notification("Verifying...", "gray")
        result = send_radius_request(username, otp)
        if "User ID Verified" in result:
            manage_notification(result, "green")
        else:
            manage_notification(result, "red")

def on_push_otp():
    username = username_entry.get()
    if not username:
        manage_notification("Please enter the username", "red")
    else:
        manage_notification("Verifying...", "gray")
        result = send_radius_request(username, "p")
        if "User ID Verified" in result:
            manage_notification(result, "green")
        else:
            manage_notification(result, "red")


# Get the path to the script or the PyInstaller bundle directory
if getattr(sys, 'frozen', False):
    # If the script is frozen (PyInstaller bundle)
    app_path = sys._MEIPASS
else:
    # If running from a script
    app_path = os.path.dirname(os.path.abspath(__file__))


# Create the main Tkinter window
root = tk.Tk()
root.withdraw() # Hide the window while setting up

# Load the icon from the bundled resource
icon_path = os.path.join(app_path, 'main.ico')

if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print("Icon file not found:", icon_path)

# Padding around the entire window
root.configure(padx=20, pady=20)

# Disable resizing of the window
root.resizable(False, False)

# Set a fixed size for the main window to prevent resizing
root.geometry("400x650")

# Add a title to the window
root.title("Helpdesk ID Verifier")

# Create a frame for the logo and title
logo_title_frame = tk.Frame(root)
logo_title_frame.pack(fill="x", expand=False, padx=(5, 0), pady=(20, 40))  # Use pack to ensure they stay close together


# Load the logo from the bundled resource
logo_path = os.path.join(app_path, 'logo.png')

# Load the PNG image using PhotoImage
image = tk.PhotoImage(file=logo_path) 

# Create a label to display the image
image_label = tk.Label(logo_title_frame, image=image)
image_label.pack(side="left", padx=(10, 0))  # Place the image label to the left

# Title
title_label = tk.Label(logo_title_frame, text="Helpdesk ID Verifier", font=("Helvetica", 20))
title_label.pack(side="left", padx=(10, 0))  # Add some padding between the image and title


# Frame for Username
username_frame = tk.Frame(root)
username_frame.pack(fill='x', pady=(0, 20))  # Maintain your original padding here

# Username Label
username_label = tk.Label(username_frame, text="SafeNet User ID", font=("Helvetica", 14),  fg="#505050")
username_label.pack(side='top', anchor='w', padx=(40))  # Align to left (west)

# Username Entry
username_entry = tk.Entry(username_frame, width=24, font=("Helvetica", 18))
username_entry.pack(side='top', fill='x', padx=(40), pady=(5, 0))  # Original padding

# Frame for OTP
otp_frame = tk.Frame(root)
otp_frame.pack(fill='x', pady=(0, 50))  # Maintain your original padding here

# OTP Label
otp_label = tk.Label(otp_frame, text="One-Time Password (OTP)", font=("Helvetica", 14),  fg="#505050")
otp_label.pack(side='top', anchor='w', padx=(40))  # Align to left (west)

# OTP Entry
otp_entry = tk.Entry(otp_frame, width=24, font=("Helvetica", 18))
otp_entry.pack(side='top', fill='x', padx=(40))  # No padding needed here as per your original setup


# Submit Button
submit_button = tk.Button(
    root, text="Submit OTP", command=on_submit, height=3, width=25, font=("Helvetica", 14),
    bg='#505050', fg='white'  # Example of a darker gray
)
submit_button.pack(pady=5)

# Push OTP Button (moved after the Submit button)
push_otp_button = tk.Button(
    root,
    text="Send Push Notification",
    command=on_push_otp,
    height=3,
    width=25,
    font=("Helvetica", 14),
    bg='#505050', fg='white'  # Matching darker gray
)
push_otp_button.pack(pady=(5, 25))


def manage_notification(message='', bg_color='SystemButtonFace'):
    if message:
        # Show notification with given message and background color
        notification_label.config(text=message, bg=bg_color)
        notification_frame.config(bg=bg_color)
        close_label.config(bg=bg_color)
        notification_frame.pack(fill='both', pady=(5, 5))
        close_label.pack(side="right", padx=15, pady=15)
        root.update()
    else:
        # Hide notification
        notification_frame.pack_forget()
        close_label.pack_forget()

# Modify your existing notification frame setup
notification_frame = tk.Frame(root, bg='SystemButtonFace', height=80)
notification_frame.pack_propagate(False)
notification_frame.pack_forget()  # Initially hide the frame

notification_label = tk.Label(notification_frame, text='', font=('Helvetica', 14), fg='white', bg='SystemButtonFace')
notification_label.pack(side='left', fill='both', expand=True, padx=(40, 0), pady=(10, 10), anchor='w')  # Adjust padding and anchor


notification_label.bind("<Button-1>", lambda event: manage_notification())

close_label = tk.Label(
    notification_frame,
    text="X",
    font=("Helvetica", 16),
    fg="white",
    bg='SystemButtonFace',
)
close_label.bind("<Button-1>", lambda event: manage_notification())
close_label.pack(side='right', padx=(10, 10), pady=(10, 10))  # Adjust padding for close label

root.deiconify() # Show the window once everything is ready
root.mainloop()