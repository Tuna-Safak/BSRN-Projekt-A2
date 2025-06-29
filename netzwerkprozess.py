## @file netzwerkprozess.py
# @brief empfängt und verarbeitet IPC-Kommandos vom UI-Prozess
# @details sendet SLCP-Nachrichten (MSG, IMG) per UDP an andere Peers im Netzwerk.

import socket

# ermöglicht das gleichzeitige Ausführen von mehreren Threads
# damit TCP und UDP seperat laufen können 
import threading 
import os

from nutzerliste import (
    initialisiere_nutzerliste, 
    gebe_nutzerliste_zurück
)

from interface import (
    lade_config
)

## @brief lokale IP-Adresse wird gesucht
# @details Ermittelt die echte lokale IP-Adresse (z. B. WLAN) durch Verbindung zu 8.8.8.8.
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

# --------JOIN-Nachricht versenden--------
## @breif versendet eine Join-Nachricht
# @param sock UDP-Socket
# @param handel Benutzername
# @param port eigener Port
# @param Discovery_port Broadcast-Port
def send_join(sock, handle, port, DISCOVERY_PORT):
    # allen im Chat wird mitgeteilt, dass ich mich im Chat befinde
    nachricht = f"JOIN {handle} {port}\n"
    sock.sendto(nachricht.encode('utf-8'), ("255.255.255.255", DISCOVERY_PORT))

# --------JOIN verarbeiten--------
## @brief Verarbeitet eine empfangene Join nachricht
# @param name des beitretenden Nutzers (handle)
# @param Discovery_port port von Discovery dienst
# @param addr die absender adresse
# @param ip=None falls eine Ip adresse bekannt ist, sonst None
def handle_join(name, DISCOVERY_PORT, addr, ip=None):
    if ip is None:
        ip = addr[0]
        
    DISCOVERY_PORT = int(DISCOVERY_PORT)

    if name not in gebe_nutzerliste_zurück(): 
        gebe_nutzerliste_zurück()[name] = (ip, DISCOVERY_PORT)
        
    

# --------Leave-Nachricht versenden--------
## @brief sendet eine leave nachricht an alle Nutzer
# @param sock UDP socket
# @param handle_nutzername name des lokalen Nutzers
# @param Discovery_Port Broadcast-Port
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
    
    eigener_handle = handle_nutzername
    if eigener_handle in gebe_nutzerliste_zurück():
        del gebe_nutzerliste_zurück()[eigener_handle]
    


# --------LEAVE verarbeiten--------
## @brief entfernt einen nutzer aus der Nutzerliste
# @param name nutzername
def handle_leave(name):
    # Verarbeitung einer LEAVE-Nachricht, um Nutzer aus der Liste zu entfernen
    if name in gebe_nutzerliste_zurück():
        del gebe_nutzerliste_zurück()[name]
        print(f"LEAVE {name}")
    else:
        print(f"LEAVE von unbekanntem Nutzer erhalten: {name}")


# --------Nachricht senden--------
## @brief sendet eine nachricht an einen nutzer
# @param sock UDP-Soket
# @param handle absender handle
# @param empfaenger_handle empfänger handle
# @param text Nachricht
def sendMSG(sock, handle, empfaenger_handle, text):
    nutzerliste = gebe_nutzerliste_zurück()

    if empfaenger_handle not in nutzerliste:
        print("Empfänger nicht bekannt.")
        print(f"Bekannte Nutzer: {nutzerliste}")
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


# --------Nachricht empfangen--------
## @brief Empfängt Nachrichten vom UDP-Socket und verarbeitet sie.
# @param sock UDP-Socket
# @param config individuelle Konfiguartions Datei
def receive_MSG(sock, config):
  
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

            # Verarbeitung von LEAVE-Nachrichten
            elif befehl == "LEAVE" and len(teile) == 2:
                absender_name = teile[1].strip().lower()
                nutzerliste = gebe_nutzerliste_zurück()

                if absender_name in nutzerliste:
                    handle_leave(absender_name)
                    print(f"[LEAVE] {absender_name}")
                else:
                    print(f"[LEAVE] Unbekannter Nutzer '{absender_name}' wollte LEAVE senden.")

            # Verarbeitung von MSG-Nachrichten
            elif befehl == "MSG" and len(teile) >= 3:
                absender_handle = teile[1]
                nachricht = " ".join(teile[2:])  # Alles ab dem dritten Wort
                print(f"\n MSG {absender_handle}: {nachricht}\n> ", end="")

                if config.get("autoreply_aktiv", False):
                    autoreply_text = config.get("autoreply", "Ich bin gerade nicht da.")
                    handle = config["client"]["handle"]
                    sendMSG(sock, handle, absender_handle, autoreply_text)

            # Verarbeitung von IMG-Nachrichten
            elif befehl == "IMG" and len(teile) == 3:
                # print(f"[DEBUG] IMG-Befehl empfangen: {teile} von {addr}")
                try:
                    handle_IMG(sock, teile, addr, config)
                except Exception as e:
                    print(f"Fehler beim Bildempfang: {e}")
            
        except Exception as e:
            print(f"Fehler: {e}")


