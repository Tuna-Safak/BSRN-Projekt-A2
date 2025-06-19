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
import toml
import os
from interface import lade_config, finde_freien_port
from discovery import nutzerspeichern, gebe_nutzerliste_zurück, discovery_main
# damit TCP und UDP seperat laufen können 
import sys

if __name__ == "__main__":
    konfig_pfad = sys.argv[1] if len(sys.argv) > 1 else None
else:
    konfig_pfad = None

config = lade_config(konfig_pfad)
# Discovery DISCOVERY_PORT aus Konfig
DISCOVERY_PORT = config["network"]["whoisdiscoveryport"]

def finde_lokale_ip():
    """Ermittelt die echte lokale IP-Adresse (z. B. WLAN) durch Verbindung zu 8.8.8.8."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"[WARNUNG] Lokale IP konnte nicht ermittelt werden: {e}")
        return "127.0.0.1"


# Erstelle den UDP-Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Binde an den freien DISCOVERY_PORT
sock.bind(('', DISCOVERY_PORT))
   

# Gib den Socket an andere Module zurück, falls gewünscht
def get_socket():
    return sock

# -----------JOIN-Nachricht versenden------------------
def send_join(handle, port):
    # allen im Chat wird mitgeteilt, dass ich mich im Chat befinde
    ip = finde_lokale_ip()
    nachricht = f"JOIN {handle} {port} {ip}\n"
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
        print(f"{name} ist dem Chat beigetreten – {ip}:{DISCOVERY_PORT}")
    else:
        gebe_nutzerliste_zurück()[name] = (ip, DISCOVERY_PORT)
        print(f"{name} erneut beigetreten – Daten aktualisiert: {ip}:{DISCOVERY_PORT}")



# -------------Leave-Nachricht versenden-----------------
def send_leave(handle_nutzername):
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
        print(f"{name} hat den Chat verlassen")
    else:
        print(f"LEAVE von unbekanntem Nutzer erhalten: {name}")


# -------------Nachricht senden-----------------
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
    print(f"[SEND] → an {empfaenger_handle} @ {ip}:{port} → {text}")
    sock.sendto(nachricht.encode('utf-8'), (ip, port))


# -------------Nachricht empfangen-----------------
def receive_MSG(sock, config):
    """
    Empfängt Nachrichten vom UDP-Socket und verarbeitet sie.
    """
     
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
                #  print(f"\n[JOIN] {name} ist dem Chat beigetreten.")

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
                print(f"\n[LEAVE] {absender_name} hat den Chat verlassen.")

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
                    nutzerliste = gebe_nutzerliste_zurück()
                    eigener_handle = config["client"]["handle"]
                    for eintrag in eintraege:
                        try:
                            handle, ip, port = eintrag.strip().split(" ")
                            if handle == eigener_handle:
                                continue
                        except ValueError:
                            print(f"[WARNUNG] Konnte Nutzer nicht verarbeiten: {eintrag}")
                else:
                     print("[INFO] Keine Nutzer in KNOWNUSERS-Antwort.")

        except Exception as e:
            print(f"Fehler: {e}")


# -------------Bild senden-----------------
# Funktion zum Versenden eines Bildes
# @param handle_sender: Benutzername des Absenders 
# @param handle_empfaenger: Benutzername des Empfängers
# @param bildpfad: Pfad zur Bilddatei
def sendIMG(handle_sender, handle_empfaenger, bildpfad):
    
    # Prüfen, ob der Empfänger überhaupt bekannt ist, also ob wir seine IP-Adresse und DISCOVERY_PORT kennen
    if handle_empfaenger not in gebe_nutzerliste_zurück():
        print("Empfänger nicht bekannt.")
        return  # die Funktion wird beendet, weil Senden nicht möglich ist

    try:
        # Bilddatei öffnen – "rb" bedeutet:
        # r = read, b = binary (binär lesen, nicht als Text)
        # wir brauchen das für Bilder, weil sie keine Textdateien sind
        with open(bildpfad, "rb") as b:
            # gesamtes Bild als Binärdaten einlesen
            bilddaten = b.read()
    except FileNotFoundError:
        # Wenn der Pfad falsch ist oder das Bild nicht existiert
        print("Bild nicht gefunden:", bildpfad)
        return  # Funktion beenden

    # Bildgröße berechnen (Anzahl der Bytes)
    # wichtig für den Empfänger damit er weiß wie viele Daten kommen
    groesse = len(bilddaten)

    #if groesse > 1400:
     #   print("Bild zu groß für eine UDP-Nachricht max 1400 Bytes")
      #  return

    # Nachricht im SLCP-Format vorbereiten: IMG <Empfänger> <Größe>
    # das ist die Steuerzeile, die vor dem Bild gesendet wird
    # f-String: setzt automatisch die Variablen ein
    # \n = Zeilenumbruch, wie vom Protokoll gefordert
    img_header = f"IMG {handle_empfaenger} {groesse}\n"

    # IP-Adresse und DISCOVERY_PORT des Empfängers aus dem Nutzerverzeichnis holen
    ip, port = gebe_nutzerliste_zurück()[handle_empfaenger]
    port = int(port)

    print("[DEBUG] Sende Header:", img_header.strip())
    print("[DEBUG] Sende Bilddaten:", len(bilddaten), "Bytes")

    # Erste Nachricht senden: den IMG-Befehl mit Empfängername und Bildgröße
    # encode() wandelt den Text in Bytes um, damit er über das Netzwerk geschickt werden kann
    sock.sendto(img_header.encode(), (ip, port))

    # Zweite Nachricht: das eigentliche Bild senden (als Binärdaten)
    sock.sendto(bilddaten, (ip, port))

    # Bestätigung ausgeben, dass das Bild erfolgreich gesendet wurde
    print(f"Bild an {handle_empfaenger} gesendet ({groesse} Bytes)")
   
   

# -------------Bild empfangen-----------------
# @brief verarbeitet eine IMG-Nachricht: liest Bilddaten ein und speichert sie als datei
# @param sock Der UDP-Socket, über den das Bild empfangen wird
# @param teile Die Teile der empfangenen Textnachricht (z. B. ["IMG", "empfänger", "Größe"])
# @param addr Die Adresse (IP, DISCOVERY_PORT) des Absenders
def handle_IMG(sock, teile, addr, config):
    
    # Prüfen, ob genug Teile in der Nachricht sind
    if len(teile) != 3:
        print("Nachricht ist nicht vollständig.")
        return

    # ist der name also an wen das Bild gesendet werden soll
    empfaenger = teile[1].strip().lower()  ### ⬅️ GEÄNDERT
    eigener_handle = config["client"]["handle"].lower()  ### ⬅️ GEÄNDERT
    if empfaenger != eigener_handle:  ### ⬅️ GEÄNDERT
        return  # Bild ist nicht für mich bestimmt – ignorieren

    try:
        groesse = int(teile[2])
    except ValueError:
        print("Ungültige Bildgröße.")
        return
    print(f"[DEBUG] Erwartete Bildgröße: {groesse} Bytes")  # ❗DEBUG

    # ❗NEU: Bilddaten in mehreren Chunks empfangen
    bilddaten = b""
    verbleibend = groesse
    sock.settimeout(3.0)

    try:
        while verbleibend > 0:
            chunk, _ = sock.recvfrom(2048)
            bilddaten += chunk
            verbleibend -= len(chunk)
            print(f"[DEBUG] Chunk empfangen, verbleibend: {verbleibend} Bytes")  # ❗DEBUG
    except socket.timeout:
        print("[ERROR] Bilddaten nicht empfangen - Timeout.")
        return
    finally:
        sock.settimeout(None)

    sender_ip = addr[0]
    if len(bilddaten) == 0:
        print("[FEHLER] Leere Bilddaten empfangen – kein Bild gespeichert!")  # ❗DEBUG
        return

    # Absendernamen aus der IP-Adresse ermitteln
    sender_name = None
    for name, (ip, _) in gebe_nutzerliste_zurück().items():
        if ip == sender_ip:
            sender_name = name
            break
    if sender_name is None:
        sender_name = "Unbekannt"
        print(f"[DEBUG] Sender-Name: {sender_name}, IP: {sender_ip}")  # ❗DEBUG

    zielverzeichnis = config["client"].get("imagepath", "empfangene_bilder")  ### ⬅️ GEÄNDERT
    os.makedirs(zielverzeichnis, exist_ok=True)

    dateiname = f"{sender_name}_bild.jpg"
    pfad = os.path.join(zielverzeichnis, dateiname)

    with open(pfad, "wb") as f:
        f.write(bilddaten)
        print(f"[DEBUG] Bild erfolgreich gespeichert: {pfad}")  # ❗DEBUG

    print(f"Bild von {sender_name} empfangen und gespeichert unter: {pfad}")



## @brief Startet den Netzwerkprozess und lauscht auf Befehle vom UI-Prozess.
#  @details Stellt einen TCP-Server auf localhost:tcpPort bereit, über den der UI-Prozess Kommandos
#           wie MSG und IMG senden kann. Diese werden analysiert und mit UDP an die Ziel-Peers
#           gemäß SLCP-Protokoll weitergeleitet.
#  @note Diese Funktion blockiert dauerhaft. Sie sollte in einem separaten Prozess ausgeführt werden.
def netzwerkprozess(konfig_pfad, tcp_port):
 
    print("[DEBUG] netzwerkprozess(konfig_pfad) wurde aufgerufen")


    ## @var config
    #  @brief Lädt Konfigurationsparameter wie Handle und Netzwerkports aus config.toml.
    config = lade_config(konfig_pfad)
    print("[DEBUG] Netzwerkprozess gestartet")

    # startet den Discovery-Dienst im Hintergrund
    threading.Thread(target=discovery_main, daemon=True).start()

    ## @var tcp_server
    #  @brief Lokaler TCP-Server-Socket für IPC zwischen UI und Netzwerkprozess.
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(("localhost", tcp_port))
    tcp_server.listen(1)


    print("[INFO] (Netzwerkprozess) TCP-IPC bereit auf Port {tcp_port}}" )

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
                sendIMG(config["client"]["handle"], empfaenger, pfad)
                

            # behandelt den JOIN-Befehl und leitet es Broadcast per UDP weiter 
            # wird von Discovery-Dienst empfangen
            elif teile[0] == "JOIN":
                _, handle, port = teile
                send_join(handle, port)

            elif teile[0] == "LEAVE": 
                send_leave(config["client"]["handle"])

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

                try:
                    # Broadcast-Nachricht an alle Peers senden
                    who_sock.sendto(b"WHO\n", ("255.255.255.255", DISCOVERY_PORT))

                    nutzerliste = gebe_nutzerliste_zurück()
                    antwort_liste = []  # lokale Liste zum Rücksenden

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
                    conn.sendall(antwort_text.encode('utf-8'))
                except Exception as e:
                    print(f"[Netzwerkprozess] Antwort an UI fehlgeschlagen: {e}")


if __name__ == "__main__":
    import sys
    import os
    import threading
    from interface import lade_config

    # Argumente auslesen
    konfig_pfad = sys.argv[1] if len(sys.argv) > 1 else None
    tcp_port = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if konfig_pfad is None or not os.path.exists(konfig_pfad):
        print("[FEHLER] Keine gültige Konfigurationsdatei angegeben.")
        sys.exit(1)

    if tcp_port is None:
        print("[FEHLER] Kein TCP-Port angegeben.")
        sys.exit(1)

    # Konfiguration laden
    config = lade_config(konfig_pfad)
    print(f"[DEBUG] Netzwerkprozess gestartet mit TCP-Port {tcp_port}")

    # UDP-Receiver starten
    threading.Thread(target=receive_MSG, args=(get_socket(), config), daemon=True).start()

    # TCP-Server starten
    netzwerkprozess(konfig_pfad, tcp_port)
