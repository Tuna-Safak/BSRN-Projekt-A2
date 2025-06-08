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
# damit TCP und UDP seperat laufen können 
import threading

## @brief Startet den Netzwerkprozess und lauscht auf Befehle vom UI-Prozess.
#  @details Stellt einen TCP-Server auf localhost:6001 bereit, über den der UI-Prozess Kommandos
#           wie MSG und IMG senden kann. Diese werden analysiert und mit UDP an die Ziel-Peers
#           gemäß SLCP-Protokoll weitergeleitet.
#  @note Diese Funktion blockiert dauerhaft. Sie sollte in einem separaten Prozess ausgeführt werden.
def netzwerkprozess():
 
    ## @var config
    #  @brief Lädt Konfigurationsparameter wie Handle und Netzwerkports aus config.toml.
    config = lade_config()
    # startet den Discovery-Dienst im Hintergrund
    threading.Thread(target=nutzerspeichern, daemon=True).start()

    ## @var tcp_server
    #  @brief Lokaler TCP-Server-Socket für IPC zwischen UI und Netzwerkprozess.
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(("localhost", 6001))
    tcp_server.listen(1)

    print("[INFO] (Netzwerkprozess) TCP-IPC bereit auf Port 6001.")

    while True:
        ## @var conn
        #  @brief Socket-Objekt für eine eingehende UI-Verbindung.
        ## @var addr
        #  @brief Adresse des UI-Clients (normalerweise localhost).
        conn, addr = tcp_server.accept()
        with conn:
            ## @var daten
            #  @brief Empfangener Befehl als Zeichenkette.
            daten = conn.recv(1024).decode().strip()
            print(f"[Netzwerkprozess] Befehl empfangen: {daten}")

            ## @var teile
            #  @brief Aufgesplitteter Befehl (z. B. ["MSG", "Bob", "Hallo"])
            teile = daten.split(" ", 2)

            # Behandelt den MSG-Befehl und leitet ihn per UDP an den Ziel-Client weiter
            if teile[0] == "MSG":
                _, empfaenger, text = teile
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sendMSG(sock, config["handle"], empfaenger, text)

            # Behandelt den IMG-Befehl und leitet das Bild weiter
            elif teile[0] == "IMG":
                _, empfaenger, pfad = teile
                sendIMG(config["handle"], empfaenger, pfad)

            # behandelt den JOIN-Befehl und leitet es Broadcast per UDP weiter 
            # wird von Discovery-Dienst empfangen
            elif teile[0] == "JOIN":
                _, handle, port = teile
                send_join(handle, port)

            ## @brief Behandelt den WHO-Befehl vom UI-Prozess über TCP.
            #  @details Führt einen UDP-Broadcast mit "WHO" an alle Peers im LAN durch. 
            #           Sammelt die eingehenden KNOWNUSERS-Antworten, nimmt alle Nutzereinträge,
            #           aktualisiert die interne Nutzerliste und sendet sie formatiert per TCP 
            #           zurück an den aufrufenden UI-Prozess.
            #  @note Verwendet dieselbe TCP-Verbindung (`conn.sendall`), über die auch der WHO-Befehl empfangen wurde.
            elif teile[0] == "WHO":
                print("[Netzwerkprozess] → WHO wird gesendet ...")
                DISCOVERY_PORT = config["network"]["whoisdiscoveryport"]

                who_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                who_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                who_sock.settimeout(2)

                try:
                    # Broadcast-Nachricht an alle Peers senden
                    who_sock.sendto(b"WHO\n", ("255.255.255.255", DISCOVERY_PORT))
                    print("[Netzwerkprozess] → Warte auf KNOWNUSERS-Antwort(en) ...")

                    nutzerliste = gebe_nutzerliste_zurück()
                    antwort_liste = []  # lokale Liste zum Rücksenden

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

                # KNOWNUSERS-Antwort zusammensetzen und per TCP an UI zurücksenden
                antwort_text = "KNOWNUSERS " + ", ".join(antwort_liste)
                try:
                    conn.sendall(antwort_text.encode())
                    print("[Netzwerkprozess] → Antwort an UI gesendet.")
                except Exception as e:
                    print(f"[Netzwerkprozess] ⚠️ Antwort an UI fehlgeschlagen: {e}")


if __name__ == "__main__":
    netzwerkprozess()