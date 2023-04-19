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
import sys


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
    print('Création du Thread d\'écriture des informations de trajectoire')
    writeThread = threading.Thread(target=Util.trajectory_generation, args=(arduino, TrajIndex, TrajLen, TrajData, stop_event), daemon=True)

    print('Passage de l\'Arduino dans le mode du concours')
    Util.write(arduino, 'contest')
    time.sleep(10)

    print('Démarrage des threads')
    ReadThread.start()
    writeThread.start()

    print('Concours en cours...')
    time.sleep(2*60) #TODO: Start/stop from server?

    print('Trajectoire terminée, arrêt du thread d\'écriture et passage de l\'Arduino en mode "Quiet"')
    stop_event.set()
    writeThread.join()
    Util.write(arduino, 'contest') #Permet de forcer la consigne de départ à 0
    time.sleep(2)
    Util.write(arduino, 'quiet')

    print('Formattage du résultat final et calcul des statistiques')
    df_final = Util.formatFinalBufferintoDataFrame(readingBuffer)
    df_final.plot()
    fig_final = plt.gcf()
    plt.show()

    #Statistiques
    df_final['following_err'] = np.abs(df_final.position-df_final.setpoint)
    df_final['t_ms'] = df_final.index.values.astype(np.int64) // 10 ** 6
    df_final.t_ms = df_final.t_ms.values.astype(np.int64) - np.int64(df_final.t_ms[0])

    avg_int = integrate.trapz(df_final.following_err, x=df_final.t_ms.values) / np.int64(df_final.t_ms[-1])
    max_foll_err = np.max(df_final.following_err)
    avg_foll_err = np.mean(df_final.following_err)

    # Saving the different results into files
    rep_base = 'LastRun'

    df_final.to_csv(os.path.join(os.getcwd(), rep_base, 'final_traj.csv'))
    fig_final.savefig(os.path.join(os.getcwd(), rep_base, 'final_traj.png'))

    stats =  '***** Statistiques de l\'erreur de poursuite *****\r\n' \
            f'Moyenne : {avg_foll_err} mm\r\n' \
            f'Moyenne de l\'intégrale : {avg_int} mm\r\n' \
            f'Maximum : {max_foll_err} mm\r\n' \

    with open(os.path.join(os.getcwd(), rep_base, 'final_traj_stat.txt'), 'w') as f:
        f.write(stats)



