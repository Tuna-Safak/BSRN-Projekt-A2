## @file netzwerkprozess.py
#  @brief Dieser Prozess empfängt IPC-Kommandos vom UI-Prozess über einen lokalen TCP-Socket
#         und sendet SLCP-Nachrichten (MSG, IMG) per UDP an andere Peers im Netzwerk.
#  @details Der Netzwerkprozess stellt die Verbindung zwischen der lokalen Benutzeroberfläche
#           und der Peer-to-Peer-Kommunikation im LAN her. Er verarbeitet übermittelte Befehle
#           und nutzt die Methoden aus `message_handler`, um SLCP-konforme Nachrichten zu versenden.

import socket
import sys
# ermöglicht den Zugriff aus Systemfunktionen
import threading 
# ermöglicht das gleichzeitige Ausführen von mehreren Threads
#import toml
import os
from interface import lade_config
from discovery import discovery_main
from nutzerliste import gebe_nutzerliste_zurück
# damit TCP und UDP seperat laufen können 
import sys

#if __name__ == "__main__":
 #   konfig_pfad = sys.argv[1] if len(sys.argv) > 1 else None
#else:
 #   konfig_pfad = None

# Discovery DISCOVERY_PORT aus Konfig

def finde_lokale_ip():
    #Ermittelt die echte lokale IP-Adresse (z. B. WLAN) durch Verbindung zu 8.8.8.8.
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"[WARNUNG] Lokale IP konnte nicht ermittelt werden: {e}")
        return "127.0.0.1"



# Gib den Socket an andere Module zurück, falls gewünscht
#def get_socket():
 #   return sock

# -----------JOIN-Nachricht versenden------------------
def send_join(sock, handle, port, DISCOVERY_PORT):
    # allen im Chat wird mitgeteilt, dass ich mich im Chat befinde
    #ip = finde_lokale_ip()
    nachricht = f"JOIN {handle} {port}\n"
    sock.sendto(nachricht.encode('utf-8'), ("255.255.255.255", DISCOVERY_PORT))

# -------------JOIN verarbeiten-----------------
def handle_join(name, DISCOVERY_PORT, addr, ip=None):
    if ip is None:
        ip = addr[0]
        
#def handle_join(name, DISCOVERY_PORT, addr):
    # Verarbeitung einer JOIN-Nachricht, um neuen Nutzer zu speichern
   # ip = addr[0]
    DISCOVERY_PORT = int(DISCOVERY_PORT)

    if name not in gebe_nutzerliste_zurück(): 
        gebe_nutzerliste_zurück()[name] = (ip, DISCOVERY_PORT)
        
    #else:
        #gebe_nutzerliste_zurück()[name] = (ip, DISCOVERY_PORT)
        #print(f"{name} erneut beigetreten – Daten aktualisiert: {ip}:{DISCOVERY_PORT}")
        #print(f"[DEBUG] Nachher bekannte Nutzer: {gebe_nutzerliste_zurück()}")


# -------------Leave-Nachricht versenden-----------------
def send_leave(sock, handle_nutzername, DISCOVERY_PORT):
    nachricht = f"LEAVE {handle_nutzername}\n"
    sock.sendto(nachricht.encode('utf-8'), ("255.255.255.255", DISCOVERY_PORT))

    eigene_ip = finde_lokale_ip()

    bekannte_nutzer = gebe_nutzerliste_zurück()
    for anderer_handle, (ip, port) in bekannte_nutzer.items():
        if ip == eigene_ip:
            continue  # Nicht an sich selbst senden
        sock.sendto(nachricht.encode('utf-8'), (ip, int(port)))
        print(f"[LEAVE] Gesendet (Unicast) an {anderer_handle} @ {ip}:{port}")


# -------------LEAVE verarbeiten-----------------
def handle_leave(name):
    # Verarbeitung einer LEAVE-Nachricht, um Nutzer aus der Liste zu entfernen
    if name in gebe_nutzerliste_zurück():
        del gebe_nutzerliste_zurück()[name]
        print(f"LEAVE {name}")
    else:
        print(f"LEAVE von unbekanntem Nutzer erhalten: {name}")


