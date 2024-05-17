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
runContest = True;


customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

app = customtkinter.CTk()  # create CTk window like you do with the Tk window
app.geometry("600x400")

ctkCol_L = 0.35
ctkCol_R = 0.65
ctkCol_C = 0.5

#*******************Choix du port COM***********************
#Titre pour le choix du port COM de l'arduino
label_COMChoice = customtkinter.CTkLabel(app, text="Choix port COM Auto", fg_color="transparent")
label_COMChoice.place(relx=ctkCol_C, rely=0.2, anchor=customtkinter.CENTER)

#Liste déroulante pour le choix du port COM de l'arduino
def combobox_COMChoice_callback(choice):
        print("combobox dropdown clicked:", choice)
        combobox_COMChoice.set(choice)
    ###
combobox_COMChoice = customtkinter.CTkComboBox(app, values=Util.serial_ports(),
                                                 command=combobox_COMChoice_callback)
combobox_COMChoice.place(relx=ctkCol_C, rely=0.3, anchor=customtkinter.CENTER)
#*******************Choix du port COM***********************


#*******************Choix de la trajectoire***********************
#def combobox_TrajChoice_callback(choice):
        #print("combobox dropdown clicked:"+ choice)
        #combobox_TrajChoice.set(choice)

#combobox_TrajChoice = customtkinter.CTkComboBox(app, values=Util.listCSVFilesInFolder(os.path.join(os.getcwd(),"Trajectory")),
#                                              command=combobox_TrajChoice_callback, width=300)#app.size[1]*0.8)

#combobox_TrajChoice.place(relx=ctkCol_R, rely=0.5, anchor=customtkinter.CENTER)
#label_TrajChoice = customtkinter.CTkLabel(app, text="Choix de la trajectoire", fg_color="transparent")
#label_TrajChoice.place(relx=ctkCol_R, rely=0.4, anchor=customtkinter.CENTER)
#*******************Choix du port COM***********************

#*******************Adresse IP***********************
label_IP = customtkinter.CTkLabel(app, text="Adresse IP", fg_color="transparent")
label_IP.place(relx=ctkCol_C, rely=0.4, anchor=customtkinter.CENTER)
entry_IP = customtkinter.CTkEntry(app, placeholder_text="Enter serveur IP")
entry_IP.place(relx=ctkCol_C, rely=0.5, anchor=customtkinter.CENTER)
#*******************Adresse IP***********************

#*******************Gestion du process***********************
def bpStart_function():
    global runContest
    print("Start pressed")
    bpStart.configure(state="disabled")
    runContest=True
    ReadMainAppStartThread = threading.Thread(target=MainAppStart, daemon=True)
    ReadMainAppStartThread.start()
    bpStart.configure(state="normal")


bpStart = customtkinter.CTkButton(master=app, text="Start", command=bpStart_function)
bpStart.place(relx=ctkCol_L, rely=0.7, anchor=customtkinter.CENTER)


def bpStop_function():
    global runContest
    print("Stop pressed")
    runContest = False
    stop_event.set()


bpStop = customtkinter.CTkButton(master=app, text="Stop", command=bpStop_function)
bpStop.place(relx=ctkCol_R, rely=0.7, anchor=customtkinter.CENTER)

#def ctKTBPrint(message):
        #ctKTextBox.insert(customtkinter.END, message + '\n')

