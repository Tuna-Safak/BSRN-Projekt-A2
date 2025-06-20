## @file discovery.py
## @brief Discovery-Dienst für SLCP – empfängt JOIN, WHO, LEAVE
## @details Verwaltet bekannte Nutzer und antwortet auf WHO-Anfragen

import socket
import toml
import os
from nutzerliste import gebe_nutzerliste_zurück
from interface import lade_config

def discovery_main(konfig_pfad):
    config = lade_config(konfig_pfad)
    DISCOVERY_PORT = config["network"]["whoisdiscoveryport"]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind(('', DISCOVERY_PORT))
        print(f"[INFO] Discovery-Dienst läuft auf Port {DISCOVERY_PORT}")
    except OSError:
        print(f"[WARNUNG] Discovery-Dienst läuft wohl schon auf Port {DISCOVERY_PORT}")
        return

    while True:
        daten, absender = sock.recvfrom(1024)
        text = daten.decode('utf-8').strip()

        if len(daten) > 512:
            print("[WARNUNG] Nachricht zu lang – ignoriert")
            continue

        teile = text.split()
        if not teile:
            continue

        befehl = teile[0]

        # JOIN-Verarbeitung
        if befehl == "JOIN" and len(teile) == 3:
            handle = teile[1]
            port = teile[2]
            ip = absender[0]

            if handle not in gebe_nutzerliste_zurück():
                print(f"[JOIN] {handle} ist neu beigetreten → {ip}:{port}")
            else:
                print(f"[JOIN] {handle} aktualisiert → {ip}:{port}")

            gebe_nutzerliste_zurück()[handle] = (ip, port)

        # WHO-Anfrage verarbeiten
        elif befehl == "WHO":
            antwort = "KNOWNUSERS "
            eintraege = [
                f"{handle} {ip} {port}" for handle, (ip, port) in gebe_nutzerliste_zurück().items()
            ]
            antwort += ", ".join(eintraege)
            sock.sendto(antwort.encode('utf-8'), absender)

         
#Löschen
#def zeige_bekannte_nutzer():
 #   print(" Bekannte Nutzer:")
  #  for handle, (ip, port
  #gebe_nutzerliste_zurück.items():
   #     print(f"  {handle} → {ip}:{port}")     



#if __name__ == "__main__":
 #   discovery_main()