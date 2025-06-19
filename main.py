## @file main.py
## @brief Start des Programms und ruft die ganzen funktionien auf
import os
# starten eines weiteren Prozesses durch ein bestehenden Prozess
import subprocess
# erlaubt eine verzögerung beim starten
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

# Importiert Methoden aus dem interface, discovery, UI_utils und netzwerkprozess 
from interface import (
    menue,
    nutzernamen_abfragen,
    eingabe_nachricht,
    eingabe_bild,
    autoreply_umschalten,
    autoreply_einschalten,
    lade_config, 
    finde_freien_port,
    erstelle_neue_config,
    finde_freien_tcp_port
)

from discovery import (
    zeige_bekannte_nutzer,
    discovery_main
)

 
'''from UI_utils import (
    lade_config, 
    finde_freien_port,
    erstelle_neue_config,
    finde_freien_tcp_port
)'''

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
# @brief Registiert einen neuen Nutzer im Chatnetzwerk
    ## @details finde_freien_port: es wird ein freier Port gesucht und ein Socket dadurch erstellt
    ## @details send_join: verschickt eine Join Nachricht an alle
## @param handle: der Benutzername des Teilnehmers
## @param config: die config Datei wird geldaden
## @return port: verwendeter UDP-Port des Nutzers
## @return nutzer_sock: der UDP-Socket, der an den Port gebunden ist

def registriere_neuen_nutzer(handle, config):
    port, nutzer_sock = finde_freien_port(config)
    send_join(handle,port)
    return port, nutzer_sock

## @brief Sendet einen Steuerbefehl über einen lokalen TCP-Socket an den Netzwerkprozess.
#  @details Diese Funktion wird vom UI-Prozess verwendet, um Nachrichten- oder Bildbefehle
#           (z. B. MSG oder IMG) an den Netzwerkprozess weiterzuleiten. Der Netzwerkprozess
#           übernimmt dann das eigentliche Senden per UDP an andere Chat-Teilnehmer.
#           Die Kommunikation erfolgt über eine TCP-Verbindung zu localhost:6001 FALSCH
#  @param befehl Der SLCP-kompatible Befehl, z. B. "MSG Bob Hallo" oder "IMG Bob pfad/zum/bild.jpg".
#  @note Wenn der Netzwerkprozess nicht läuft oder der Socket nicht erreichbar ist,
#        wird eine Fehlermeldung ausgegeben.
def sende_befehl_an_netzwerkprozess(befehl: str, tcp_port: int):
    try:
        with socket.create_connection(("localhost", tcp_port)) as sock:
            sock.sendall(befehl.encode())
    except ConnectionRefusedError:
        print("Netzwerkprozess läuft nicht!")




## Hauptfunktion
#  @brief startet alle funktionienen nach eingabe durch eingabe im Terminal
#  @details lädt das Menü und verwaltet den Ablauf
def main():
    # nutzername abfragen
    handle = nutzernamen_abfragen()
    # Dateipfad zusammenbauen um die richtige config zu laden
    konfig_pfad = f"Konfigurationsdateien/config_{handle.lower()}.toml"
    # Prüft, ob die Konfigurationsdatei für den angegebenen Benutzer bereits existiert.
    # Wenn nicht, wird automatisch eine neue Konfiguration angelegt (z. B. config_tuna.toml)
    if not os.path.exists(konfig_pfad):
        erstelle_neue_config(handle)  # Konfig anlegen, falls nicht vorhanden

    # Startet den Netzwerkprozess als separaten Hintergrundprozess.
    # Übergeben werden: Pfad zur Benutzer-Konfigurationsdatei und der dynamisch gewählte TCP-Port.
    # subprocess.Popen wird verwendet, damit dieser Prozess parallel zur UI läuft.
    # !Jetzt erst Netzwerkprozess starten
    tcp_port = finde_freien_tcp_port()
    subprocess.Popen(["python", "netzwerkprozess.py", konfig_pfad, str(tcp_port)])

    # Kurze Wartezeit, um sicherzustellen, dass der Netzwerkprozess genügend Zeit zum Hochfahren hat.
    # Verhindert Race Conditions bei späterer Kommunikation (z. B. TCP-Verbindung).
    time.sleep(1)
    # nutzernamen abfragen
   
   
    #ui_utils
    config = lade_config(konfig_pfad)
    #interface
    #netzwerkprozess(konfig_pfad)
    #threading.Thread(target=receive_MSG, args=(get_socket(), config), daemon=True).start()
    #main
    port, nutzer_sock = registriere_neuen_nutzer(handle,config)
   

    #print(f"Willkommen, {handle}! Dein Port: {port}")

    while True:
        auswahl = menue() # interface
        if auswahl == "1":
            print("→ WHO wird gesendet ...")
            try:
                # Öffnet eine TCP-Verbindung zum lokalen Netzwerkprozess (TCPport) 
                with socket.create_connection(("localhost", tcp_port)) as sock:
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
            empfaenger, text = eingabe_nachricht() # Interface
            befehl = f"MSG {empfaenger} {text}"
            sende_befehl_an_netzwerkprozess(befehl, tcp_port)
            continue
        elif auswahl == "3":
            empfaenger, pfad = eingabe_bild() # Interface
            befehl = f"IMG {empfaenger} {pfad}"
            sende_befehl_an_netzwerkprozess(befehl, tcp_port) # main
            continue
        elif auswahl == "4":
            autoreply_einschalten(config, konfig_pfad) # interface
            continue
        elif auswahl =="5":
            config = autoreply_umschalten(config, konfig_pfad) # interface
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
                sende_befehl_an_netzwerkprozess(f"LEAVE {handle}", tcp_port) # main
                break

            
       

## beginnt das Programm
#  @note Beim starten wird name durch main ersetzt, erst wenn es stimmt, wird die Main Funktion gestartet
if __name__ == "__main__":
    main()