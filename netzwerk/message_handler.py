import socket
# Bibliothek, ermöglicht Netzwerkomunikation
import toml
import os
import threading
# ermöglicht das gleichzeitige Ausführen von mehreren Threads
import sys
# ermöglicht den Zugriff aus Systemfunktionen




# -------------Konfigurationsdatei laden-----------------
def load_config():
    # lädt die Konfigurationsdatei (config.toml) und gibt sie als Wörterbuch zurück
    with open("config.toml", "r") as f:
        # öffnet die Datei im Lesemodus ("r") und nennt sie "f"
        return toml.load(f)
        # lädt und parst den Inhalt der Datei im TOML-Format in ein Python-Wörterbuch

config = load_config()
handle = config["user"]["handle"]
port = config["network"]["port"]




# Startet Empfangsfunktion im Hintergrund
threading.Thread(target=receive_MSG, args=(sock,), daemon=True).start()


    # ein neuer Thread wird gestartet, der die Funktion receive_MSG ausführt
    # dadurch läuft das Nachrichten-Empfangen "nebenbei", während man z. B. selbst schreibt
    # daemon=True → dieser Thread wird automatisch beendet, wenn das Hauptprogramm beendet wird
    # args=(sock,) → übergibt dem Thread den Socket als Argument


# ------------Erstellen eines globalen UDP-Sockets-----------------


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# UDP-Socket wird erstellt, um auf dem angegebenen Port Nachrichten zu empfangen, zu senden, einschließlich Broadcast
# socket.AF_INET: 'address family: internet' --> der Socket verwendet IPv4-Adressen(z.B 192.168.1.10 )
        # socket.SOCK_DGRAM  : 'socket type:datagram' --> der Socket verwendet UDP-Protokoll (User Datagram Protocol)
            # --> für schnelle lokale Kommunikation, ohne voeherige Verindung    
            # --> es git keine Garantie, dass Datenpakete in der richtigen Reihenfolge ankommen oder überhaupt ankommen
# Socket wird für Broadcast freigeschaltet
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# option: auf welche Einstellung der Socket gesetzt werden soll (z.B Broasdcast)
        #  beugt Fehler vor : PermissionError: [Errno 13] Permission denied
        # weil einige Optionen erst explizit freigeschaltet werden müssen (--> Port mehrfach benutzen, Broadcast)
            # Broadcast: ermöglicht es, dass der Socket erlaubt, dass der Nutzer an alle Computer im Netzwerk senden darf


   
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 'set socket option' --> ermöglicht besondere Einstellungen für den Socket zu aktivieren, die nicht automatisch aktiv sind
        # spcket.SOL_SOCKET: 'socket option level' --> legt fest, dass die Option auf Socket-Ebene gesetzt wird
        # socket.SO_REUSEADDR: 'socket optin naame' --> ermöglicht es, dass ein adnerer Prozess denselben
        # Port nochmal verwenden kann(z.B nach einem Abstrurz des Programms)
            # --> beugt diesen Fehler vor: OSError: [Errno 98] Address already in use
    # 1: aktiviert die Option
    # 0 würde die Option deaktivieren
   
   
port=5000
sock.bind(('', port))
# bind(...) verknüpft den Socket mit einer IP-Adresse und Portnummer
    # socket auf Port 5000 öffnen (alle IPs erlauben), sorgt dafür, dass der UDP-Socket auf diesem Port lauscht, also Nachrichten empfangen kann
    # '' bedeutet, dass der Socket auf allen verfügbaren IP-Adressen lauscht
    # 5000 ist der Port, auf dem das Programm auf eingehende Nachrichten wartet, von dem ich von allen Computern
    # UDP-Nachrichten empfangen kann, was in einem Peer-to-Peer-Chat-Projekt notwendig ist (es ist wichtig, dem Socket zu vermitteln,
    #  von wo er die Nachricht empfangen soll, weil es sonst nicht weiß,)

   


# -----------JOIN-Nachricht versenden------------------
def send_join(handle_nutzername, port):
    # allen im Chat wird mitgeteilt, dass ich mich im Chat befinde
    # benötigten Eingabewerte der Funktion:
        # handle: Nutzername e.g. "Alice"
        # port: Portnummer,auf der die Person erreichbar ist, um Nachrichten zu empfangen
    nachricht = f"JOIN {handle_nutzername} {port}\n"
    # f-String: ermöglicht es, Variablen in einen String einzbauen
    # JOIN: ist der Befehl, der an alle anderen Computer im Netzwerk gesendet wird
    sock.sendto(nachricht.encode(), ("255.255.255.255", 4000))
    # sendto()_ sendet die Nachricht über den UPD-Socket
    # Nachricht wird in Bytes umgewandelt damit sie über das Netzwerk gesendet werden kann
    print(f"[JOIN] Gesendet: {nachricht.strip()}")


# -------------Leave-Nachricht versenden-----------------
def send_leave(handle_nutzername):
    # allen im Chat wird mitgeteilt, dass ich den Chat verlasse
    nachricht = f"LEAVE {handle_nutzername}\n"
    sock.sendto(nachricht.encode(), ("255.255.255.255", 4000))
    # 255.255.255.255: Sonderadresse für alle
    print(f"[LEAVE] Gesendet: {nachricht.strip()}")


