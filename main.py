## @file main.py
##  @brief Start des Programms

## Importiert Methoden aus dem interface.py
import threading
## importiert socket
import socket
## importiert
import multiprocessing
#
from netzwerkprozess import netzwerkprozess
## Importiert Methoden aus dem interface.py
from interface import (
    menue,
    nutzernamen_abfragen,
    eingabe_nachricht,
    eingabe_bild,
    autoreply_umschalten
)

## Importiert Methoden aus dem UI_utils.py, discovery und message_handler
from discovery import nutzerspeichern, zeige_bekannte_nutzer
from UI_utils import lade_config, finde_freien_port
from message_handler import send_who, send_join, send_leave, sendMSG, sendIMG, receive_MSG, get_socket

#registriere_neuen_nutzer
#, _ heißt socket wird ignoriert
def registriere_neuen_nutzer(handle,config):
    port, nutzer_sock = finde_freien_port(config)
    send_join(handle,port)
    return port, nutzer_sock

## @brief Sendet einen Steuerbefehl über einen lokalen TCP-Socket an den Netzwerkprozess.
#  @details Diese Funktion wird vom UI-Prozess verwendet, um Nachrichten- oder Bildbefehle
#           (z. B. MSG oder IMG) an den Netzwerkprozess weiterzuleiten. Der Netzwerkprozess
#           übernimmt dann das eigentliche Senden per UDP an andere Chat-Teilnehmer.
#           Die Kommunikation erfolgt über eine TCP-Verbindung zu localhost:6001.
#
#  @param befehl Der SLCP-kompatible Befehl, z. B. "MSG Bob Hallo" oder "IMG Bob pfad/zum/bild.jpg".
#  @note Wenn der Netzwerkprozess nicht läuft oder der Socket nicht erreichbar ist,
#        wird eine Fehlermeldung ausgegeben.
def sende_befehl_an_netzwerkprozess(befehl: str):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", 6001))
        sock.sendall(befehl.encode())
        sock.close()
    except ConnectionRefusedError:
        print("Netzwerkprozess läuft nicht!")



## Hauptfunktion
#  @brief ruft funktionen aus den importierten Datei auf
#  @details lädt das Menü und verwaltet den Ablauf
def main():
    netzwerkprozess()
    #ui_utils
    config = lade_config()
    #interface
    handle = nutzernamen_abfragen()
    #main
    port, nutzer_sock = registriere_neuen_nutzer(handle,config)
    #message_handler
    # @para sock
    # @para config
    # programm läuft im hintergrund
    ## daemon=true schließt die funktion automatisch nach schließung des Programms
    threading.Thread(target=receive_MSG, args=(nutzer_sock, config), daemon=True).start()
    # NEU FÜR TCP-KOMMUNIKATION
    netzwerk_p = multiprocessing.Process(target=netzwerkprozess)
    netzwerk_p.start()
  
    print(f"Willkommen, {handle}! Dein Port: {port}")

    while True:
        ## aufrufen der Main methode
        #kommt aus dem interface
        auswahl = menue()
        if auswahl=="0":
            send_join(handle,port)
            continue
        elif auswahl == "1":
            print("→ WHO wird gesendet ...")
            # hier später Netzwerkfunktion einbinden
            send_who()
            continue
        #NEU FÜR TCP
        elif auswahl == "2":
         empfaenger, text = eingabe_nachricht()
         befehl = f"MSG {empfaenger} {text}"
         sende_befehl_an_netzwerkprozess(befehl)

        elif auswahl == "3":
         empfaenger, pfad = eingabe_bild()
         befehl = f"IMG {empfaenger} {pfad}"
         sende_befehl_an_netzwerkprozess(befehl)

        elif auswahl == "4":
            #interface
            config = autoreply_umschalten(config)
            print("→ Autoreply aktualisiert.")
            continue
        elif auswahl == "5":
            print("→ Aktuelle Konfiguration:")
            # config hat schlüssel und wert paare
            # k=kex(schlüssel) --> autoreply
            # v=(value)Wert --> text
            # gibt die schlüssel/Wert paare aus
            for k, v in config.items():
                print(f"  {k}: {v}")
            continue    
        elif auswahl == "6":
            print(f"→ LEAVE {handle}")
            break
            
       

## beginnt das Programm
#  @note Beim starten wird name durch main ersetzt, erst wenn es stimmt, wird die Main Funktion gestartet
if __name__ == "__main__":
    main()