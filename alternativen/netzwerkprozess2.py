## @file netzwerkprozess.py
#  @brief Dieser Prozess empfängt IPC-Kommandos vom UI-Prozess über einen lokalen TCP-Socket
#         und sendet SLCP-Nachrichten (MSG, IMG) per UDP an andere Peers im Netzwerk.
#  @details Der Netzwerkprozess stellt die Verbindung zwischen der lokalen Benutzeroberfläche
#           und der Peer-to-Peer-Kommunikation im LAN her. Er verarbeitet übermittelte Befehle
#           und nutzt die Methoden aus `message_handler`, um SLCP-konforme Nachrichten zu versenden.

import socket
import sys
import threading 
import toml
import os
from UI_utils import lade_config, finde_freien_port
from discovery import nutzerspeichern, gebe_nutzerliste_zurück

# Lade die Konfiguration aus config.toml
config = lade_config()

# Discovery DISCOVERY_PORT aus Konfig
DISCOVERY_PORT = config["network"]["whoisdiscoveryport"]

# Erstelle den UDP-Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(('', DISCOVERY_PORT))
print(f"[INFO] (Discovery-) Socket gebunden an DISCOVERY_PORT {DISCOVERY_PORT}")

def finde_lokale_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"[WARNUNG] Lokale IP konnte nicht ermittelt werden: {e}")
        return "127.0.0.1"

def get_socket():
    return sock

# -----------JOIN-Nachricht versenden------------------
def send_join(handle, port):
    ip = finde_lokale_ip()
    nachricht = f"JOIN {handle} {port} {ip}\n"
    sock.sendto(nachricht.encode(), ("255.255.255.255", DISCOVERY_PORT))
    print(f"[JOIN] Gesendet: {nachricht.strip()}")

# -------------JOIN verarbeiten-----------------
def handle_join(name, DISCOVERY_PORT, addr, ip=None):
    if ip is None:
        ip = addr[0]
    DISCOVERY_PORT = int(DISCOVERY_PORT)
    if name not in gebe_nutzerliste_zurück():
        gebe_nutzerliste_zurück()[name] = (ip, DISCOVERY_PORT)
        print(f"{name} ist dem Chat beigetreten – {ip}:{DISCOVERY_PORT}")
    else:
        gebe_nutzerliste_zurück()[name] = (ip, DISCOVERY_PORT)
        print(f"{name} erneut beigetreten – Daten aktualisiert: {ip}:{DISCOVERY_PORT}")

# -------------Leave-Nachricht versenden-----------------
def send_leave(handle_nutzername):
    nachricht = f"LEAVE {handle_nutzername}\n"
    sock.sendto(nachricht.encode(), ("255.255.255.255", DISCOVERY_PORT))
    print(f"[LEAVE] Gesendet: {nachricht.strip()}")

# -------------LEAVE verarbeiten-----------------
def handle_leave(name):
    if name in gebe_nutzerliste_zurück():
        del gebe_nutzerliste_zurück()[name]
        print(f"{name} hat den Chat verlassen")
    else:
        print(f"LEAVE von unbekanntem Nutzer erhalten: {name}")

# -------------Nachricht senden-----------------
def sendMSG(sock, config, handle, empfaenger_handle, text):
    if empfaenger_handle not in gebe_nutzerliste_zurück():
        print("Empfänger nicht bekannt.")
        print(f"Bekannte Nutzer: {gebe_nutzerliste_zurück()}")
        return
    nachricht = f'MSG {handle} "{text}"\n'
    if len(nachricht.encode()) > 512:
        print("Nachricht ist zu lang (max. 512 Zeichen erlaubt).")
        return
    ip, DISCOVERY_PORT = gebe_nutzerliste_zurück()[empfaenger_handle]
    print(f"[SEND] → an {empfaenger_handle} @ {ip}:{DISCOVERY_PORT} → {text}")
    sock.sendto(nachricht.encode(), (ip, DISCOVERY_PORT))

# -------------Nachricht verarbeiten und formatieren-----------------
def handle_MSG(sender, text):
    clean_text = text.strip('"')
    print(f" Nachricht von {sender}: {clean_text}")

# -------------Nachricht empfangen-----------------
def receive_MSG(sock, config):
    while True:
        daten, addr = sock.recvfrom(1024)
        text = daten.decode().strip()
        teile = nachricht.strip().split(" ")
        if len(teile) == 0:
            continue
        befehl = teile[0]
        if befehl == "JOIN" and len(teile) >= 3:
            name = teile[1]
            port = teile[2]
            ip = teile[3] if len(teile) == 4 else None
            handle_join(name, port, addr, ip)
        elif befehl == "LEAVE" and len(teile) == 2:
            handle_leave(teile[1])
        elif befehl == "MSG" and len(teile) == 3:
            absender_handle = teile[1]
            nachricht = teile[2]
            print(f"Nachricht von {absender_handle}: {nachricht}\n> ", end="")
            if config.get("client", {}).get("autoreply_aktiv", False):
                autoreply_text = config["client"].get("autoreply", "Ich bin gerade nicht da.")
                sendMSG(sock, config, config["client"]["handle"], absender_handle, autoreply_text)
        elif befehl == "IMG" and len(teile) == 3:
            try:
                handle_IMG(sock, teile, addr)
            except Exception as e:
                print(f"Fehler beim Bildempfang: {e}")
        elif befehl == "KNOWNUSERS" and len(teile) == 2:
            eintraege = teile[1].split(", ")
            nutzerliste = gebe_nutzerliste_zurück()
            for eintrag in eintraege:
                try:
                    handle, ip, port = eintrag.strip().split(" ")
                    nutzerliste[handle] = (ip, int(port))
                    print(f"[INFO] → {handle} @ {ip}:{port} gespeichert")
                except ValueError:
                    print(f"[WARNUNG] Konnte Nutzer nicht verarbeiten: {eintrag}")
        else:
            print(f" Unbekannte Nachricht: {text}")

# Starte den Nachricht-Empfangs-Thread nach der Definition
def start_receiver_thread():
    threading.Thread(target=lambda: receive_MSG(sock, config), daemon=True).start()

# Dummy-Definition der Funktion netzwerkprozess() zum Beheben des Fehlers
def netzwerkprozess():
    print("[INFO] Dummy netzwerkprozess gestartet. Bitte mit echter Logik ersetzen.")

# Hauptprogramm
if __name__ == "__main__":
    start_receiver_thread()
    netzwerkprozess()