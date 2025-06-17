## @file main.py
## @brief Start des Programms und ruft die ganzen funktionien auf
import subprocess
import time

# mehrere Aufgaben gleichzeitig im selben Prozess: eigehende Nachrichten, senden von Nachrichten ermöglichen 
import threading
# importiert socket
# kommunikation zwischen zwei Programmen(Prozessen)
import socket
# hat eigenen Speicher für jeden einzelnen Prozess des Projektes: e.g Netzwerkprozess und Discovery gleichzeitig laufen lassen
# pyhton Modul
import multiprocessing
# importiert die Klasse Process vom gesamten mulitprocessing Modul
from multiprocessing import Process

# Importiert Methoden aus dem interface.py
from interface import (
    menue,
    nutzernamen_abfragen,
    eingabe_nachricht,
    eingabe_bild,
    autoreply_umschalten,
    autoreply_einschalten
)

# Importiert Methoden aus dem discovery, UI_utils.py und netzwerkprozess
from discovery import (
    zeige_bekannte_nutzer,
    discovery_main
)
import os 
from UI_utils import (
    lade_config, 
    finde_freien_port,
    erstelle_neue_config
    
)

from netzwerkprozess import (
    send_join, 
    netzwerkprozess,
    send_leave, 
    sendMSG, 
    sendIMG, 
    receive_MSG, 
    get_socket 
)

# registriere_neuen_nutzer
# @brief 
# @param handle: den Benutzername der eingegeben wird
# @param config: die geladenen congig wird als Variable übergeben
def registriere_neuen_nutzer(handle,config):
    port, nutzer_sock = finde_freien_port(config)
    send_join(handle,port)
    return port, nutzer_sock

## @brief Sendet einen Steuerbefehl über einen lokalen TCP-Socket an den Netzwerkprozess.
#  @details Diese Funktion wird vom UI-Prozess verwendet, um Nachrichten- oder Bildbefehle
#           (z. B. MSG oder IMG) an den Netzwerkprozess weiterzuleiten. Der Netzwerkprozess
#           übernimmt dann das eigentliche Senden per UDP an andere Chat-Teilnehmer.
#           Die Kommunikation erfolgt über eine TCP-Verbindung zu localhost:6001
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
#  @brief ruft Funktionen aus den importierten Datei auf
#  @details lädt das Menü und verwaltet den Ablauf
def main():


    handle = nutzernamen_abfragen()
    konfig_pfad = f"Konfigurationsdateien/config_{handle.lower()}.toml"

    if not os.path.exists(konfig_pfad):
        erstelle_neue_config(handle)  # ❗Konfig anlegen, falls nicht vorhanden

    # Jetzt erst Netzwerkprozess starten
    subprocess.Popen(["python", "netzwerkprozess.py", konfig_pfad])
    time.sleep(1)
    # nutzernamen abfragen
   
   
    #ui_utils
    config = lade_config(konfig_pfad)
    #interface
    #netzwerkprozess(konfig_pfad)
    threading.Thread(target=receive_MSG, args=(get_socket(), config), daemon=True).start()
    #main
    port, nutzer_sock = registriere_neuen_nutzer(handle,config)
   

    print(f"Willkommen, {handle}! Dein Port: {port}")

    while True:
        ## aufrufen der Main methode
        #kommt aus dem interface
        auswahl = menue()
        if auswahl == "1":
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
                                    print(" Fehler beim Eintrag:", eintrag)
                    else:
                        print("Unerwartete Antwort vom Netzwerkprozess:", antwort)

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
            print("Hallo")
            autoreply_einschalten(config, konfig_pfad)
            continue
        elif auswahl =="5":
            #interface
            config = autoreply_umschalten(config, konfig_pfad)
            print("→ Autoreply aktualisiert.")
            continue
        elif auswahl == "6":
            print("→ Aktuelle Konfiguration:")
            # config hat schlüssel und wert paare
            # k=kex(schlüssel) --> autoreply
            # v=(value)Wert --> text
            # gibt die schlüssel/Wert paare aus
            for k, v in config.items():
                print(f"  {k}: {v}")
            continue    
        elif auswahl == "7":
                sende_befehl_an_netzwerkprozess(f"LEAVE {handle}")
                break

            
       

## beginnt das Programm
#  @note Beim starten wird name durch main ersetzt, erst wenn es stimmt, wird die Main Funktion gestartet
if __name__ == "__main__":
    main()