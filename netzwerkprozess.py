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
from UI_utils import lade_config, finde_freien_port
from discovery import nutzerspeichern, gebe_nutzerliste_zurück, discovery_main
# damit TCP und UDP seperat laufen können 


# Lade die Konfiguration aus config.toml
config = lade_config()

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
print(f"[INFO] (Discovery-) Socket gebunden an DISCOVERY_PORT {DISCOVERY_PORT}")

# Gib den Socket an andere Module zurück, falls gewünscht
def get_socket():
    return sock

# -----------JOIN-Nachricht versenden------------------
def send_join(handle, port):
    # allen im Chat wird mitgeteilt, dass ich mich im Chat befinde
    ip = finde_lokale_ip()
    nachricht = f"JOIN {handle} {port} {ip}\n"
    sock.sendto(nachricht.encode('utf-8'), ("255.255.255.255", DISCOVERY_PORT))
    print(f"[JOIN] Gesendet: {nachricht.strip()}")
    
   # nachricht = f"JOIN {handle} {port}\n"
    # JOIN: ist der Befehl, der an alle anderen Computer im Netzwerk gesendet wird
    #sock.sendto(nachricht.encode(), ("255.255.255.255", DISCOVERY_PORT))
    #print(f"[JOIN] Gesendet: {nachricht.strip()}")

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
    # allen im Chat wird mitgeteilt, dass ich den Chat verlasse (Nur Discovery)
    nachricht = f"LEAVE {handle_nutzername}\n"
    sock.sendto(nachricht.encode('utf-8'), ("255.255.255.255", DISCOVERY_PORT))
    print(f"[LEAVE] Gesendet: {nachricht.strip()}")

    # allen per Unicast zeigen das ich leave
    bekannte_nutzer = gebe_nutzerliste_zurück()
    for anderer_handle, (ip, port) in bekannte_nutzer.items():
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

# # -------------Nachricht empfangen-----------------
# def receive_MSG(sock, config):
#     while True:
#         daten, addr = sock.recvfrom(1024)
#         text = daten.decode('utf-8').strip()


#         teile = text.strip().split(" ")
#         if len(teile) == 0:
#             print("Leere Nachricht")
#             continue

#         befehl = teile[0]

#         if teile[0] == "JOIN" and len(teile) >= 3:
#             name = teile[1]
#             port = teile[2]
#             ip = teile[3] if len(teile) >= 4 else addr[0]
#             DISCOVERY_PORT = int(port)  

#         elif befehl == "LEAVE" and len(teile) == 2:
#             handle_leave(teile[1])

#         elif befehl == "MSG" and len(teile) >= 3:
#             absender_handle = teile[1]
#             nachricht =  " ".join(teile[2:])  # alles ab dem dritten Wort
#             print(f"\nNachricht von {absender_handle}: {nachricht}\n> ", end="")

#             if config.get("autoreply_aktiv", False):
#                 autoreply_text = config.get("autoreply", "Ich bin gerade nicht da.")
#                 handle = config["client"]["handle"]
#                 sendMSG(sock, handle, absender_handle, autoreply_text)


#         elif befehl == "IMG" and len(teile) == 3:
#             try:
#                 handle_IMG(sock, teile, addr)
#             except Exception as e:
#                 print(f"Fehler beim Bildempfang: {e}")
   
   
#         elif befehl == "KNOWNUSERS" and len(teile) == 2:
#             eintraege = teile[1].split(", ")
#             nutzerliste = gebe_nutzerliste_zurück()
#             for eintrag in eintraege:
#                 try:
#                      handle, ip, port = eintrag.strip().split(" ")
#                      nutzerliste[handle] = (ip, int(port))
#                      print(f"[INFO] → {handle} @ {ip}:{port} gespeichert")
#                 except ValueError:
#                     print(f"[WARNUNG] Konnte Nutzer nicht verarbeiten: {eintrag}")

