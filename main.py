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
        with socket.create_connection(("localhost", 6001)) as sock:
            sock.sendall(befehl.encode())
    except ConnectionRefusedError:
        print("Netzwerkprozess läuft nicht!")




## Hauptfunktion
#  @brief ruft funktionen aus den importierten Datei auf
#  @details lädt das Menü und verwaltet den Ablauf
def main():
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

    print(f"Willkommen, {handle}! Dein Port: {port}")

    while True:
        ## aufrufen der Main methode
        #kommt aus dem interface
        auswahl = menue()
        if auswahl=="0":
           sende_befehl_an_netzwerkprozess(f"JOIN {handle} {port}")
           continue
        
                ## @brief Behandelt Menüauswahl "1" – WHO-Befehl senden und bekannte Nutzer anzeigen.
        #  @details Diese Funktion sendet den WHO-Befehl über eine TCP-Verbindung an den
        #           Netzwerkprozess (localhost:6001). Der Netzwerkprozess führt den WHO-Broadcast
        #           im LAN aus, sammelt die Antworten (KNOWNUSERS) und sendet sie per TCP zurück.
        #           Diese Rückmeldung wird hier analysiert und im UI ausgegeben.
        elif auswahl == "1":
            print("→ WHO wird gesendet ...")
            try:
                # Öffnet eine TCP-Verbindung zum lokalen Netzwerkprozess (Port 6001)
                with socket.create_connection(("localhost", 6001)) as sock:
                    # Sendet den WHO-Befehl (als Bytefolge)
                    sock.sendall(b"WHO")

                    # Wartet auf Antwort (z. B. "KNOWNUSERS Alice 192.168.0.2 5000, Bob ...")
                    antwort = sock.recv(4096).decode().strip()

                    if antwort.startswith("KNOWNUSERS"):
                        print("Bekannte Nutzer:")
                        teile = antwort.split(" ", 1)

                        if len(teile) == 2:
                            eintraege = teile[1].split(", ")

                            # Iteriert über alle bekannten Nutzer und gibt sie formatiert aus
                            for eintrag in eintraege:
                                try:
                                    handle, ip, port = eintrag.strip().split(" ")
                                    print(f"  {handle} → {ip}:{port}")
                                except ValueError:
                                    print("❌ Fehler beim Eintrag:", eintrag)
                    else:
                        print("⚠️ Unerwartete Antwort vom Netzwerkprozess:", antwort)

            except ConnectionRefusedError:
                print("Netzwerkprozess läuft nicht!")


        #NEU FÜR TCP
        elif auswahl == "2":
         empfaenger, text = eingabe_nachricht()
         befehl = f"MSG {empfaenger} {text}"
         sende_befehl_an_netzwerkprozess(befehl)
         continue
        elif auswahl == "3":
         empfaenger, pfad = eingabe_bild()
         befehl = f"IMG {empfaenger} {pfad}"
         sende_befehl_an_netzwerkprozess(befehl)
         continue
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