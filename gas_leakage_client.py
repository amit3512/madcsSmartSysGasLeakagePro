#! /usr/bin/python3

"""
This file contains GUI code for Configuring Air Monitoring HAT ans MG-2 Gas Sensor
Developed by Team 9, Smart Systems Module, MSc Advanced Computer Science, Leeds Beckett University, Original code provided by SB Components (http://sb-components.co.uk)
"""
import logging
import os
import threading
import tkinter as tk
import tkinter as ttk

from datetime import datetime, timedelta
from time import sleep
from tkinter import font
from tkinter import messagebox

# imports for Plotting
import matplotlib
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from air_monitoring_hat import AirReader
import smbus
import time
import socket
import json

host = '192.168.50.222'
port = 12345                   # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))

# I2C address for Pmod AD2
I2C_ADDRESS = 0x28  # Adjust this address based on the configuration of your Pmod AD2

# Initialize the I2C bus
bus = smbus.SMBus(1)  # 1 indicates /dev/i2c-1, for Raspberry Pi 3, use 0 for older models

matplotlib.use("TkAgg")

COMPORT_BASE = ""

if os.name == "posix":
    COMPORT_BASE = "/dev/"
    COMPORT = "ttyS0"
else:
    COMPORT = "COM"


class MainApp(tk.Tk):
    """
    This is a class for Creating Frames and Buttons for left and top frame
    """

    def __init__(self, *args, **kwargs):
        global logo, img, xy_pos

        tk.Tk.__init__(self, *args, **kwargs)

        self.screen_width = tk.Tk.winfo_screenwidth(self)
        self.screen_height = tk.Tk.winfo_screenheight(self)
        self.app_width = 800
        self.app_height = 480
        self.xpos = (self.screen_width / 2) - (self.app_width / 2)
        self.ypos = (self.screen_height / 2) - (self.app_height / 2)

        xy_pos = self.xpos, self.ypos

        self.geometry(
            "%dx%d+%d+%d" % (self.app_width, self.app_height, self.xpos,
                             self.ypos))
        self.title("Air Monitoring System")
        if not self.screen_width > self.app_width:
            self.attributes('-fullscreen', True)

        self.config(bg="gray85")

        img = tk.PhotoImage(file=path + '/Images/settings.png')
        logo = tk.PhotoImage(file=path + '/Images/sblogo.png')

        self.top_frame = tk.Frame(self, height=int(self.app_height / 12), bd=2,
                                  width=self.app_width, bg="green")
        self.top_frame.pack(side="top", fill="both")

        self.main_frame = tk.Frame(self, width=self.app_width, bg="gray85")
        self.main_frame.pack(side="bottom", fill="both")

        self.label_font = font.Font(family="Helvetica", size=10)
        self.heading_font = font.Font(family="Helvetica", size=12)

        tk.Label(self.top_frame, bg="green", fg="white",
                 text="Air Monitoring System",
                 font=font.Font(family="Helvetica", size=18)).place(x=250)
        tk.Label(self.top_frame, justify="left", bg="white", height=30,
                 fg="black", bd=2, image=logo).place(x=600,
                                                     y=1)

        frame = GraphFrame(parent=self.main_frame, controller=self)
        frame.config(bg="white")
        frame.grid(row=0, column=0, sticky="nsew")

        frame.tkraise()


