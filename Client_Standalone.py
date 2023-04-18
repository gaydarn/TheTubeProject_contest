# Press Maj+F10 to execute

# Importation des librairie

import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import datetime, threading, time
import serial
import Util


TrajIndex = 0
TrajLen = 0
TrajData = pd.Series()


stop_event = threading.Event()

arduino = serial.Serial(port='COM7', baudrate=115200, timeout=.1)
readingBuffer = []

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('Chargement de la trajectoire')
    TrajData = Util.LoadDataFile('Trajectoire_TheTube.csv')
    TrajData.plot()
    TrajLen = TrajData.size - 1
    plt.show()

    print('Création du Thread de lecture des données de l\'arduino')
    ReadThread = threading.Thread(target=Util.readToBuffer, args=(arduino, readingBuffer), daemon=True)
    print('Création du Thread d\'écriture des informations de trajectoires')
    writeThread = threading.Thread(target=Util.trajectory_generation, args=(arduino, TrajIndex, TrajLen, TrajData, stop_event), daemon=True)

    print('Passage de l\'Arduino dans le mode du concours')
    Util.write(arduino,'contest')
    time.sleep(10)

    print('Démarrage des threads')
    ReadThread.start()
    writeThread.start()

    print('Concours en cours...')
    time.sleep(5) #TODO: Start/stop from server?

    print('Trajectoire terminée, arrêt du thread d\'écriture et passage de l\'Arduino en mode "Quiet"')
    stop_event.set()
    writeThread.join()
    Util.write(arduino,'contest') #Permet de forcer la consigne de départ à 0
    time.sleep(2)
    Util.write(arduino,'quiet')

    df_final = Util.formatFinalBufferintoDataFrame(readingBuffer)
    df_final.plot()
    plt.show()