# --------Bild senden--------
## @brief Sendet ein Bild an einen anderen Nutzer über UDP
# @param sock Der UDP-Socket zum Senden der Nachricht
# @param handle_empfaenger Benutzername des Empfängers
# @param bildpfad Pfad zur Bilddatei, die gesendet werden soll
def send_IMG(sock, handle_empfaenger, bildpfad):
    nutzer = gebe_nutzerliste_zurück()

    # Prüfen, ob der Empfänger überhaupt im Nutzerverzeichnis bekannt ist
    if handle_empfaenger not in nutzer:
        print("[ERROR] Empfänger nicht bekannt:", handle_empfaenger)
        return

    # 2) Bild einlesen
    try:
        # Bilddatei öffnen – "rb" bedeutet:
        # r = read, b = binary (binär lesen, nicht als Text)
        # wir brauchen das für Bilder, weil sie keine Textdateien sind
        with open(bildpfad, "rb") as b:
        # Liest alle Bilddaten in binärer Form
            bilddaten = b.read()

    except FileNotFoundError:
         # Wenn der Pfad falsch ist oder das Bild nicht existiert
        print("[ERROR] Bild nicht gefunden:", bildpfad)
        return
    
    # Bildgröße berechnen (Anzahl der Bytes)
    # wichtig für den Empfänger damit er weiß wie viele Daten kommen
    groesse = len(bilddaten)
    if groesse == 0:
        print("[ERROR] Leere Bilddatei:", bildpfad)
        return

    # 3) Header senden
    ip, port = nutzer[handle_empfaenger]
    
    # Nachricht im SLCP-Format vorbereiten: IMG <Empfänger> <Größe>
    # das ist die Steuerzeile, die vor dem Bild gesendet wird
    # f-String: setzt automatisch die Variablen ein
    # \n = Zeilenumbruch, wie vom Protokoll gefordert

    img_header = f"IMG {handle_empfaenger} {groesse}\n".encode()
    sock.sendto(img_header, (ip, int(port)))
    print(img_header.decode().strip(), "Bytes")

    # Erste Nachricht senden: den IMG-Befehl mit Empfängername und Bildgröße    
    sent = sock.sendto(bilddaten, (ip, int(port)))
    if sent != groesse:
        # (kommt bei UDP normalerweise nicht vor)
        print("[ERROR] sendto() hat weniger Bytes gesendet als erwartet.")
    else:
        print(f"[INFO] Bild an {handle_empfaenger} gesendet ({groesse} B).")


# --------Bild empfangen--------
## @brief Verarbeitet eine empfangene IMG-Nachricht und speichert das Bild
# @param sock Der UDP-Socket, über den das Bild empfangen wird
# @param teile Die Teile der empfangenen Textnachricht (z. B. ["IMG", "empfänger", "Größe"])
# @param addr Die Adresse (IP, Port) des Absenders
# @param config Die Konfiguration des Clients (z. B. mit Handle und Speicherpfad)

