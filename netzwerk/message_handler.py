import socket
# Bibliothek, ermöglicht Netzwerkomunikation 
import toml


def open_socket(port):
    # UDP_Socket wird erstellt, um auf dem angegebenen Port Nachrichten zu empfangen, zu senden, einschließlich Broadcast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # erstellt einen neuen Netzwerksocket
        # socket.AF_INET: 'address family: internet' --> der Socket verwendet IPv4-Adressen(z.B 192.168.1.10 )
        # socket.SOCK_DGRAM  : 'socket type:datagram' --> der Socket verwendet UDP-Protokoll (User Datagram Protocol)
            # --> für schnelle lokale Kommunikation, ohne voeherige Verindung    
            # --> es git keine Garantie, dass Datenpakete in der richtigen Reihenfolge ankommen oder überhaupt ankommen
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 'set socket option' --> ermöglicht besondere Einstellungen für den Socket zu aktivieren, die nicht automatisch aktiv sind
        # spcket.SOL_SOCKET: 'socket option level' --> legt fest, dass die Option auf Socket-Ebene gesetzt wird
        # socket.SO_REUSEADDR: 'socket optin naame' --> ermöglicht es, dass ein adnerer Prozess denselben Port nochmal verwenden kann(z.B nach einem Abstrurz des Programms)
            # --> beugt diesen Fehler vor: OSError: [Errno 98] Address already in use
    # 1: aktiviert die Option
    # 0 würde die Option deaktivieren
   
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # option: auf welche Einstellung der Socket gesetzt werden soll (z.B Broasdcast)
        #  beugt Fehler vor : PermissionError: [Errno 13] Permission denied
        # weil einige Optionen erst explizit freigeschaltet werden müssen (--> Port mehrfach benutzen, Broadcast)
            # Broadcast: ermöglicht es, dass der Socket erlaubt, dass der Nutzer an alle Computer im Netzwerk senden darf
    sock.bind(('', port)) 
    return sock




def send_join(sock, handle, port):
    # allen im Chat wird mitgeteilt, dass ich mich im Chat befinde
    # benötigten Eingabewerte der Funktion:
        # sock(geöffneter UDP-Socket)
        # handle: Nutzername e.g. "Alice"
        # port: Portnummer,auf der die Person erreichbar ist, um Nachrichten zu empfangen
    nachricht = f"JOIN {handle} {port}\n"
    # f-String: ermöglicht es, Variablen in einen String einzbauen
    # JOIN: ist der Befehl, der an alle anderen Computer im Netzwerk gesendet wird
    sock.sendto(nachricht.encode(), ("255.255.255.255", 4000))
    # sendto()_ sendet die Nachricht über den UPD-Socket
    # Nachricht wird in Bytes umgewandelt damit sie über das Netzwerk gesendet werden kann
    print(f"[JOIN] Gesendet: {nachricht.strip()}")


def send_leave(sock, handle):
    # allen im Chat wird mitgeteilt, dass ich den Chat verlasse
    nachricht = f"LEAVE {handle}\n"
    sock.sendto(nachricht.encode(), ("255.255.255.255", 4000))
    # 255.255.255.255: Sonderadresse für alle
    print(f"[LEAVE] Gesendet: {nachricht.strip()}")


def send_who(sock):
    # es wird erfragt, wer gerade im Chat online ist
    nachricht = "WHO\n"
    sock.sendto(nachricht.encode(), ("255.255.255.255", 4000))
    print("[WHO] Gesendet")






def sendMSG(handle, ip, port, text):
    # implementieren einer Funktion für das Nachrichtensenden
        nachricht = f"MSG {handle} {text}\n"  
        #Zusammenbauen der Nachricht im SLCP-Format
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #  erstellt eine UDP_Socket

    sock.sendto(nachricht.encode(), (ip, port))  
    # sendto() sendet die Nachricht an ein Datenpaket
    # nachricht.encode(): Nachricht(Text) wird in Bytes umgewandelt, damit sie über das Netzwerk gesendet werden kann)
    # (ip, port): das ist das Zielgerät: an welches Ziel-IP + welche Portnummer die Nachricht gesendet werden soll
    sock.close()  
    # socket wird geschlossen, um 



    def receiveMSG():
        # implementieren einer Funktion für das Nachrichten empfangen                   
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    # erneutes erstellen einer UDP-Socket
    sock.bind(('', 5000)) 
    # bind(...) verknüpft den Socket mit einer IP-Adresse und Portnummer
    # socket auf Port 5000 öffnen (alle IPs erlauben), sorgt dafür, dass der UDP-Socket auf diesem Port lauscht, also Nachrichten empfangen kann
    # '' bedeutet, dass der Socket auf allen verfügbaren IP-Adressen lauscht
    # 5000 ist der Port, auf dem das Programm auf eingehende Nachrichten wartet, von dem ich von allen Computern UDP-Nachrichten empfangen kann, was in einem Peer-to-Peer-Chat-Projekt notwendig ist (es ist wichtig, dem Socket zu vermitteln von wo er die Nachricht empfangen soll, weil es sonst nicht weiß,)
    daten, addr = sock.recvfrom(1024) 
    # sock: UDP-Socket mit dem aud die Nachricht gewartet wird (eine Art Briefkasten)
    #  recvfrom(1024): wartet auf eine Nachricht mit einer maximalen Größe von 1024 Bytes
    # daten: wandelt die empfangene Nachricht in eine Bytefolge um(noch nicht lesbarer Text)
    # addr: enthält die Adresse des Absenders- ein Tupel(Liste, mit festem Inhalt, Datensatz mit mehreren Werten) wie ('192.168.1.42', 5000)
    text = daten.decode().strip()  
    # Nachricht decodieren: in einen lesbaren Text umwandeln
    # strip(): entfernt Leerzeichen und Zeilenumbrüche am Anfang und Ende der Nachricht
    print("Nachricht empfangen:", text)  
    # erhaltene Nachricht wird ausgegeben
    print("Absender:", addr)
    # gibt die Adresse des Absenders aus
    sock.close() 
    #  schließt Socket --> beendet die Verbindung
    # dmait mein Programm nicht mehr auf weitere Daten(Nachrichten) wartet




