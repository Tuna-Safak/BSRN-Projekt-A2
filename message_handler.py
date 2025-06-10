import socket
# Bibliothek, ermöglicht Netzwerkomunikation
import toml
import os
import threading
# ermöglicht das gleichzeitige Ausführen von mehreren Threads
import sys
# ermöglicht den Zugriff aus Systemfunktionen
from discovery import gebe_nutzerliste_zurück
# ermöglicht das Laden der Konfigdatei
from UI_utils import lade_config, finde_freien_port

# Lade die Konfiguration aus config.toml
config = lade_config()

# Discovery DISCOVERY_PORT aus Konfig
DISCOVERY_PORT = config["network"]["whoisdiscoveryport"]

# Erstelle den UDP-Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Binde an den freien DISCOVERY_PORT
sock.bind(('', DISCOVERY_PORT))
print(f"[INFO] (Discovery-) Socket gebunden an DISCOVERY_PORT {DISCOVERY_PORT}")


#port = finde_freien_port(config)
#sock.bind(('', port))
#print(f"[INFO] Socket gebunden an Port {port}")
#port = finde_freien_port(config)


# Gib den Socket an andere Module zurück, falls gewünscht
def get_socket():
    return sock

# -----------JOIN-Nachricht versenden------------------
def send_join(handle_nutzername, port):
    # allen im Chat wird mitgeteilt, dass ich mich im Chat befinde
    
    nachricht = f"JOIN {handle_nutzername} {port}\n"
    # JOIN: ist der Befehl, der an alle anderen Computer im Netzwerk gesendet wird
    sock.sendto(nachricht.encode(), ("255.255.255.255", DISCOVERY_PORT))
    print(f"[JOIN] Gesendet: {nachricht.strip()}")

# -------------JOIN verarbeiten-----------------
def handle_join(name, DISCOVERY_PORT, addr):
    # Verarbeitung einer JOIN-Nachricht, um neuen Nutzer zu speichern
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
    # allen im Chat wird mitgeteilt, dass ich den Chat verlasse
    nachricht = f"LEAVE {handle_nutzername}\n"
    sock.sendto(nachricht.encode(), ("255.255.255.255", DISCOVERY_PORT))
    print(f"[LEAVE] Gesendet: {nachricht.strip()}")

# -------------LEAVE verarbeiten-----------------
def handle_leave(name):
    # Verarbeitung einer LEAVE-Nachricht, um Nutzer aus der Liste zu entfernen
    if name in gebe_nutzerliste_zurück():
        del gebe_nutzerliste_zurück()[name]
        print(f"{name} hat den Chat verlassen")
    else:
        print(f"LEAVE von unbekanntem Nutzer erhalten: {name}")


# -------------Nachricht senden-----------------
def sendMSG (sock, config, handle, empfaenger_handle, text):
    if empfaenger_handle not in gebe_nutzerliste_zurück():
        print("Empfänger nicht bekannt.")
        print(f"Bekannte Nutzer: {gebe_nutzerliste_zurück()()}")
        return

    nachricht = f'MSG {config[handle]} "{text}"\n'
    ip, DISCOVERY_PORT = gebe_nutzerliste_zurück()[empfaenger_handle]
    print(f"[SEND] → an {empfaenger_handle} @ {ip}:{DISCOVERY_PORT} → {text}")
    sock.sendto(nachricht.encode(), (ip, DISCOVERY_PORT))


# -------------Nachricht verarbeiten und formatieren-----------------
def handle_MSG(sender, text):
    # Zeigt eine empfangene Nachricht schön formatiert im Terminal an.
    clean_text = text.strip('"')  # Entferne äußere Anführungszeichen
    print(f" Nachricht von {sender}: {clean_text}")

# -------------Nachricht empfangen-----------------
def receive_MSG(sock, config):
    while True:
        daten, addr = sock.recvfrom(1024)
        text = daten.decode().strip()
        print(f"Nachricht von {addr}: {text}")

        teile = text.split(' ', 2)
        if len(teile) == 0:
            print("Leere Nachricht")
            continue

        befehl = teile[0]

        if befehl == "JOIN" and len(teile) == 3:
            handle_join(teile[1], teile[2], addr)

        elif befehl == "LEAVE" and len(teile) == 2:
            handle_leave(teile[1])

        elif befehl == "MSG" and len(teile) == 3:
            absender_handle = teile[1]
            nachricht = teile[2]
            print(f"Nachricht von {absender_handle}: {nachricht}\n> ", end="")

            if config.get("autoreply_aktiv", False):
                autoreply_text = config.get("autoreply", "Ich bin gerade nicht da.")
                sendMSG(sock, config["handle"], absender_handle, autoreply_text)

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
    ip, DISCOVERY_PORT = gebe_nutzerliste_zurück()[handle_empfaenger]

    # Erste Nachricht senden: den IMG-Befehl mit Empfängername und Bildgröße
    # encode() wandelt den Text in Bytes um, damit er über das Netzwerk geschickt werden kann
    sock.sendto(img_header.encode(), (ip, DISCOVERY_PORT))

    # Zweite Nachricht: das eigentliche Bild senden (als Binärdaten)
    sock.sendto(bilddaten, (ip, DISCOVERY_PORT))

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

