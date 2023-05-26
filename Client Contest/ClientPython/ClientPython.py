
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

#vars
##ComPort = sys.argv[1]
##print(ComPort)
#connect to server
global client_socket 
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = True

TrajIndex = 0
TrajLen = 0
TrajData = pd.Series()
SerialConnect = False

stop_event = threading.Event()

#while SerialConnect == False :
    #try :
arduino = serial.Serial(port='COM5', baudrate=115200, timeout=.1)
readingBuffer = []
Start = False
SerialConnect == True
    #except:
        #print('COM port not connected close all existing connection')
        #sleep(2)


if __name__ == '__main__':

    print('Creation thread')
    
    print('Passage de l\'Arduino dans le mode du concours')
    Util.write(arduino, 'contest')
    time.sleep(10)
    print('Demarage thread')
    print('Concours en cours...')

    

    
    while True:
        try :
            data = client_socket.recv(1024)  
            print(data.decode())
            if data.decode()=='contest\r\n':
                Util.write(arduino,'contest')
            if data.decode()=='quiet\r\n':
                Util.write(arduino,'quiet')
                Start = False
            if data.decode()=='STOP\r\n':
                client_socket.send(b'STOP')
                Start = False
            if Start == True :
                Util.write(arduino,data.decode())
            if data.decode()=='START\r\n':
                Start = True
            

        except socket.error as exc  :
            print ("Caught exception socket.error : %s" % exc)
            connected = False  
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print( "Waiting for connection to server" )  
            while not connected:  
                    # attempt to reconnect, otherwise sleep for 2 seconds  
                    try:  
                        client_socket.connect(('157.26.100.48',8888))
                        connected = True  
                        print( "connection successful" )  
                        ReadThread = threading.Thread(target=Util.ReadArduioToServer, args=(arduino,client_socket,), daemon=True)
                        ReadThread.start()

                    except socket.error:  
                        sleep( 2 )    