#ctKTextBox = customtkinter.CTkTextbox(master=app, width=700, height=200)
#ctKTextBox.place(relx=ctkCol_C, rely=0.8, anchor=customtkinter.CENTER)
#*******************Gestion du process***********************
def appStandalone(arduino_Auto,  readingBuffer):
    print('Démarrage en standalone')
    print('Chargement de la trajectoire')
    TrajData = Util.LoadDataFile('Trajectoire_TheTube.csv')
    TrajData.plot()
    TrajLen = TrajData.size - 1
    plt.show()

    print('Création du Thread de lecture des données de l\'arduino')
    ReadThread = threading.Thread(target=Util.readToBuffer, args=(arduino_Auto, readingBuffer, stop_event), daemon=True)
    print('Création du Thread d\'écriture des informations de trajectoire')
    writeThread = threading.Thread(target=Util.trajectory_generation,
                                   args=(arduino_Auto, TrajIndex, TrajLen, TrajData, stop_event), daemon=True)
    stop_event.clear()

    print('Passage de l\'Arduino dans le mode du concours')
    Util.write(arduino_Auto, 'contest')
    # Util.write(arduino_Man, 'start')
    time.sleep(10)

    print('Démarrage des threads')
    ReadThread.start()
    writeThread.start()

    print('Concours en cours, attente de la fin de la génération de trajectoire')
    # time.sleep(2 * 60)  # TODO: Start/stop from server?
    writeThread.join()
    print('Trajectoire terminée, arrêt du thread de lecture et passage de l\'Arduino en mode "Quiet"')
    stop_event.set()


def appContest(arduino_Auto, _stop_event,  ipAddr='127.0.0.1'):
    global runContest
    Start = False
    connected = False

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Tentative de connexion au serveur : ')
    while (not connected) and (not _stop_event.is_set()):
        # attempt to reconnect, otherwise sleep for 2 seconds
        try:
            client_socket.connect((ipAddr, 8888))
            connected = True
            print('Connexion réussie!')
            ReadThread = threading.Thread(target=Util.ReadArduioToServer, args=(arduino_Auto, client_socket,_stop_event,), daemon=True)
            ReadThread.start()

        except socket.error:
            print('Echec! : Nouvelle tentative...')
            sleep(2)

    while not _stop_event.is_set():
        try:
            data = client_socket.recv(1024)

            if data.decode() == 'STOP\r\n':
                client_socket.send(b'STOP')
                Start = False
                _stop_event.set()
            elif data.decode() == 'START\r\n':
                Start = True
            elif data.decode() == 'contest\r\n':
                Util.write(arduino_Auto, 'contest')
            elif data.decode() == 'quiet\r\n':
                Util.write(arduino_Auto, 'quiet')
            elif "traj" in data.decode():
                Util.write(arduino_Auto, data.decode())

        except socket.error as exc:
            print("Caught exception socket.error : %s" % exc)

    if connected:
        client_socket.send(b'STOP')
        Util.write(arduino_Auto, 'quiet')

#Méthode appelée à la pression sur le bouton start. En fonction des choix sur l'interface,
# se connecte au serveur ou commence à envoyer la trajectoire sélectionnée.
def MainAppStart():
    ##time.sleep(5)

    arduino_Auto = serial.Serial(port=combobox_COMChoice.get(), baudrate=115200, timeout=.1)
    readingBuffer = []

    print('Démarrage du client en mode contest...')
    #Choix du mode du client, serveur ou standalone
    _ip = entry_IP.get()
    contestThread = threading.Thread(target=appContest, args=(arduino_Auto, stop_event, _ip,),daemon=True)
    contestThread.start()
    #appContest(arduino_Auto, readingBuffer, client_socket, stop_event, ipAddr=entry_IP.get())
    #appStandalone(arduino_Auto, readingBuffer)
    print('Contest en cours...')
    contestThread.join()
    #Util.write(arduino_Auto, 'contest')  # Permet de forcer la consigne de départ à 0
    time.sleep(2)
    Util.write(arduino_Auto, 'quiet')
    #Util.write(arduino_Man, 'quiet')

    print('Concours terminé')
    #df_final = Util.formatFinalBufferintoDataFrame(readingBuffer)
    #df_final.plot()
    #fig_final = plt.gcf()
    #plt.show()

    # Saving the different results into files
    #rep_base = 'LastRun'

    #df_final.to_csv(os.path.join(os.getcwd(), rep_base, 'final_traj.csv'))
    #fig_final.savefig(os.path.join(os.getcwd(), rep_base, 'final_traj.png'))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    app.mainloop()

    exit(0)





