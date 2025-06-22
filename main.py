## @file main.py
# @brief Start des Programms und ruft die ganzen funktionien auf

# erlaubt eine verzögerung beim starten
import time
# hat eigenen Speicher für jeden einzelnen Prozess des Projektes: z.B. Netzwerkprozess und Discovery gleichzeitig laufen lassen
import multiprocessing
# importiert socket
# kommunikation zwischen zwei Programmen(Prozessen)
import socket

# Importiert Methoden aus dem interface, discovery, netzwerkprozess und nutzerliste
from interface import (
    menue,
    nutzernamen_abfragen,
    eingabe_nachricht,
    eingabe_bild,
    autoreply_umschalten,
    autoreply_einschalten,
    lade_config, 
    finde_freien_port,
    finde_freien_tcp_port
)

from discovery import (
    discovery_main
)

from netzwerkprozess import (
    send_join,  
    starte_netzwerkprozess
)
# verwendet, um gemeinsam nutzbares Objekte zwischen Prozessen zu erzeugen
# hat eigenen Speicher für jeden einzelnen Prozess des Projektes: z.B. Netzwerkprozess und Discovery gleichzeitig laufen lassen
# importiert die Klasse Process vom gesamten mulitprocessing Modul
from multiprocessing import(
    Manager,
    Process
)
# Nutzerverzeichnis
from nutzerliste import (
    initialisiere_nutzerliste
)

# --------Regiestiere neuen Nutzer--------
## @brief Registiert einen neuen Nutzer im Chatnetzwerk
    # @details finde_freien_port: es wird ein freier Port gesucht und ein Socket dadurch erstellt
    # @details send_join: verschickt eine Join Nachricht an alle
# @param handle: der Benutzername des Teilnehmers
# @param config: die config Datei wird geldaden
# @return port: verwendeter UDP-Port des Nutzers
# nutzer_sock: der UDP-Socket, der an den Port gebunden ist

def registriere_neuen_nutzer(handle, config):
    port, nutzer_sock = finde_freien_port(config)
    DISCOVERY_PORT = config["network"]["whoisdiscoveryport"]
    send_join(nutzer_sock, handle,port, DISCOVERY_PORT)
    nutzer_sock.close()  # Port bleibt "reserviert" bis zum neuen Binden im Netzwerkprozess
    return port

# --------Befehl an Netzwerkprozess--------
## @brief Sendet einen Steuerbefehl über einen lokalen TCP-Socket an den Netzwerkprozess
# @details Diese Funktion wird vom UI-Prozess verwendet, um Nachrichten- oder Bildbefehle
#           (z. B. MSG oder IMG) an den Netzwerkprozess weiterzuleiten.
#           Der Netzwerkprozess übernimmt dann das eigentliche Senden per UDP an andere Chat-Teilnehmer.
#           Die Kommunikation erfolgt über eine TCP-Verbindung zu localhost:6001
# @param befehl Der SLCP-kompatible Befehl, z. B. "MSG Bob Hallo" oder "IMG Bob pfad/zum/bild.jpg".
# @param tcp_port verbindet netzwerkprozess mit Main
# @note Wenn der Netzwerkprozess nicht läuft oder der Socket nicht erreichbar ist, wird eine Fehlermeldung ausgegeben.
def sende_befehl_an_netzwerkprozess(befehl: str, tcp_port: int):
    try:
        with socket.create_connection(("localhost", tcp_port)) as sock:
            sock.sendall(befehl.encode())
    except ConnectionRefusedError:
        print("Netzwerkprozess läuft nicht!")