def handle_IMG(sock, teile, addr, config):
    # Header-Format prüfen
    # Prüfen, ob alle erforderliche Teile in der Nachricht sind
    if len(teile) != 3:
        print("[WARN] IMG-Header unvollständig:", " ".join(teile))
        return
    
    # ist der name also an wen das Bild gesendet werden soll
    # Groß-, Kleinschreibung ignorieren
    empfaenger = teile[1].strip().lower()
    eigener_handle = config["client"]["handle"].lower()
    if empfaenger != eigener_handle:
        return  # Bild ist nicht für mich bestimmt – ignorieren

    # Bildgröße lesen  und in Integer umwandeln
    try:
        groesse = int(teile[2])
    except ValueError:
        print("[WARN] Ungültige Groesse:", teile[2])
        return

    if groesse <= 0:
        print("[WARN] Groesse muss > 0 sein")
        return

    # EIN Datagramm mit Bilddaten empfangen
    sock.settimeout(3.0)        # Timeout gegen Hänger
    try:
        #print(f"[DEBUG] Warte auf Bilddaten: {groesse} Bytes …")
        bilddaten, _ = sock.recvfrom(groesse)
        #print(f"[DEBUG] Empfangen: {len(bilddaten)} Bytes")
    except socket.timeout:
        print("[ERROR] Timeout – Bilddatagramm nicht angekommen.")
        return
    finally:
        sock.settimeout(None) # Timeout wieder entfernen

    # Prüfen: Wurden wirklich alle Bytes empfangen?
    if len(bilddaten) != groesse:
        print(f"[ERROR] Bytezahl stimmt nicht ({len(bilddaten)} ≠ {groesse}) – Bild verworfen.")
        return

    # Absendername aus IP ermitteln
    sender_name = next(
        (name for name, (ip, _) in gebe_nutzerliste_zurück().items() if ip == addr[0]),
        "Unbekannt"
    )

    # Speicherort festlegen (aus Config oder Standardverzeichnis)
    zielverzeichnis = config["client"].get("imagepath", "images")
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
# @note Diese Funktion blockiert dauerhaft. Sie sollte in einem separaten Prozess ausgeführt werden.
# @param sock UDP-Socket
# @param konfig_pfad Pfad der aktuellen Config
# @tcp_port verbindung zwischen Main und Netzwerkprozess
def netzwerkprozess(sock, konfig_pfad, tcp_port):
 
    #print("[DEBUG] netzwerkprozess(konfig_pfad) wurde aufgerufen")

    ## @var config
    #  @brief Lädt Konfigurationsparameter wie Handle und Netzwerkports aus config.toml.
    config = lade_config(konfig_pfad)
    print("[INFO] Netzwerkprozess gestartet")

    ## @var tcp_server
    #  @brief Lokaler TCP-Server-Socket für IPC zwischen UI und Netzwerkprozess.
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(("localhost", tcp_port))
    tcp_server.listen(1)

    #print("f[INFO] (Netzwerkprozess) TCP-IPC bereit auf Port {tcp_port}" )

    while True:
        ## @var conn
        #  @brief Socket-Objekt für eine eingehende UI-Verbindung.
        ## @var addr
        #  @brief Adresse des UI-Clients (normalerweise localhost).
        conn, _ = tcp_server.accept()
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
                send_IMG(sock, empfaenger, pfad)
                
            # behandelt den JOIN-Befehl und leitet es Broadcast per UDP weiter 
            # wird von Discovery-Dienst empfangen
            elif teile[0] == "JOIN":
                _, handle, port = teile
                send_join(sock, handle, port, config["network"]["whoisdiscoveryport"])
                 # Lokalen Nutzer selbst eintragen
                eigene_ip = finde_lokale_ip()

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
                
                nutzerdict = gebe_nutzerliste_zurück()
                antwort_liste = [f"{handle} {ip} {port}" for handle, (ip, port) in nutzerdict.items()]

                try:
                    # WHO-Nachricht senden
                    who_sock.sendto(b"WHO", ("255.255.255.255", DISCOVERY_PORT))

                    while True:
                        daten, _ = who_sock.recvfrom(1024)
                        text = daten.decode('utf-8').strip()

                        if text.startswith("KNOWNUSERS"):
                            teile = text.split(" ", 1)
                            if len(teile) == 2:
                                eintraege = teile[1].split(", ")
                              #  nutzerdict = gebe_nutzerliste_zurück()

                                for eintrag in eintraege:
                                    try:
                                        handle, ip, port = eintrag.strip().split(" ")
                                        port = int(port)

                                        # Zugriff direkt auf das zentrale Dictionary
                                        if handle in nutzerdict and nutzerdict[handle] == (ip, port):
                                            continue  # schon drin

                                        # Nutzer in Dictionary speichern
                                        nutzerdict[handle] = (ip, port)

                                        # Nur hinzufügen, wenn NICHT schon in antwort_liste
                                        eintrag_str = f"{handle} {ip} {port}"
                                        if eintrag_str not in antwort_liste:
                                            antwort_liste.append(eintrag_str)


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


def starte_netzwerkprozess(konfig_pfad, tcp_port, port, shared_dict):
    initialisiere_nutzerliste(shared_dict)
    
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