class GraphFrame(tk.Frame):
    """
    This is a class for Creating widgets for Matplotlib Graph
    """

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.readFlag = False
        self.controller = controller
        #  Graph Variables
        base = datetime.now()
        self.xList = [base - timedelta(seconds=(i)) for i in range(50)]
        self.xList.reverse()
        self.pm_1_list = [0] * 50
        self.pm_10_list = [0] * 50
        self.pm_25_list = [0] * 50

        self.entry_font = font.Font(family="Helvetica", size=10)
        self.label_font = font.Font(family="Helvetica", size=12)

        self.healthy_img = tk.PhotoImage(file="Images/AQI_healthy.png")
        self.unhealthy_img = tk.PhotoImage(file="Images/AQI_unhealthy.png")
        self.hazardous_img = tk.PhotoImage(file="Images/AQI_hazardous.png")

        self.LARGE_FONT = ("Verdana", 12)
        style.use("ggplot")

        #  Checkbox Variables
        self.PM1Check = tk.IntVar()
        self.PM25Check = tk.IntVar()
        self.PM10Check = tk.IntVar()
        self.PM1Check.set(1)
        self.PM25Check.set(1)
        self.PM10Check.set(1)

        self.pm1_label = tk.Label(self, text="", width=10, bg="green",
                                  fg="white")
        self.pm1_label.grid(row=1, column=0)
        self.pm1_label.config(text="")
        tk.Checkbutton(self, text="PM 1.0", fg='green',
                       variable=self.PM1Check).grid(row=2, column=0, pady=10)

        self.pm25_label = tk.Label(self, text="", width=10, bg="red",
                                   fg="white")
        self.pm25_label.grid(row=1, column=1)
        self.pm25_label.config(text="")
        tk.Checkbutton(self, text="PM 2.5", fg='red',
                       variable=self.PM25Check).grid(row=2, column=1, pady=10)

        self.pm10_label = tk.Label(self, text="", width=10, bg="blue",
                                   fg="white")
        self.pm10_label.grid(row=1, column=2)
        self.pm10_label.config(text="")
        tk.Checkbutton(self, text="PM 10", fg='blue',
                       variable=self.PM10Check).grid(row=2, column=2, pady=10)

        #  Start Button
        self.start_button = ttk.Button(self, text="Start", bg="gray90",
                                       width=6,
                                       command=self.continousRead)
        self.start_button.grid(row=1, column=3)

        #  Close Button
        tk.Button(self, text="Close", bg="gray90", width=6,
                  command=self.close_window).grid(row=2, column=3)

        #  Graph Plotting
        self.ani = None

        self.fig = Figure(figsize=(5.5, 3.7), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.autofmt_xdate()
        self.ax.set_xlabel("Time", fontsize=10, color="blue")
        self.ax.set_ylabel("PM level", fontsize=10, color="green")

        self.date_format = matplotlib.dates.DateFormatter('%H:%M:%S')
        self.ax.xaxis.set_major_formatter(self.date_format)

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=0, column=0, padx=0, pady=0,
                                         rowspan=1, sticky="en", columnspan=4)

        #  Right Side Image Label
        self.img_label = tk.Label(self, justify="left", bg="white",
                                  fg="black", bd=2, image=self.healthy_img,
                                  height=250,
                                  width=250)
        self.img_label.grid(row=0, column=4, columnspan=2, padx=0, pady=5)
        self.img_label.image = self.healthy_img

        #  Serial
        com_label = tk.Label(self, bg="white", fg="Black",
                             text="Comm Port",
                             font=self.label_font)
        com_label.grid(row=1, column=4)

        self.com_entry = tk.Entry(self, width=15, bd=3,
                                  font=self.entry_font)
        self.com_entry.grid(row=1, column=5)
        self.com_entry.insert(0, COMPORT_BASE + COMPORT)

        self.circle = tk.Canvas(self, height=40, width=40, bg="white",
                                bd=0, highlightthickness=0)
        self.indication = self.circle.create_oval(10, 10, 30, 30, fill="red")
        self.circle.grid(row=2, column=4)

        self.connect_button = tk.Button(self, text="Connect",
                                        bg="gray90",
                                        font=self.label_font,
                                        command=self.connect_hat)
        self.connect_button.grid(row=2, column=5)

    def animate(self, i):
        self.ax.clear()
        self.ax.xaxis.set_major_formatter(self.date_format)
        self.fig.autofmt_xdate()
        self.ax.set_xlabel("Time", fontsize=10, color="blue")
        self.ax.set_ylabel("PM level", fontsize=10, color="green")

        if self.PM1Check.get():
            self.ax.plot(self.xList, self.pm_1_list, color='green')

        if self.PM25Check.get():
            self.ax.plot(self.xList, self.pm_25_list, color='red')

        if self.PM10Check.get():
            self.ax.plot(self.xList, self.pm_10_list, color='blue')

    def continousRead(self):
        """
        This function create thread to read params from servo motor
        """
        if robot.alive:
            if self.start_button.cget('text') == 'Start':
                self.readFlag = True
                self.threadContRead = threading.Thread(target=self.read_data)
                self.threadContRead.daemon = True
                self.threadContRead.start()

                if self.ani:
                    self.ani.event_source.start()
                    self.start_button.config(relief="sunken", text='Stop')

                elif self.ani is None:
                    self.ani = animation.FuncAnimation(self.fig, self.animate,
                                                       interval=1,
                                                       repeat=False)
                    self.ani._start()
                    # dates = matplotlib.dates.date2num([datetime.now()])
                    self.start_button.config(relief="sunken", text='Stop')

            elif self.start_button.cget('text') == 'Stop':
                # self.id_entry.config(state="normal")
                self.ani.event_source.stop()
                self.start_button.config(relief="raised", text='Start')

                self.readFlag = False

        else:
            messagebox.showerror("Comm Error",
                                 "Comm Port is not Connected..!!")

    def read_data(self):
        while self.readFlag:
            try:
                pm_1, pm_25, pm_10 = robot.update_data()

                self.xList.pop(0)
                self.xList.append(datetime.now())

                self.pm_1_list.pop(0)
                self.pm_1_list.append(pm_1)
                self.pm1_label.config(text=str(pm_1))

                self.pm_25_list.pop(0)
                self.pm_25_list.append(pm_25)
                self.pm25_label.config(text=str(pm_25))

                self.pm_10_list.pop(0)
                self.pm_10_list.append(pm_10)
                self.pm10_label.config(text=str(pm_10))
                #print('Air Quality Measurument 1:', pm_1)
                #print('Air Quality Measurument 2:', pm_25)
                #print('Air Quality Measurument 3:', pm_10) 
                voltage = readadc()  
                #print(f"Raw ADC Reading: {adc_reading}")
                #print(voltage)
                #variable_dict = {format(pm_1).encode(),format(voltage).encode()}
                variable_dict = {'v1':pm_25,'v2':voltage}
                serialized_data = json.dumps(variable_dict)
                #print('Air Quality Measurument 2:', serialized_data)
                s.sendall(serialized_data.encode())
                #s.sendall(format(pm_1).encode(), voltage)
                data_server = s.recv(1024)
                print(f"Received data: {repr(data_server)}")
                if "there is a gas leakage" in data_server.decode():
                    messagebox.showwarning("Gas Leakage Warning", "Gas leakage detected! Run to a safe place!")
                    self.img_label.image = self.hazardous_img
                                                    
                if pm_25 <= 25:
                    self.img_label.config(image=self.healthy_img)
                    self.img_label.image = self.healthy_img
                elif 25 < pm_25 <= 50:
                    self.img_label.config(image=self.unhealthy_img)
                    self.img_label.image = self.unhealthy_img
                elif pm_25 > 50:
                    self.img_label.config(image=self.hazardous_img)
                    self.img_label.image = self.hazardous_img
                    
            except TypeError:
                self.continousRead()
                messagebox.showerror("Response Error", "No Response from "
                                                       "Motor..!!")

    def close_window(self):
        """
        This function delete the temp folder and close PiArm
        """
        self.readFlag = False
        self.controller.destroy()

    def connect_hat(self):
        """
        This function connects the serial port
        """
        if self.connect_button.cget(
                'text') == 'Connect' and self.com_entry.get():
            robot.connect(self.com_entry.get(), 9600)
            if robot.alive:
                self.connect_button.config(relief="sunken", text="Disconnect")
                self.circle.itemconfigure(self.indication, fill="green3")
                self.com_entry.config(state="readonly")
            else:
                messagebox.showerror("Port Error",
                                     "Couldn't Connect with {} ".format(
                                         self.com_entry.get()))

        elif self.connect_button.cget('text') == 'Disconnect':
            self.connect_button.config(relief="raised", text="Connect")
            self.circle.itemconfigure(self.indication, fill="red")
            self.com_entry.config(state="normal")
            robot.disconnect()

    def ent_validate(self, new_value):
        """
        Validate the ID of servo in Operate frame
        """
        try:
            if not new_value or 0 < int(new_value) <= 253:
                return True
            else:
                self.bell()
                return False
        except ValueError:
            self.bell()
            return False

    def id_validate(self, new_value):
        """
        Validate the ID of servo in Operate frame
        """
        try:
            if not new_value or 0 < int(new_value) <= 253:
                return True
            else:
                self.bell()
                return False
        except ValueError:
            self.bell()
            return False

# Read ADC value from Pmod AD2 and convert to voltage

def readadc():
    try:
        # Pmod AD2 command format: read analog input channel 0 (single-ended)
        data = bus.read_i2c_block_data(I2C_ADDRESS, 0x40, 2)
        return data[1]
    except IOError:
        print("Error reading ADC")
        return -1
        
robot = None
logo = None
img = None
path = os.path.abspath(os.path.dirname(__file__))
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

if __name__ == "__main__":
    robot = AirReader()
    app = MainApp()
    app.tk.call('wm', 'iconphoto', app._w, img)
    app.resizable(0, 0)
    app.mainloop()