#         else:
#             print(f" Unbekannte Nachricht: {text}")


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
            teile = text.strip().split(" ")
            if len(teile) == 0:
                print("Leere Nachricht")
                continue

            befehl = teile[0]

            # Verarbeitung von JOIN-Nachrichten
            if befehl == "JOIN" and len(teile) >= 3:
                name = teile[1]
                port = teile[2]
                ip = teile[3] if len(teile) >= 4 else addr[0]
                DISCOVERY_PORT = int(port)  

            # Verarbeitung von LEAVE-Nachrichten
            elif befehl == "LEAVE" and len(teile) == 2:
                handle_leave(teile[1])

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
                try:
                    handle_IMG(sock, teile, addr)
                except Exception as e:
                    print(f"Fehler beim Bildempfang: {e}")

            # Verarbeitung von KNOWNUSERS-Nachrichten
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
                print(f"Unbekannte Nachricht: {text}")

        except ConnectionResetError as e:
            # Dieser Fehler tritt auf, wenn die Verbindung vom Remote Host geschlossen wurde
            print(f"Fehler: Verbindung vom Remote Host geschlossen. {e}")
            break  # Verbindung unterbrochen, daher Abbruch der Schleife

        except Exception as e:
            # Alle anderen unerwarteten Fehler werden hier abgefangen
            print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
            break  # Abbruch bei unerwartetem Fehler


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



    if groesse > 1400:
        print("Bild zu groß für eine UDP-Nachricht max 1400 Bytes")
        return

    # Nachricht im SLCP-Format vorbereiten: IMG <Empfänger> <Größe>
    # das ist die Steuerzeile, die vor dem Bild gesendet wird
    # f-String: setzt automatisch die Variablen ein
    # \n = Zeilenumbruch, wie vom Protokoll gefordert
    img_header = f"IMG {handle_empfaenger} {groesse}\n"

    # IP-Adresse und DISCOVERY_PORT des Empfängers aus dem Nutzerverzeichnis holen
    ip, port = gebe_nutzerliste_zurück()[handle_empfaenger]
    port = int(port)

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
def handle_IMG(sock, teile, addr):
    # Prüfen, ob genug Teile in der Nachricht sind
    if len(teile) != 3:
        print("Nachricht ist nicht vollständig.")
        return

    # ist der name also an wen das Bild gesendet werden soll
    empfaenger = teile[1]

    try:
        # Die Bildgröße aus dem Text in eine Zahl umwandeln
        groesse = int(teile[2])
    except ValueError:
        # Wenn keine Zahl übergeben wurde sondern was anders
        print("Ungültige Bildgröße.")
        return

    # Die eigentlichen Bilddaten empfangen 
    # recvfrom() wartet auf ein weiteres UDP-Paket
    # Die Anzahl groesse + 1024 gibt einen Puffer mit dazu, falls z. B. mehr Daten ankommen
    # bilddaten enthält die empfangenen Binärdaten 
    bilddaten, addr2 = sock.recvfrom(groesse + 1024)  # etwas Puffer

    # IP-Adresse vom Absender herausfinden bzw speichern
    sender_ip = addr[0]

    # Absendernamen aus der IP-Adresse ermitteln
    # durchsucht known_users
    sender_name = None
    for name, (ip, _) in gebe_nutzerliste_zurück().items():
        if ip == sender_ip:
            sender_name = name
            break

    # Wenn kein Name gefunden wurde, "Unbekannt" setzen
    if sender_name is None:
        sender_name = "Unbekannt"

    # Speicherordner erstellen, falls noch nicht vorhanden
    os.makedirs("empfangene_bilder", exist_ok = True)

    # Bild speichern mit einfachem Namen z.B. büsra_bild.jpg
    # es wird ein vollständiger pfad gebaut
    dateiname = f"{sender_name}_bild.jpg"
    pfad = os.path.join("empfangene_bilder", dateiname)

    # Bild speichern
    # w = write, b = binary
    # öffnet die datei im wb und schreibt alle empfangenen Bytes in die Datei
    with open(pfad, "wb") as f:
        f.write(bilddaten)

    # Info ausgeben, dass das Bild gespeichert wurde
    print(f"Bild von {sender_name} empfangen und gespeichert unter: {pfad}")




## @brief Startet den Netzwerkprozess und lauscht auf Befehle vom UI-Prozess.
#  @details Stellt einen TCP-Server auf localhost:6001 bereit, über den der UI-Prozess Kommandos
#           wie MSG und IMG senden kann. Diese werden analysiert und mit UDP an die Ziel-Peers
#           gemäß SLCP-Protokoll weitergeleitet.
#  @note Diese Funktion blockiert dauerhaft. Sie sollte in einem separaten Prozess ausgeführt werden.
def netzwerkprozess(konfig_pfad=None):
 
   

    ## @var config
    #  @brief Lädt Konfigurationsparameter wie Handle und Netzwerkports aus config.toml.
    config = lade_config(konfig_pfad)
    # startet den Discovery-Dienst im Hintergrund
    threading.Thread(target=discovery_main, daemon=True).start()

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
            daten = conn.recv(1024).decode('utf-8').strip()
            print(f"[Netzwerkprozess] Befehl empfangen: {daten}")

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
                send_leave(handle)
            


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
                    print("[Netzwerkprozess] → Antwort an UI gesendet.")
                except Exception as e:
                    print(f"[Netzwerkprozess] ⚠️ Antwort an UI fehlgeschlagen: {e}")


if __name__ == "__main__":
    threading.Thread(target=receive_MSG, args=(sock, config), daemon=True).start()
    netzwerkprozess()