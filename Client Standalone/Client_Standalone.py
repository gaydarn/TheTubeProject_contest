# Press Maj+F10 to execute

# Import des librairies
import os
import pandas as pd
from matplotlib import pyplot as plt
import threading
import serial
import Util
import customtkinter
import time
import socket
import sys
import json
from time import sleep
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import datetime, threading, time
import serial
import Util
from scipy import integrate

client_socket = 0


TrajIndex = 0
TrajLen = 0
TrajData = pd.Series()


stop_event = threading.Event()


customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

app = customtkinter.CTk()  # create CTk window like you do with the Tk window
app.geometry("800x600")

ctkCol_L = 0.25
ctkCol_R = 0.75
ctkCol_C = 0.5

#*******************Choix du port COM***********************
#Titre pour le choix du port COM de l'arduino
label_COMChoice = customtkinter.CTkLabel(app, text="Choix port COM Auto", fg_color="transparent")
label_COMChoice.place(relx=ctkCol_C, rely=0.2, anchor=customtkinter.CENTER)

#Liste déroulante pour le choix du port COM de l'arduino
def combobox_COMChoice_callback(choice):
        ctkTBPrint("combobox dropdown clicked:", choice)
        combobox_COMChoice.set(choice)
    ###
combobox_COMChoice = customtkinter.CTkComboBox(app, values=Util.serial_ports(),
                                                 command=combobox_COMChoice_callback)
combobox_COMChoice.place(relx=ctkCol_C, rely=0.3, anchor=customtkinter.CENTER)
#*******************Choix du port COM***********************


#*******************Choix de la trajectoire***********************
def combobox_TrajChoice_callback(choice):
        ctkTBPrint("combobox dropdown clicked:"+ choice)
        combobox_TrajChoice.set(choice)

combobox_TrajChoice = customtkinter.CTkComboBox(app, values=Util.listCSVFilesInFolder(os.path.join(os.getcwd(),"Trajectory")),
                                              command=combobox_TrajChoice_callback, width=300)#app.size[1]*0.8)

combobox_TrajChoice.place(relx=ctkCol_R, rely=0.5, anchor=customtkinter.CENTER)
label_TrajChoice = customtkinter.CTkLabel(app, text="Choix de la trajectoire", fg_color="transparent")
label_TrajChoice.place(relx=ctkCol_R, rely=0.4, anchor=customtkinter.CENTER)
#*******************Choix du port COM***********************

#*******************Adresse IP***********************
label_IP = customtkinter.CTkLabel(app, text="Adresse IP", fg_color="transparent")
label_IP.place(relx=ctkCol_L, rely=0.4, anchor=customtkinter.CENTER)
entry_IP = customtkinter.CTkEntry(app, placeholder_text="Enter serveur IP")
entry_IP.place(relx=ctkCol_L, rely=0.5, anchor=customtkinter.CENTER)
#*******************Adresse IP***********************

#*******************Gestion du process***********************
def bpStart_function():
        ctkTBPrint("Start pressed")
        bpStart.configure(state="disabled")
        MainAppStart()
        bpStart.configure(state="normal")

bpStart = customtkinter.CTkButton(master=app, text="Start", command=bpStart_function)
bpStart.place(relx=ctkCol_C, rely=0.6, anchor=customtkinter.CENTER)

def ctkTBPrint(message):
        ctKTextBox.insert(customtkinter.END, message + '\n')

