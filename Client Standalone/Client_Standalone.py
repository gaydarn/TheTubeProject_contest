# Press Maj+F10 to execute

# Importation des librairie
import os
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import datetime, threading, time
import serial
import Util
from scipy import integrate
import customtkinter
import sys
import time


TrajIndex = 0
TrajLen = 0
TrajData = pd.Series()


stop_event = threading.Event()


customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

app = customtkinter.CTk()  # create CTk window like you do with the Tk window
app.geometry("400x400")


def combobox_Auto_callback(choice):
    print("combobox dropdown clicked:", choice)
    combobox_Auto.set(choice)

combobox_Auto = customtkinter.CTkComboBox(app, values=Util.serial_ports(),
                                         command=combobox_Auto_callback)
combobox_Auto.place(relx=0.5, rely=0.3, anchor=customtkinter.CENTER)
label_Auto = customtkinter.CTkLabel(app, text="Choix port COM Auto", fg_color="transparent")
label_Auto.place(relx=0.5, rely=0.2, anchor=customtkinter.CENTER)


def bpStart_function():
    print("Start pressed")
    bpStart.configure(state="disabled")
    MainAppStart()
    bpStart.configure(state="normal")



# Use CTkButton instead of tkinter Button
bpStart = customtkinter.CTkButton(master=app, text="Start", command=bpStart_function)
bpStart.place(relx=0.5, rely=0.8, anchor=customtkinter.CENTER)

def MainAppStart():
    ##time.sleep(5)

    arduino_Auto = serial.Serial(port=combobox_Auto.get(), baudrate=115200, timeout=.1)
    #arduino_Man = serial.Serial(port=combobox_Manu.get(), baudrate=115200, timeout=.1)
    readingBuffer = []

    print('Chargement de la trajectoire')
    TrajData = Util.LoadDataFile('Trajectoire_TheTube.csv')
    TrajData.plot()
    TrajLen = TrajData.size - 1
    plt.show()

    print('Création du Thread de lecture des données de l\'arduino')
    ReadThread = threading.Thread(target=Util.readToBuffer, args=(arduino_Auto, readingBuffer), daemon=True)
    print('Création du Thread d\'écriture des informations de trajectoire')
    writeThread = threading.Thread(target=Util.trajectory_generation,
                                   args=(arduino_Auto, TrajIndex, TrajLen, TrajData, stop_event), daemon=True)

    print('Passage de l\'Arduino dans le mode du concours')
    Util.write(arduino_Auto, 'contest')
    #Util.write(arduino_Man, 'start')
    time.sleep(10)

    print('Démarrage des threads')
    ReadThread.start()
    writeThread.start()

    print('Concours en cours...')
    time.sleep(2 * 60)  # TODO: Start/stop from server?

    print('Trajectoire terminée, arrêt du thread d\'écriture et passage de l\'Arduino en mode "Quiet"')
    stop_event.set()
    writeThread.join()
    Util.write(arduino_Auto, 'contest')  # Permet de forcer la consigne de départ à 0
    time.sleep(2)
    Util.write(arduino_Auto, 'quiet')
    #Util.write(arduino_Man, 'quiet')

    print('Formattage du résultat final')
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





