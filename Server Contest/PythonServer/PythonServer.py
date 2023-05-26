
##Server

from multiprocessing.connection import Client
import socket, time, sys
import threading
import pprint
import os
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import datetime, threading, time 
import tkinter as tk

TCP_IP = ''
TCP_PORT = 8888
BUFFER_SIZE = 1024

clientCount = 0
TrajIndex = 0
TrajLen = 0
TrajData = pd.Series()
SingleLoop = False
ExectueLoop = False
dt_string = 0
clientCount


class Application(tk.Frame):
    def __init__(self, master=None,my_var=0):
        super().__init__(master)
        self.master = master
        self.my_var = my_var
        self.pack()
        self.create_widgets()
        self.update_my_var()
        self.update_Etat()
        

    def create_widgets(self):
        # Bouton "Start"
        self.start_button = tk.Button(self, text="Start",relief="ridge",bg="green",bd=5,fg="white")
        

        # Bouton "Stop"
        self.stop_button = tk.Button(self, text="Stop",bg="red", fg="white")
        

        # Groupe de boutons radio pour sélectionner le type de boucle
        self.loop_type = tk.StringVar(value="1 boucle")
        self.loop_type_1 = tk.Radiobutton(self, text="1 boucle", variable=self.loop_type, value="1 boucle")
        self.loop_type_2 = tk.Radiobutton(self, text="boucle infinie", variable=self.loop_type, value="boucle infinie")
        self.client_label = tk.Label(self, text="Nombre de client: 0")
        self.Etat_label = tk.Label(self, text="Etat du cicle: ")
        
        
        # Lier les boutons aux méthodes correspondantes
        self.start_button.bind("<Button-1>", self.start_loop)
        self.stop_button.bind("<Button-1>", self.stop_loop)


        self.stop_button.config(width=20, height=5)
        self.start_button.config(width=20, height=5)
        self.client_label.config(borderwidth=2, relief="groove")

        #Placement des composentes
        self.loop_type_1.grid(row=1, column=0, padx=10, pady=10)
        self.loop_type_2.grid(row=1, column=1, padx=10, pady=10)
        self.stop_button.grid(row=0, column=1, padx=10, pady=10)
        self.start_button.grid(row=0, column=0, padx=10, pady=10)
        self.client_label.grid(row=2, column=0, padx=10, pady=10 )
        self.Etat_label.grid(row=3, column=0, padx=10, pady=10 )

    def update_my_var(self):
        global clientCount
        self.client_label.configure(text="Nombre de client: " + str(clientCount))
        self.after(1000, self.update_my_var)
    def update_Etat(self):
        global ExectueLoop
        if ExectueLoop ==True:
            if self.loop_type.get() == "1 boucle":
                self.Etat_label.configure(text="Etat du cicle: Boucle unique en cours")
            else:
               self.Etat_label.configure(text="Etat du cicle: Boucle infinit en cours")
        else:
            self.Etat_label.configure(text="Etat du cicle: Arreté")
        self.after(100, self.update_Etat)

    def start_loop(self, event):
        global SingleLoop, ExectueLoop,dt_string,TrajIndex
        if TrajIndex == 0:
            if self.loop_type.get() == "1 boucle":
                print("Démarrage de la boucle unique")
                SingleLoop = True
                ExectueLoop = True
                today = datetime.datetime.now()
                dt_string = today.strftime("%d-%m-%Y_%H-%M-%S")
                # Mettez ici votre code pour la boucle unique
            else:
                print("Démarrage de la boucle infinie")
                SingleLoop = False
                ExectueLoop = True
                today = datetime.datetime.now()
                dt_string = today.strftime("%d-%m-%Y_%H-%M-%S")
                # Mettez ici votre code pour la boucle infinie

    def stop_loop(self, event):
        global SingleLoop, ExectueLoop
        print("Arrêt de la boucle")
        SingleLoop = False
        ExectueLoop = False
        s._broadcast(f"traj={datetime.datetime.now().time()};0")
        # Mettez ici le code pour arrêter votre boucle





def LoadDataFile(fileName):
    # Cr�ation du chemin du fichier des donn�es joint
    rep_base = ''
    filePath = os.path.join(os.getcwd(), rep_base, fileName)

    # R�cup�ration des donn�es joint
    series = pd.read_csv(filePath, header=0, sep=";")
    # D�part de l'index � 0ms
    series.index = series.index.values.astype(float) - float(series.index[0])

    return series


