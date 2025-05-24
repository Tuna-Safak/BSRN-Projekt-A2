import socket
# Bibliothek, ermöglicht Netzwerkomunikation
import toml
import os
import threading
# ermöglicht das gleichzeitige Ausführen von mehreren Threads
import sys
# ermöglicht den Zugriff aus Systemfunktionen

# Wörterbuch zum Speichern bekannter Teilnehmer (ähnlich wie HashMap)
known_users = {}

# ------------Erstellen eines globalen UDP-Sockets-----------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# UDP-Socket wird erstellt, um auf dem angegebenen Port Nachrichten zu empfangen, zu senden, einschließlich Broadcast
# socket.AF_INET: 'address family: internet' --> der Socket verwendet IPv4-Adressen(z.B 192.168.1.10 )
# socket.SOCK_DGRAM: 'socket type:datagram' --> der Socket verwendet UDP-Protokoll (User Datagram Protocol)
# --> für schnelle lokale Kommunikation, ohne vorherige Verbindung    
# --> es gibt keine Garantie, dass Datenpakete in der richtigen Reihenfolge ankommen oder überhaupt ankommen

# Socket wird für Broadcast freigeschaltet
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# option: auf welche Einstellung der Socket gesetzt werden soll (z.B Broadcast)
# beugt Fehler vor : PermissionError: [Errno 13] Permission denied
# weil einige Optionen erst explizit freigeschaltet werden müssen (--> Port mehrfach benutzen, Broadcast)
# Broadcast: ermöglicht es, dass der Socket erlaubt, dass der Nutzer an alle Computer im Netzwerk senden darf

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# 'set socket option' --> ermöglicht besondere Einstellungen für den Socket zu aktivieren, die nicht automatisch aktiv sind
# socket.SOL_SOCKET: 'socket option level' --> legt fest, dass die Option auf Socket-Ebene gesetzt wird
# socket.SO_REUSEADDR: 'socket option name' --> ermöglicht es, dass ein anderer Prozess denselben
# Port nochmal verwenden kann (z.B nach einem Absturz des Programms)
# --> beugt diesem Fehler vor: OSError: [Errno 98] Address already in use

port = 5000
sock.bind(('', port))
# bind(...) verknüpft den Socket mit einer IP-Adresse und Portnummer
# socket auf Port 5000 öffnen (alle IPs erlauben), sorgt dafür, dass der UDP-Socket auf diesem Port lauscht
# '' bedeutet, dass der Socket auf allen verfügbaren IP-Adressen lauscht
# 5000 ist der Port, auf dem das Programm auf eingehende Nachrichten wartet

# Startet Empfangsfunktion im Hintergrund
threading.Thread(target=receive_MSG, args=(sock,), daemon=True).start()
# ein neuer Thread wird gestartet, der die Funktion receive_MSG ausführt
# dadurch läuft das Nachrichten-Empfangen "nebenbei", während man z. B. selbst schreibt
# daemon=True → dieser Thread wird automatisch beendet, wenn das Hauptprogramm beendet wird
# args=(sock,) → übergibt dem Thread den Socket als Argument

# -----------JOIN-Nachricht versenden------------------
def send_join(handle_nutzername, port):
    # allen im Chat wird mitgeteilt, dass ich mich im Chat befinde
    nachricht = f"JOIN {handle_nutzername} {port}\n"
    # JOIN: ist der Befehl, der an alle anderen Computer im Netzwerk gesendet wird
    sock.sendto(nachricht.encode(), ("255.255.255.255", 4000))
    print(f"[JOIN] Gesendet: {nachricht.strip()}")

# -------------Leave-Nachricht versenden-----------------
def send_leave(handle_nutzername):
    # allen im Chat wird mitgeteilt, dass ich den Chat verlasse
    nachricht = f"LEAVE {handle_nutzername}\n"
    sock.sendto(nachricht.encode(), ("255.255.255.255", 4000))
    print(f"[LEAVE] Gesendet: {nachricht.strip()}")

# -------------WHO-Nachricht versenden-----------------
def send_who():
    # es wird erfragt, wer gerade im Chat online ist
    nachricht = "WHO\n"
    sock.sendto(nachricht.encode(), ("255.255.255.255", 4000))
    print("[WHO] Gesendet")

# -------------Nachricht senden-----------------
def sendMSG(handle_nutzername):
    # Nachrichten senden
    while True:
        target = input("Empfänger (Handle): ").strip()
        if target not in known_users:
            print("Nutzer nicht bekannt. Warte auf JOIN oder WHO.")
            continue

        text = input(" Nachricht: ").strip()
        msg = f'MSG {handle_nutzername} "{text}"\n'
        ip, target_port = known_users[target]
        sock.sendto(msg.encode(), (ip, target_port))
        print(f"[MSG] Gesendet an {target}: {text}")

# -------------Nachricht verarbeiten und formatieren-----------------
def handle_MSG(sender, text):
    # Zeigt eine empfangene Nachricht schön formatiert im Terminal an.
    clean_text = text.strip('"')  # Entferne äußere Anführungszeichen
    print(f" Nachricht von {sender}: {clean_text}")