# -------------Nachricht senden-----------------
def sendMSG(sock, handle, empfaenger_handle, text):
    nutzerliste = gebe_nutzerliste_zurück()

    if empfaenger_handle not in nutzerliste:
        print("Empfänger nicht bekannt.")
        # print(f"Bekannte Nutzer: {nutzerliste}")
        return

    eintrag = nutzerliste[empfaenger_handle]

    if len(eintrag) != 2:
        print(f"[FEHLER] Eintrag für {empfaenger_handle} hat kein (ip, port)-Format: {eintrag}")
        return

    ip, port = eintrag
    try:
        port = int(port)
    except ValueError:
        print(f"[FEHLER] Port ist keine Zahl: {port}")
        return

    nachricht = f'MSG {handle} "{text}"\n'
    print(f'MSG {empfaenger_handle} "{text}"')
    sock.sendto(nachricht.encode('utf-8'), (ip, port))


# -------------Nachricht empfangen-----------------
def receive_MSG(sock, config):
   # Empfängt Nachrichten vom UDP-Socket und verarbeitet sie.
     
    while True:
        try:
            # Empfängt Daten vom Socket
            daten, addr = sock.recvfrom(1024)  # Daten und Adresse des Absenders
            text = daten.decode('utf-8').strip()
            # Teile der Nachricht aufspalten
            teile = text.strip().split(" ", 1)
            befehl = teile[0]
            rest = teile[1] if len(teile) > 1 else ""

            teile = [befehl] + rest.strip().split(" ")
            if len(teile) == 0:
                print("Leere Nachricht")
                continue

            befehl = teile[0]
            eigene_ip = finde_lokale_ip()
            eigener_handle = config["client"]["handle"]

            # Verarbeitung von JOIN-Nachrichten
            if befehl == "JOIN" and len(teile) >= 3:
                name = teile[1]
                port = teile[2]
                ip = teile[3] if len(teile) >= 4 else addr[0]
                if name == eigener_handle and ip == eigene_ip:
                    continue

                handle_join(name, port, addr, ip) 
                #print(f"\n[JOIN] {name} ist dem Chat beigetreten.") #maybe löschen

            # Verarbeitung von LEAVE-Nachrichten
            elif befehl == "LEAVE" and len(teile) == 2:
                absender_ip = addr[0]
                absender_name = None
                for name, (ip, _) in gebe_nutzerliste_zurück().items():
                    if ip == absender_ip:
                     absender_name = name
                     break

                if not absender_name:
                    absender_name = teile[1]  # Fallback, falls IP nicht gefunden

                handle_leave(absender_name)
                # print(f"\n[LEAVE] {absender_name} hat den Chat verlassen.")

            # Verarbeitung von MSG-Nachrichten
            elif befehl == "MSG" and len(teile) >= 3:
                absender_handle = teile[1]
                nachricht = " ".join(teile[2:])  # Alles ab dem dritten Wort
                print(f"\nNachricht von {absender_handle}: {nachricht}\n> ", end="")

                if config.get("autoreply_aktiv", False):
                    autoreply_text = config.get("autoreply", "Ich bin gerade nicht da.")
                    handle = config["client"]["handle"]
                    sendMSG(sock, handle, absender_handle, autoreply_text)

            # Verarbeitung von IMG-Nachrichten
            elif befehl == "IMG" and len(teile) == 3:
                print(f"[DEBUG] IMG-Befehl empfangen: {teile} von {addr}")
                try:
                    handle_IMG(sock, teile, addr, config)
                except Exception as e:
                    print(f"Fehler beim Bildempfang: {e}")

            # Verarbeitung von KNOWNUSERS-Nachrichten
            elif befehl == "KNOWNUSERS":
            
                if rest:
                    eintraege = rest.split(", ")
                    nutzerlist = gebe_nutzerliste_zurück()
                   # eigener_handle = config["client"]["handle"]
                   
                    for eintrag in eintraege:
                        try:
                            handle, ip, port = eintrag.strip().split(" ")
                            nutzerlist[handle] = (ip, int(port)) 

        
                            #if handle == eigener_handle:
                               # continue
                        except ValueError:
                            print(f"[WARNUNG] Konnte Nutzer nicht verarbeiten: {eintrag}")
                else:
                     print("[INFO] Keine Nutzer in KNOWNUSERS-Antwort.")

        except Exception as e:
            print(f"Fehler: {e}")