def trajectory_generation():
    global TrajIndex
    global TrajLen
    global TrajData
    global ExectueLoop, clientCount
   
    next_call = time.time()
    while True:
        if(not (TrajIndex == TrajLen and SingleLoop) and ExectueLoop and clientCount>0):
            next_call = next_call + 0.1
            if len(s.CLIENTS) > 0 :
                print(f"ENVOI = traj={datetime.datetime.now().time()};{TrajData.Setpoint[TrajIndex]}")
                if TrajIndex == 0 :
                    #s._broadcast('contest')
                    s._broadcast('START')

                s._broadcast(f"traj={datetime.datetime.now().time()};{TrajData.Setpoint[TrajIndex]}")
            
                if TrajIndex < TrajLen:
                    TrajIndex = TrajIndex + 1
                else:
                    TrajIndex = 0
                    print('STOP')
            else:
           
                TrajIndex = 0
            sleep_time = next_call - time.time()
            if sleep_time>=0:
                time.sleep(next_call - time.time())
            else:
                print('!! Warning, slot time missed !!')
        elif (TrajIndex == TrajLen and SingleLoop):
            ExectueLoop = False
            next_call = time.time()
            TrajIndex = 0
            #s._broadcast('quiet')
            print('Single loop finish')
        elif (ExectueLoop == False):
            TrajIndex = 0
            next_call = time.time()
        else:
            ExectueLoop = False
            next_call = time.time()

class server():
    global ClientsNB
    def __init__(self):
        self.CLIENTS = []        


    def startServer(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((TCP_IP,TCP_PORT))
            s.listen(10)    ## Nombre de connection limit� a 10 
            while 1:
                client_socket, addr = s.accept()
                print ('Connected with ' + addr[0] + ':' + str(addr[1]))
                global clientCount
                
                # register client
                
                self.CLIENTS.append(client_socket)
                clientCount = len(self.CLIENTS)
                print(clientCount)
                if addr[0] == '127.0.0.2' :
                    threading.Thread(target=self.MasterHandler, args=(client_socket,addr[0],)).start()
                else :
                    threading.Thread(target=self.playerHandler, args=(client_socket,addr[0],)).start()
            s.close()
        except socket.error as msg:
            print ('Could Not Start Server Thread. Error Code : ') #+ str(msg[0]) + ' Message ' + msg[1]
          
            sys.exit()

    def MasterHandler(self, client_socket,addr):
        #send welcome msg to new client
        global SingleLoop,clientCount
        client_socket.send(bytes('Hello send START or STOP\r\n', 'UTF-8'))
        while 1:
            try :
                data = client_socket.recv(BUFFER_SIZE)
                if not data: 
                    break
                if (data == 'STOP' and SingleLoop) :
                    None
                print ('Data : ' + repr(data) + "\n")
                #data = data.decode("UTF-8")
           
                client_socket.send(bytes('TG\r\n','UTF-8'))
            except :
                None
        # the connection is closed: unregister
        self.CLIENTS.remove(client_socket)
        clientCount = len(self.CLIENTS)
        
   #client handler :one of these loops is running for each thread/player   
    def playerHandler(self, client_socket,addr):
        global clientCount, dt_string
        #send welcome msg to new client
        #client_socket.send(bytes('Hello ' + addr + '\r\n', 'UTF-8'))
        today = datetime.datetime.now()
        dt_string = today.strftime("%d-%m-%Y_%H-%M-%S")
        chemin_dossier = os.path.join(os.getcwd(), "Results")
        if not os.path.exists(chemin_dossier):
            os.mkdir(chemin_dossier)
        chemin = f'Results/{addr}'
        chemin_dossier = os.path.join(os.getcwd(), chemin)
        if not os.path.exists(chemin_dossier):     
            os.mkdir(chemin_dossier)
      
        while 1:
            try :
                
                data = client_socket.recv(BUFFER_SIZE)

                if not data: 
                    break
                
                f = open(f'{chemin}/{addr}_{dt_string}.csv','a')
                f.write(data.decode()+'\n')
                print (data.decode()+ "\r\n")
                f.close()
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                break

         # the connection is closed: unregister
        self.CLIENTS.remove(client_socket)
        clientCount = len(self.CLIENTS)
        
       

    def broadcast(self, message):

        for c in self.CLIENTS:
            c.send(message)

    def _broadcast(self,message):        
        for sock in self.CLIENTS:           
            try :
                self._send(sock,message )
            except socket.error:                
                sock.close()  # closing the socket connection
                self.CLIENTS.remove(sock,message)  # removing the socket from the active connections list

    def _send(self, sock, message):      
        try :
            sock.send(bytes(message + '\r\n', 'UTF-8'))
        except:
            sock.close()
            None






root = tk.Tk()


if __name__ == '__main__':
    s = server() #create new server listening for connections
    threading.Thread(target=s.startServer).start()
    TrajData = LoadDataFile('..\..\Trajectoire_TheTube.csv')
    TrajData.plot()
    TrajLen = TrajData.size-1
    ##plt.show()
    timerThread = threading.Thread(target=trajectory_generation)
    timerThread.daemon = True
    timerThread.start()
    app = Application(master=root,my_var=clientCount)
    app.master.geometry("400x300")  # Changer la taille de la fenêtre à 400x300 pixels
    app.mainloop()
    print(clientCount)
        
        
        

       