# --------Hauptfunktionen--------
##  @brief startet alle funktionienen nach eingabe durch eingabe im Terminal
#  @details lädt das Menü und verwaltet den Ablauf
def main():

    # nutzername abfragen
    handle = nutzernamen_abfragen()
    # Dateipfad zusammenbauen um die richtige config zu laden
    konfig_pfad = f"Konfigurationsdateien/config_{handle.lower()}.toml"
    
    config = lade_config(konfig_pfad)
    
    # erstellt ein Objekt
    manager = Manager()
    # erstellt eine nutzerliste, auf die zwei Prozesse zugreifen können
    shared_nutzerliste = manager.dict()
    # ruft funktion auf und übergibt die nutzerliste
    initialisiere_nutzerliste(shared_nutzerliste)
    # Discovery-Prozess nur einmal starten
    discovery_proc = Process(target=discovery_main, args=(konfig_pfad, shared_nutzerliste))
    discovery_proc.start()
    time.sleep(1.5)  # Kleine Pause, damit Discovery bereit ist
    port = registriere_neuen_nutzer(handle, config)

    # Startet den Netzwerkprozess als separaten Hintergrundprozess.
    # Übergeben werden: Pfad zur Benutzer-Konfigurationsdatei und der dynamisch gewählte TCP-Port.
    # Netzwerkprozess wird zuerst gestartet
    tcp_port = finde_freien_tcp_port()
    netzwerk_prozess = Process(target=starte_netzwerkprozess, args=(konfig_pfad, tcp_port, port, shared_nutzerliste))
    netzwerk_prozess.start()
    # Kurze Wartezeit, um sicherzustellen, dass der Netzwerkprozess genügend Zeit zum Hochfahren hat.
    # Verhindert Race Conditions bei späterer Kommunikation (z. B. TCP-Verbindung).
    time.sleep(1)
    # nachdem netzwerkprozess läuft:
    sende_befehl_an_netzwerkprozess(f"JOIN {handle} {port}", tcp_port)

    while True:
        auswahl = menue() # interface
        if auswahl == "1":
            # @details Sendet WHO per TCP an den Netzwerkprozess (localhost:tcp_port),
            #       empfängt die KNOWNUSERS-Antwort und gibt bekannte Nutzer aus.
            #       Erwartet Antwortformat: "KNOWNUSERS <handle1> <ip1> <port1>, ..."
            # @param tcp_port TCP-Port, auf dem der Netzwerkprozess auf WHO hört
            print("WHO wird gesendet")
            try:
                with socket.create_connection(("localhost", tcp_port)) as sock:
                    sock.sendall(b"WHO")  # Nur WHO senden
                    antwort = sock.recv(4096).decode('utf-8').strip()

                    if antwort.startswith("KNOWNUSERS"):
                        teile = antwort.split(" ", 1)
                        if len(teile) == 2:
                            eintraege = teile[1].split(", ")
                            print("KNOWNUSERS")
                            for eintrag in eintraege:
                                try:
                                    handle, ip, port = eintrag.strip().split(" ")
                                    print(f"  {handle} → {ip}:{port}")
                                except ValueError:
                                    print("  [FEHLER] Ungültiger Eintrag:", eintrag)
                        else:
                            print("[INFO] Keine bekannten Nutzer.")
                    else:
                        print("Unerwartete Antwort:", antwort)
            except ConnectionRefusedError:
                print("Netzwerkprozess läuft nicht!")

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
            print("Aktuelle Konfiguration:")
            # config hat schlüssel und wert paare
            # k=kex(schlüssel) --> autoreply
            # v=(value)Wert --> text
            # gibt die schlüssel/Wert paare aus
            for k, v in config.items():
                print(f"  {k}: {v}")
            continue    
        elif auswahl == "7":
            sende_befehl_an_netzwerkprozess(f"LEAVE {handle}", tcp_port) # main
            time.sleep(1)  # Optional, um die Nachricht sehen zu können
            netzwerk_prozess.terminate()
            discovery_proc.terminate()
            netzwerk_prozess.join()
            discovery_proc.join()
            break

# --------Programmeinstiegspunkt--------
# beginnt das Programm
# Beim starten wird name durch main ersetzt, erst wenn es stimmt, wird die Main Funktion gestartet
if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True) 
    main()