# -------------WHO_Nachricht versenden-----------------


def send_who(sock):
    # es wird erfragt, wer gerade im Chat online ist
    nachricht = "WHO\n"
    sock.sendto(nachricht.encode(), ("255.255.255.255", 4000))
    print("[WHO] Gesendet")





def handle_join(name, port, addr):
    # Verarbeitung einer JOIN-Nachricht, um neuen Nutzer zu speichern
    ip = addr[0]  # IP-Adresse aus dem Tupel (addr = (ip, port))
    port = int(port)  # Port in Zahl umwandeln


    if name not in known_users:
        known_users[name] = (ip, port)
        print(f"{name} ist dem Chat beigetreten – {ip}:{port}")
    else:
        # falls Teilnehmer bereits bekannt ist, eventuell IP/Port aktualisieren
        known_users[name] = (ip, port)
        print(f"name} erneut beigetreten – Daten aktualisiert: {ip}:{port}")


def handle_leave(name):
    # Verarbeitung einer LEAVE-Nachricht, um Nutzer aus der Liste zu entfernen
    if name in known_users:
        del known_users[name]
        print(f"{name} hat den Chat verlassen")
    else:
        print(f"LEAVE von unbekanntem Nutzer erhalten: {name}")
     



# -------------Nachrticht senden-----------------
def sendMSG(handle_nutzername, ip, port, text):
    # implementieren einer Funktion für das Nachrichtensenden
      #  Nachrichten senden
    while True:
        target = input("Empfänger (Handle): ").strip()
        if target not in known_users:
            print("Nutzer nicht bekannt. Warte auf JOIN oder WHO.")
            continue


        text = input(" Nachricht: ").strip()
        msg = f'MSG {handle_nutzername} "{text}"\n'
        joip, target_port = known_users[target]
        sock.sendto(msg.encode(), (ip, target_port))
        sock.sendto(nachricht.encode(), (ip, port))  
        # sendto() sendet die Nachricht an ein Datenpaket
        # nachricht.encode(): Nachricht(Text) wird in Bytes umgewandelt, damit sie über das Netzwerk gesendet werden kann)
        # (ip, port): das ist das Zielgerät: an welches Ziel-IP + welche Portnummer die Nachricht gesendet werden soll




# -------------Nachrticht verarbeiten und formatieren-----------------


def handle_msg(sender, text):
    # Zeigt eine empfangene Nachricht schön formatiert im Terminal an.
    clean_text = text.strip('"')  # Entferne äußere Anführungszeichen
    # Entfernt Anführungszeichen am Anfang/Ende.
    print(f" Nachricht von {sender}: {clean_text}")






# -------------Nachrticht empfangen-----------------
def receive_MSG(sock):
    # implementieren einer Funktion für das Nachrichten empfangen                  
    # Wartet auf eine Nachricht über den Socket, dekodiert sie und verarbeitet sie mit handle_msg.
    daten, addr = sock.recvfrom(1024)
    # daten: wandelt die empfangene Nachricht in eine Bytefolge um (noch nicht lesbarer Text)
    # addr: enthält die Adresse des Absenders – ein Tupel (Liste mit festem Inhalt, Datensatz mit mehreren Werten) wie ('192.168.1.42', 5000)
    # recvfrom(1024): wartet auf eine Nachricht mit einer maximalen Größe von 1024 Bytes


    text = daten.decode().strip()  
    # Nachricht decodieren: in einen lesbaren Text umwandeln
    # strip(): entfernt Leerzeichen und Zeilenumbrüche am Anfang und Ende der Nachricht


    print(f"Nachricht von {addr}: {text}")
    # erhaltene Nachricht wird ausgegeben


    # Nachricht analysieren (Parsing)
    teile = text.split(' ', 2)


    if len(teile) == 0:
        print("Leere Nachricht")
        return


    befehl = teile[0]


    if befehl == "JOIN" and len(teile) == 3:
        handle_join(teile[1], teile[2], addr)
        # wenn der Befehl "JOIN" ist und dieser 3 Komponenten hat, dann wird die Funktion handle_join aufgerufen
        # daher der Beitritt des Nutzer in den Chat anerkannt
        # (z. B. ["JOIN", "Bob", "5000"]),


    elif befehl == "LEAVE" and len(teile) == 2:
        handle_leave(teile[1])
        # wenn der Befehl "LEAVE" ist und nur 2 Komponenten hat → handle_leave()
        # so verlässt der Nutzer den Chat
        # ["LEAVE", "Bob"]),


    elif befehl == "MSG" and len(teile) == 3:
        handle_msg(teile[1], teile[2])
        # wenn der Befehl "MSG" ist und 3 Teile hat → handle_msg()
        # dann wird die Nachricht angezeigt
        # (z. B. ["MSG", "Bob", "Hallo"])


    else:
        print(f" Unbekannte Nachricht: {text}")







