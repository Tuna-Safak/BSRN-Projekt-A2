## @file discovery.py
# @brief Discovery-Dienst für SLCP – empfängt JOIN, WHO, LEAVE
# @details Verwaltet bekannte Nutzer und antwortet auf WHO-Anfragen

import socket
import toml
import os
from nutzerliste import(
 gebe_nutzerliste_zurück 
) 

from interface import (
    lade_config
)

from nutzerliste import (
    initialisiere_nutzerliste
)
# --------Funktion von Discovery--------
def discovery_main(konfig_pfad, shared_dict):
    initialisiere_nutzerliste(shared_dict)
    config = lade_config(konfig_pfad)
    DISCOVERY_PORT = config["network"]["whoisdiscoveryport"]

    # socket erstellen
    # variable namens 'sock', datentyp socket
    # socket.socket() = socket = modul/package, socket() = funktion/klasse
    # socket.AF_INET, socket.SOCK_DGRAM = argumente/parameter
    # socket.AF_INET = Netzwerk-Typ: IPv4
    # socket.SOCK_DGRAM	= UDP-Socket statt TCP

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # sock.setsockopt = option/einstellung setzen fuer socket
    # SOL_SOCKET = option gilt nur auf Socket-Ebene (nicht zB für TCP selbst) -> (SOL = Socket Option Level)
    # socket.SO_BROADCAST = erlaube Senden/Empfangen von Broadcasts
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # socket.SO_REUSEADDR = erlaube Wiederverwendung einer Port-Adresse
    # 1 = aktivieren (True / Ja)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bindet den Socket an eine IP-Adresse und einen Port
    # sock	= Variable, die den UDP-Socket enthält
    # bind()	= Methode, um dem Socket eine Adresse (IP + Port) zu geben
    # ('', DISCOVERY_PORT) = '' bedeutet: alle lokalen IP-Adressen, Port kommt aus der Konfigurationsdatei
    try:
        sock.bind(('', DISCOVERY_PORT))
        print(f"[INFO] Discovery-Dienst läuft auf Port {DISCOVERY_PORT}")
    except OSError:
        print(f"[WARNUNG] Discovery-Dienst läuft wohl schon auf Port {DISCOVERY_PORT}")
        return

    while True:
      # recvfrom() = Methode für UDP-Sockets, liefert zwei Werte zurueck, 
      # daten = in bytes (inhalt der nachricht), absender = IP-Adresse und Port des Absenders
      # empfängt bis zu 1024 Bytes, Max. Nachrichtenlänge: 512 Zeichen, 1024 = doppelte Menge (Sicherheitsreserve)

        daten, absender = sock.recvfrom(1024)
        text = daten.decode('utf-8').strip()

        # Überpruefung
        if len(daten) > 512:
            print("[WARNUNG] Nachricht zu lang – ignoriert")
            continue
        # teile = datentyp: list 
        # split() = teilt text in Teilstrings 
        teile = text.strip().split()
        # SLCP-Regel: Nachricht muss mindestens 1 Teil enthalten
        # wenn Liste leer ist, dann überspringe den Rest der Schleife
        # und mache mit nächster empfangenen Nachricht weiter
        if not teile:
            continue

        # erstes Wort aus der Nachricht holen, also den Befehl, den der Absender geschickt hat
        befehl = teile[0]

        # JOIN-Verarbeitung
        if befehl == "JOIN" and len(teile) == 3:
            handle = teile[1].strip().lower()
            port = teile[2]

            # IP-Adresse aus dem Datenpaket "absender" holen
            ip = absender[0]

            if handle not in gebe_nutzerliste_zurück():
                print(f"JOIN {handle} {port}")
            else:
                print(f"JOIN {handle} aktualisiert → {port}")

            gebe_nutzerliste_zurück()[handle] = (ip, port)

        # WHO-Anfrage verarbeiten
        elif befehl == "WHO":
            antwort = "KNOWNUSERS "
            eintraege = [
                f"{handle} {ip} {port}" for handle, (ip, port) in gebe_nutzerliste_zurück().items()
            ]
            antwort += ", ".join(eintraege)
            
            # sendto() = methode zum versenden von UDP-Nachrichten
            # encode() = wandelt string in bytes um
            # absender = IP-Adresse und Port an dem die Nachricht gehen soll
            sock.sendto(antwort.encode('utf-8'), absender)
        # LEAVE-Verarbeitung
        elif befehl == "LEAVE" and len(teile) == 2:
            handle = teile[1].strip().lower()
            nutzerliste = gebe_nutzerliste_zurück()

            if handle in nutzerliste:
                del nutzerliste[handle]
                print(f"[LEAVE] {handle} hat den Chat verlassen (aus Discovery gelöscht).")
            else:
                print(f"[LEAVE] Unbekannter Nutzer '{handle}' wollte LEAVE senden.")