# -------------Bild senden-----------------
# @brief Sendet ein Bild an einen anderen Nutzer über UDP
# @param sock Der UDP-Socket zum Senden der Nachricht
# @param handle_sender Benutzername des Absenders 
# @param handle_empfaenger Benutzername des Empfängers
# @param bildpfad Pfad zur Bilddatei, die gesendet werden soll
def sendIMG(sock, handle_sender, handle_empfaenger, bildpfad):
    nutzer = gebe_nutzerliste_zurück()

    # 1) Empfänger bekannt?
    if handle_empfaenger not in nutzer:
        print("[ERROR] Empfänger nicht bekannt:", handle_empfaenger)
        return

    # 2) Bild einlesen
    try:
        with open(bildpfad, "rb") as b:
            bilddaten = b.read()
    except FileNotFoundError:
        print("[ERROR] Bild nicht gefunden:", bildpfad)
        return

    groesse = len(bilddaten)
    if groesse == 0:
        print("[ERROR] Leere Bilddatei:", bildpfad)
        return

    # 3) Header senden
    ip, port = nutzer[handle_empfaenger]
    img_header = f"IMG {handle_empfaenger} {groesse}\n".encode()
    sock.sendto(img_header, (ip, int(port)))
    print("[INFO] Header gesendet:", img_header.decode().strip())

    # 4) Bild senden – EIN Datagramm
    sent = sock.sendto(bilddaten, (ip, int(port)))
    if sent != groesse:
        # (kommt bei UDP normalerweise nicht vor)
        print("[ERROR] sendto() hat weniger Bytes gesendet als erwartet.")
    else:
        print(f"[INFO] Bild an {handle_empfaenger} gesendet ({groesse} B).")

###############################################################################
# Bild empfangen
###############################################################################
def handle_IMG(sock, teile, addr, config):
    # Header-Format prüfen
    if len(teile) != 3:
        print("[WARN] IMG-Header unvollständig:", " ".join(teile))
        return

    empfaenger = teile[1].strip().lower()
    eigener_handle = config["client"]["handle"].lower()
    if empfaenger != eigener_handle:
        return  # Nicht für mich

    # Bildgröße lesen
    try:
        groesse = int(teile[2])
    except ValueError:
        print("[WARN] Ungültige Size:", teile[2])
        return

    if groesse <= 0:
        print("[WARN] Size muss > 0 sein")
        return

    # EIN Datagramm mit Bilddaten empfangen
    sock.settimeout(3.0)        # Timeout gegen Hänger
    try:
        print(f"[DEBUG] Warte auf Bilddaten: {groesse} Bytes …")
        bilddaten, _ = sock.recvfrom(groesse)
        print(f"[DEBUG] Empfangen: {len(bilddaten)} Bytes")
    except socket.timeout:
        print("[ERROR] Timeout – Bilddatagramm nicht angekommen.")
        return
    finally:
        sock.settimeout(None)

    if len(bilddaten) != groesse:
        print(f"[ERROR] Bytezahl stimmt nicht ({len(bilddaten)} ≠ {groesse}) – Bild verworfen.")
        return

    # Absendername aus IP ermitteln
    sender_name = next(
        (name for name, (ip, _) in gebe_nutzerliste_zurück().items() if ip == addr[0]),
        "Unbekannt"
    )

    # Bild speichern
    zielverzeichnis = config["client"].get("imagepath", "empfangene_bilder")
    os.makedirs(zielverzeichnis, exist_ok=True)
    dateiname = f"{sender_name}_bild.jpg"
    pfad = os.path.join(zielverzeichnis, dateiname)

    with open(pfad, "wb") as f:
        f.write(bilddaten)

    print(f"[INFO] Bild ({groesse} B) von {sender_name} gespeichert unter: {pfad}")