ctKTextBox = customtkinter.CTkTextbox(master=app, width=700, height=200)
ctKTextBox.place(relx=ctkCol_C, rely=0.8, anchor=customtkinter.CENTER)
#*******************Gestion du process***********************
def appStandalone(arduino_Auto,  readingBuffer):
    ctkTBPrint('Démarrage en standalone')
    ctkTBPrint('Chargement de la trajectoire')
    TrajData = Util.LoadDataFile('Trajectoire_TheTube.csv')
    TrajData.plot()
    TrajLen = TrajData.size - 1
    plt.show()

    ctkTBPrint('Création du Thread de lecture des données de l\'arduino')
    ReadThread = threading.Thread(target=Util.readToBuffer, args=(arduino_Auto, readingBuffer, stop_event), daemon=True)
    ctkTBPrint('Création du Thread d\'écriture des informations de trajectoire')
    writeThread = threading.Thread(target=Util.trajectory_generation,
                                   args=(arduino_Auto, TrajIndex, TrajLen, TrajData, stop_event), daemon=True)
    stop_event.clear()

    ctkTBPrint('Passage de l\'Arduino dans le mode du concours')
    Util.write(arduino_Auto, 'contest')
    # Util.write(arduino_Man, 'start')
    time.sleep(10)

    ctkTBPrint('Démarrage des threads')
    ReadThread.start()
    writeThread.start()

    ctkTBPrint('Concours en cours, attente de la fin de la génération de trajectoire')
    # time.sleep(2 * 60)  # TODO: Start/stop from server?
    writeThread.join()
    ctkTBPrint('Trajectoire terminée, arrêt du thread de lecture et passage de l\'Arduino en mode "Quiet"')
    stop_event.set()


def appContest(arduino_Auto, readingBuffer, client_socket, ipAddr='127.0.0.1'):
    #ctkTBPrint('Démarrage en mode contest')
    Start = False
    connected = False
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ctkTBPrint('Tentative de connexion au serveur : ')
    while not connected:
        # attempt to reconnect, otherwise sleep for 2 seconds
        try:
            client_socket.connect((ipAddr, 8888))
            connected = True
            ctkTBPrint('Connexion réussie!')
            ReadThread = threading.Thread(target=Util.ReadArduioToServer, args=(arduino_Auto, client_socket,), daemon=True)
            ReadThread.start()

        except socket.error:
            ctkTBPrint('Echec! : Nouvelle tentative...')
            sleep(2)

    while True:
        try:
            data = client_socket.recv(1024)

            if data.decode() == 'STOP\r\n':
                client_socket.send(b'STOP')
                Start = False
            elif data.decode() == 'START\r\n':
                Start = True
            elif data.decode() == 'contest\r\n':
                Util.write(arduino_Auto, 'contest')
            elif data.decode() == 'quiet\r\n':
                Util.write(arduino_Auto, 'quiet')
            elif "traj" in data.decode():
                Util.write(arduino_Auto, data.decode())

            #if data.decode() == 'contest\r\n':
                #Util.write(arduino_Auto, 'contest')
            #if data.decode() == 'quiet\r\n':
                #Util.write(arduino_Auto, 'quiet')
                #Start = False
            #if data.decode() == 'STOP\r\n':
                #client_socket.send(b'STOP')
                #Start = False
            #if Start == True:
                #Util.write(arduino_Auto, data.decode())
            #if data.decode() == 'START\r\n':
                #Start = True



        except socket.error as exc:
            print("Caught exception socket.error : %s" % exc)

#Méthode appelée à la pression sur le bouton start. En fonction des choix sur l'interface,
# se connecte au serveur ou commence à envoyer la trajectoire sélectionnée.
def MainAppStart():
    ##time.sleep(5)

    arduino_Auto = serial.Serial(port=combobox_COMChoice.get(), baudrate=115200, timeout=.1)
    readingBuffer = []

    #Choix du mode du client, serveur ou standalone
    appContest(arduino_Auto, readingBuffer, client_socket, ipAddr=entry_IP.get())
    #appStandalone(arduino_Auto, readingBuffer)

    #Util.write(arduino_Auto, 'contest')  # Permet de forcer la consigne de départ à 0
    time.sleep(2)
    Util.write(arduino_Auto, 'quiet')
    #Util.write(arduino_Man, 'quiet')

    ctkTBPrint('Formattage du résultat final')
    df_final = Util.formatFinalBufferintoDataFrame(readingBuffer)
    df_final.plot()
    fig_final = plt.gcf()
    plt.show()

    # Saving the different results into files
    rep_base = 'LastRun'

    df_final.to_csv(os.path.join(os.getcwd(), rep_base, 'final_traj.csv'))
    fig_final.savefig(os.path.join(os.getcwd(), rep_base, 'final_traj.png'))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    app.mainloop()

    exit(0)