# -------------JOIN verarbeiten-----------------
def handle_join(name, port, addr):
    # Verarbeitung einer JOIN-Nachricht, um neuen Nutzer zu speichern
    ip = addr[0]
    port = int(port)

    if name not in known_users:
        known_users[name] = (ip, port)
        print(f"{name} ist dem Chat beigetreten – {ip}:{port}")
    else:
        known_users[name] = (ip, port)
        print(f"{name} erneut beigetreten – Daten aktualisiert: {ip}:{port}")

# -------------LEAVE verarbeiten-----------------
def handle_leave(name):
    # Verarbeitung einer LEAVE-Nachricht, um Nutzer aus der Liste zu entfernen
    if name in known_users:
        del known_users[name]
        print(f"{name} hat den Chat verlassen")
    else:
        print(f"LEAVE von unbekanntem Nutzer erhalten: {name}")
       
# -------------Bild senden-----------------
# Funktion zum Versenden eines Bildes
# @param handle_sender: Benutzername des Absenders 
# @param handle_empfaenger: Benutzername des Empfängers
# @param bildpfad: Pfad zur Bilddatei
def sendIMG(handle_sender, handle_empfaenger, bildpfad):
    
    # Prüfen, ob der Empfänger überhaupt bekannt ist, also ob wir seine IP-Adresse und Port kennen
    if handle_empfaenger not in known_users:
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

    # Nachricht im SLCP-Format vorbereiten: IMG <Empfänger> <Größe>
    # das ist die Steuerzeile, die vor dem Bild gesendet wird
    # f-String: setzt automatisch die Variablen ein
    # \n = Zeilenumbruch, wie vom Protokoll gefordert
    img_header = f"IMG {handle_empfaenger} {groesse}\n"

    # IP-Adresse und Port des Empfängers aus dem Nutzerverzeichnis holen
    ip, port = known_users[handle_empfaenger]

    # Erste Nachricht senden: den IMG-Befehl mit Empfängername und Bildgröße
    # encode() wandelt den Text in Bytes um, damit er über das Netzwerk geschickt werden kann
    sock.sendto(img_header.encode(), (ip, port))

    # Zweite Nachricht: das eigentliche Bild senden (als Binärdaten)
    sock.sendto(bilddaten, (ip, port))

    # Bestätigung ausgeben, dass das Bild erfolgreich gesendet wurde
    print(f"Bild an {handle_empfaenger} gesendet ({groesse} Bytes)")

# -------------Bild empfangen-----------------
# @brief verarbeitet eine IMG-Nachricht: liest Bilddaten ein und speichert sie
# @param sock Der Socket, über den das Bild empfangen wird
# @param teile Die Teile der empfangenen Textnachricht (z. B. ["IMG", "Ziel", "Größe"])
# @param addr Die Adresse (IP, Port) des Absenders
def handle_IMG(sock, teile, addr):
    # Prüfen, ob genug Teile in der Nachricht sind
    if len(teile) != 3:
        print("Nachricht ist nicht vollständig.")
        return

    empfaenger = teile[1]

    try:
        # Die Bildgröße aus dem Text in eine Zahl umwandeln
        groesse = int(teile[2])
    except ValueError:
        # Wenn keine Zahl übergeben wurde
        print("Ungültige Bildgröße.")
        return

    # Die eigentlichen Bilddaten empfangen (zweites Paket)
    bilddaten, addr2 = sock.recvfrom(groesse + 1024)  # etwas Puffer

    # IP-Adresse vom Absender herausfinden
    sender_ip = addr[0]

    # Absendernamen aus der IP-Adresse ermitteln
    sender_name = None
    for name, (ip, _) in known_users.items():
        if ip == sender_ip:
            sender_name = name
            break

    # Wenn kein Name gefunden wurde, "Unbekannt" setzen
    if sender_name is None:
        sender_name = "Unbekannt"

    # Speicherordner erstellen, falls noch nicht vorhanden
    os.makedirs("empfangene_bilder", exist_ok = True)

    # Bild speichern mit einfachem Namen z.B. büsra_bild.jpg
    dateiname = f"{sender_name}_bild.jpg"
    pfad = os.path.join("empfangene_bilder", dateiname)

    # Bild speichern
    # w = write, b = binary
    with open(pfad, "wb") as f:
        f.write(bilddaten)

    # Info ausgeben, dass Bild gespeichert wurde
    print(f"Bild von {sender_name} empfangen und gespeichert unter: {pfad}")


# -------------Nachricht empfangen-----------------
def receive_MSG(sock):
    # implementieren einer Funktion für das Nachrichten empfangen                  
    while True:
        daten, addr = sock.recvfrom(1024)
        # daten: wandelt die empfangene Nachricht in eine Bytefolge um (noch nicht lesbarer Text)
        # addr: enthält die Adresse des Absenders – ein Tupel wie ('192.168.1.42', 5000)

        text = daten.decode().strip()
        # Nachricht decodieren: in einen lesbaren Text umwandeln

        print(f"Nachricht von {addr}: {text}")
        # erhaltene Nachricht wird ausgegeben

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
            handle_MSG(teile[1], teile[2])
            
        elif befehl == "IMG" and len(teile) == 3:
            handle_IMG(sock, teile, addr)

        else:
            print(f" Unbekannte Nachricht: {text}")