## @brief Startet den Netzwerkprozess und lauscht auf Befehle vom UI-Prozess.
#  @details Stellt einen TCP-Server auf localhost:tcpPort bereit, über den der UI-Prozess Kommandos
#           wie MSG und IMG senden kann. Diese werden analysiert und mit UDP an die Ziel-Peers
#           gemäß SLCP-Protokoll weitergeleitet.
#  @note Diese Funktion blockiert dauerhaft. Sie sollte in einem separaten Prozess ausgeführt werden.
def netzwerkprozess(sock, konfig_pfad, tcp_port):
 
    print("[DEBUG] netzwerkprozess(konfig_pfad) wurde aufgerufen")


    ## @var config
    #  @brief Lädt Konfigurationsparameter wie Handle und Netzwerkports aus config.toml.
    config = lade_config(konfig_pfad)
    print("[DEBUG] Netzwerkprozess gestartet")


    ## @var tcp_server
    #  @brief Lokaler TCP-Server-Socket für IPC zwischen UI und Netzwerkprozess.
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(("localhost", tcp_port))
    tcp_server.listen(1)


    print("f[INFO] (Netzwerkprozess) TCP-IPC bereit auf Port {tcp_port}" )

    while True:
        ## @var conn
        #  @brief Socket-Objekt für eine eingehende UI-Verbindung.
        ## @var addr
        #  @brief Adresse des UI-Clients (normalerweise localhost).
        conn, addr = tcp_server.accept()
        with conn:
            ## @var daten
            #  @brief Empfangener Befehl als Zeichenkette.
            daten = conn.recv(1024).decode('utf-8').strip()
        
            ## @var teile
            #  @brief Aufgesplitteter Befehl (z. B. ["MSG", "Bob", "Hallo"])
            teile = daten.strip().split(" ", 2)  # WICHTIG!

            # Behandelt den MSG-Befehl und leitet ihn per UDP an den Ziel-Client weiter
            if teile[0] == "MSG":
                _, empfaenger, text = teile
                handle = config["client"]["handle"]
                sendMSG(sock, handle, empfaenger, text)


            # Behandelt den IMG-Befehl und leitet das Bild weiter
            elif teile[0] == "IMG":
                _, empfaenger, pfad = teile
                sendIMG(sock, config["client"]["handle"], empfaenger, pfad)
                

            # behandelt den JOIN-Befehl und leitet es Broadcast per UDP weiter 
            # wird von Discovery-Dienst empfangen
            elif teile[0] == "JOIN":
                _, handle, port = teile
                send_join(sock, handle, port, config["network"]["whoisdiscoveryport"])
                 # Lokalen Nutzer selbst eintragen
                eigene_ip = finde_lokale_ip()
                gebe_nutzerliste_zurück()[handle] = (eigene_ip, int(port))
          

            elif teile[0] == "LEAVE": 
                send_leave(sock, config["client"]["handle"],config["network"]["whoisdiscoveryport"] )

            ## @brief Behandelt den WHO-Befehl vom UI-Prozess über TCP.
            #  @details Führt einen UDP-Broadcast mit "WHO" an alle Peers im LAN durch. 
            #           Sammelt die eingehenden KNOWNUSERS-Antworten, nimmt alle Nutzereinträge,
            #           aktualisiert die interne Nutzerliste und sendet sie formatiert per TCP 
            #           zurück an den aufrufenden UI-Prozess.
            #  @note Verwendet dieselbe TCP-Verbindung (`conn.sendall`), über die auch der WHO-Befehl empfangen wurde.
            elif teile[0] == "WHO":
                DISCOVERY_PORT = config["network"]["whoisdiscoveryport"]

                who_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                who_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                who_sock.settimeout(2) 

                antwort_liste = []  # lokale Liste zum Rücksenden

                try:
        # WHO-Nachricht senden
                    who_sock.sendto(b"WHO", ("255.255.255.255", DISCOVERY_PORT))

                    while True:
                        daten, addr = who_sock.recvfrom(1024)
                        text = daten.decode('utf-8').strip()

                        if text.startswith("KNOWNUSERS"):
                            teile = text.split(" ", 1)
                            if len(teile) == 2:
                                eintraege = teile[1].split(", ")
                                for eintrag in eintraege:
                                    try:
                                        handle, ip, port = eintrag.strip().split(" ")
                                        port = int(port)

                            # ✅ Zugriff direkt auf das zentrale Dictionary!
                                        nutzerdict = gebe_nutzerliste_zurück()
                                        if handle in nutzerdict and nutzerdict[handle] == (ip, port):
                                            continue  # schon drin
                                        nutzerdict[handle] = (ip, port)
                                        antwort_liste.append(f"{handle} {ip} {port}")
                                        print(f"[WHO] Bekannt: {handle} @ {ip}:{port}")

                                    except ValueError:
                                        print(f"[WHO] Fehler beim Verarbeiten: {eintrag}")
                except socket.timeout:
                    print("[WHO] Antwortphase beendet.")
                finally:
                    who_sock.close()

    # TCP-Antwort zurück an das UI
                antwort_text = "KNOWNUSERS " + ", ".join(antwort_liste)
                try:
                    conn.sendall(antwort_text.encode('utf-8'))
                except Exception as e:              
                    print(f"[Netzwerkprozess] Antwort an UI fehlgeschlagen")


def starte_netzwerkprozess(konfig_pfad, tcp_port, port):
    config = lade_config(konfig_pfad)
    DISCOVERY_PORT = config["network"]["whoisdiscoveryport"]
    
# Erstelle den UDP-Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(('', port))  # <--- Wichtig: mit dem übergebenen Port binden
# Binde an den freien DISCOVERY_PORT
    
    
    threading.Thread(target=receive_MSG, args=(sock, config), daemon=True).start()
    netzwerkprozess(sock, konfig_pfad, tcp_port)
