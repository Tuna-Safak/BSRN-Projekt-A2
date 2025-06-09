## @file netzwerkprozess.py
#  @brief Dieser Prozess empfängt IPC-Kommandos vom UI-Prozess über einen lokalen TCP-Socket
#         und sendet SLCP-Nachrichten (MSG, IMG) per UDP an andere Peers im Netzwerk.
#  @details Der Netzwerkprozess stellt die Verbindung zwischen der lokalen Benutzeroberfläche
#           und der Peer-to-Peer-Kommunikation im LAN her. Er verarbeitet übermittelte Befehle
#           und nutzt die Methoden aus `message_handler`, um SLCP-konforme Nachrichten zu versenden.

import socket
from message_handler import sendMSG, sendIMG, send_join
from UI_utils import lade_config
from discovery import nutzerspeichern, gebe_nutzerliste_zurück
import threading

# Neue globale Map zur Speicherung nutzerspezifischer Konfigurationen
nutzerkonfigurationen = {}

## @brief Startet den Netzwerkprozess und lauscht auf Befehle vom UI-Prozess.
#  @details Stellt einen TCP-Server auf localhost:6001 bereit, über den der UI-Prozess Kommandos
#           wie MSG und IMG senden kann. Diese werden analysiert und mit UDP an die Ziel-Peers
#           gemäß SLCP-Protokoll weitergeleitet.
#  @note Diese Funktion blockiert dauerhaft. Sie sollte in einem separaten Prozess ausgeführt werden.
def netzwerkprozess():

    # Lade Standardkonfiguration (z. B. globale Netzwerkeinstellungen)
    config = lade_config()

    # starte den Discovery-Dienst im Hintergrund
    threading.Thread(target=nutzerspeichern, daemon=True).start()

    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(("localhost", 6001))
    tcp_server.listen(1)

    print("[INFO] (Netzwerkprozess) TCP-IPC bereit auf Port 6001.")

    while True:
        conn, addr = tcp_server.accept()
        with conn:
            daten = conn.recv(1024).decode().strip()
            print(f"[Netzwerkprozess] Befehl empfangen: {daten}")

            teile = daten.split(" ", 2)

            if teile[0] == "JOIN":
                # JOIN <handle> <port>
                _, handle, port = teile
                try:
                    benutzer_config = lade_config(f"config_{handle}.toml")
                    nutzerkonfigurationen[handle] = benutzer_config
                    print(f"[INFO] Konfiguration für {handle} geladen.")
                    send_join(handle, port)
                except FileNotFoundError:
                    print(f"[WARNUNG] Konfigurationsdatei für {handle} nicht gefunden.")

            elif teile[0] == "MSG":
                # MSG <empfänger> <nachricht>
                _, empfaenger, text = teile

                # Suche den Sender-Handle anhand der Empfängeradresse (nur einer erlaubt)
                sender_handle = None
                for handle, cfg in nutzerkonfigurationen.items():
                    if "client" in cfg and "handle" in cfg["client"]:
                        sender_handle = cfg["client"]["handle"]
                        break

                if sender_handle:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sendMSG(sock, sender_handle, empfaenger, text)
                else:
                    print("[ERROR] Kein gültiger Sender-Handle gefunden für MSG.")

            elif teile[0] == "IMG":
                # IMG <empfänger> <pfad>
                _, empfaenger, pfad = teile

                sender_handle = None
                for handle, cfg in nutzerkonfigurationen.items():
                    if "client" in cfg and "handle" in cfg["client"]:
                        sender_handle = cfg["client"]["handle"]
                        break

                if sender_handle:
                    sendIMG(sender_handle, empfaenger, pfad)
                else:
                    print("[ERROR] Kein gültiger Sender-Handle gefunden für IMG.")

            elif teile[0] == "WHO":
                print("[Netzwerkprozess] → WHO wird gesendet ...")
                DISCOVERY_PORT = config["network"]["whoisdiscoveryport"]

                who_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                who_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                who_sock.settimeout(2)

                try:
                    who_sock.sendto(b"WHO\n", ("255.255.255.255", DISCOVERY_PORT))
                    print("[Netzwerkprozess] → Warte auf KNOWNUSERS-Antwort(en) ...")

                    nutzerliste = gebe_nutzerliste_zurück()
                    antwort_liste = []

                    while True:
                        daten, addr = who_sock.recvfrom(1024)
                        text = daten.decode().strip()

                        if text.startswith("KNOWNUSERS"):
                            teile = text.split(" ", 1)
                            if len(teile) == 2:
                                eintraege = teile[1].split(", ")
                                for eintrag in eintraege:
                                    try:
                                        handle, ip, port = eintrag.strip().split(" ")
                                        nutzerliste[handle] = (ip, int(port))
                                        antwort_liste.append(f"{handle} {ip} {port}")
                                        print(f"[WHO] → {handle} @ {ip}:{port} gespeichert")
                                    except ValueError:
                                        print(f"[WHO] Warnung: Eintrag konnte nicht verarbeitet werden: {eintrag}")

                except socket.timeout:
                    print("[WHO] Antwortphase beendet.")
                finally:
                    who_sock.close()

                antwort_text = "KNOWNUSERS " + ", ".join(antwort_liste)
                try:
                    conn.sendall(antwort_text.encode())
                    print("[Netzwerkprozess] → Antwort an UI gesendet.")
                except Exception as e:
                    print(f"[Netzwerkprozess] ⚠️ Antwort an UI fehlgeschlagen: {e}")

if __name__ == "__main__":
    netzwerkprozess()
