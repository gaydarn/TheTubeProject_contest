import os
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import datetime, threading, time
import serial
import Util
import sys
import glob
from socket import socket
from asyncio.windows_events import NULL

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def listCSVFilesInFolder(folderPath):
    """
    Crée une liste des fichiers avec l'extension .csv dans le dossier spécifié.

    Args:
        dossier (str): Chemin du dossier à parcourir.

    Returns:
        list: Liste des chemins des fichiers avec l'extension .csv.
    """
    CSVFilesList = []
    for file in os.listdir(folderPath):
        if file.endswith(".csv"):
            FilePath = os.path.join(folderPath, file)
            CSVFilesList.append(FilePath)
    return CSVFilesList

def LoadDataFile(fileName):
    # Création du chemin du fichier des données joint
    rep_base = ''
    filePath = os.path.join(os.getcwd(), rep_base, fileName)

    # Récupération des données joint
    series = pd.read_csv(filePath, header=0, sep=";")
    # Départ de l'index à 0ms
    series.index = series.index.values.astype(float) - float(series.index[0])

    return series


def formatFinalBufferintoDataFrame(_readingBuffer):
    _df = pd.DataFrame.from_records(_readingBuffer, columns=['time', 'setpoint', 'position'])
    _df['time'] = pd.to_datetime(_df['time'], format='%H:%M:%S.%f')
    _df = _df.set_index('time')
    _df['position'] = _df['position'].astype(float)
    _df['setpoint'] = _df['setpoint'].astype(float)

    return _df


def trajectory_generation(arduino, _traj_index, _traj_len, _traj_data, _stop_event,_traj_period = 0.1):

    while not _stop_event.is_set():
        next_call = time.time()

        write(arduino,f"traj={datetime.datetime.now().time()};{_traj_data.Setpoint[_traj_index]}\r\n")

        next_call = next_call + _traj_period
        if _traj_index < _traj_len:
            _traj_index = _traj_index + 10 * _traj_period
        else:
            _traj_index = 0
            break

        time_sleep = next_call - time.time()
        if time_sleep > 0 :
            time.sleep(time_sleep)
        else:
            print("!! Warning, time frame missed !!")


def write(arduino,x):
    #print("ArduinoSend:"+x)
    arduino.write(bytes(x, 'utf-8'))

def ReadArduioToServer(arduino, socket: socket, _stop_event):
    while not _stop_event.is_set():
        if arduino.inWaiting() > 0:
            try:
                line = arduino.readline().strip()
                #print(line)
                if (socket == NULL):
                    raise ValueError('A very specific bad thing happened.')
                socket.sendall(line)
            except Exception as error:  # this deals will the error

                print(error)
                break

def readToBuffer(arduino, readingBuffer, _stop_event):

    while not _stop_event.is_set():
        if arduino.inWaiting() > 0:
            try:
                line = arduino.readline().strip()
                values = line.decode('ascii').split(';')
                readingBuffer.append(tuple(values))
            except ValueError:  # this deals will the error
                print("!! Warning, Unable to put data in read buffer !!")
