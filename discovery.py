import socket
# woerterbuch zum speichern bekannter teilnehmer (aehnlich wie HashMap)
bekannte_nutzer = {}  

# socket erstellen
# variable namens 'sock', datentyp socket
# socket.socket() = socket = modul/package, socket() = funktion/klasse
# socket.AF_INET, socket.SOCK_DGRAM = argumente/parameter
# socket.AF_INET = Netzwerk-Typ: IPv4
# socket.SOCK_DGRAM	= UDP-Socket statt TCP

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# sock.setsockopt = option/einstellung setzen fuer socket
# SOL_SOCKET = option gilt nur auf Socket-Ebene (nicht zB für TCP selbst) -> (SOL = Socket Option Level)
# socket.SO_BROADCAST = erlaube Senden/Empfangen von Broadcasts
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# socket.SO_REUSEADDR = erlaube Wiederverwendung einer Port-Adresse
# 1 = aktivieren (True / Ja)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Socket soll ab jetzt auf Port 4000 alle eingehenden Nachrichten empfangen
# sock	= Variable, die den UDP-Socket enthält
# bind()	= Methode, um dem Socket eine Adresse (IP + Port) zu geben
# ('', 4000) = 	'' = alle lokalen IP-Adressen, 4000 = Port für Discovery-Dienst

sock.bind(('', 4000))
print("Discovery-Dienst läuft und hört auf Port 4000...")

while True:
      # recvfrom() = Methode für UDP-Sockets, liefert zwei Werte zurueck, 
      # nachricht = in bytes (inhalt der nachricht), absender = IP-Adresse und Port des Absenders
      # empfängt bis zu 1024 Bytes, Max. Nachrichtenlänge: 512 Zeichen, 1024 = doppelte Menge (Sicherheitsreserve)
      nachricht, absender = sock.recvfrom(1024)
      # message = enthält die Nachricht als Bytes
      # .decode() = wandelt Bytes in String um
      # strip() = entfernt leerzeichen und zeilechumbrueche, vorne und hinten
      message = nachricht.decode().strip()
      # ueberpruefung 
      if len(nachricht) > 512:
        print("Nachricht zu lang - Verstoß gegen SLCP-Protokoll!")
        continue
      # nachrichtTeilen = datentyp: list 
      # split() = teilt die nachricht in Teilstrings 

      nachrichtTeilen = message.split()




