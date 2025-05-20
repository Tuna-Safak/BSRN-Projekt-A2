import socket
import toml
import threading
import os

# woerterbuch zum speichern bekannter teilnehmer (aehnlich wie HashMap)
known_users = {}  

# lädt die Konfigurationsdatei (config.toml) und gibt sie als Wörterbuch zurück

with open("config/config.toml", "r") as f:  
    config = toml.load(f)  

# lädt aus dem config-file den Port für den Discovery-Dienst (whoisport)  # NEU
DISCOVERY_PORT = config["network"]["whoisport"]  # NEU    

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
       # SLCP-Regel: Nachricht muss mindestens 1 Teil enthalten
      # wenn Liste leer ist, dann überspringe den Rest der Schleife
      # und mache mit nächster empfangenen Nachricht weiter
      if not nachrichtTeilen:
        continue
      
      # erstes Wort aus der Nachricht holen, also den Befehl, den der Absender geschickt hat
      befehl = nachrichtTeilen[0]

      if befehl == "JOIN" and len(nachrichtTeilen) == 3:
       # handle = benutzername
        handle = nachrichtTeilen[1]
        port = nachrichtTeilen[2]

       # IP-Adresse aus dem Datenpaket "absender" holen
        ip = absender[0]   

       # benutzer im Woerterbuch speichern
        known_users[handle] = (ip, port)

        print(f" [INFO: ] {handle} ist jetzt bekannt unter {ip}: {port}")
       # who-block

      elif befehl == "WHO" and len(nachrichtTeilen) == 1:
         antwort = "KNOWNUSERS: "

         # join() = alle Elemente in der Liste verbinden zu einem Teilstring 
         # items() =  liste von Tupeln mit Schlüssel und Wert
         antwort += ", ".join(
            f"{handle} {ip} {port}" for handle, (ip, port) in known_users.items()
         )

         # sendto() = methode zum versenden von UDP-Nachrichten
         # encode() = wandelt string in bytes um
         # absender = IP-Adresse und Port an dem die Nachricht gehen soll

         sock.sendto(antwort.encode(), absender)

         print(f"[SEND] → {absender}: {antwort}")

      elif befehl == "LEAVE" and len(nachrichtTeilen) == 2:
         handle = nachrichtTeilen[1]
         
      if handle in known_users:
         
            del known_users[handle]
            print(f"[INFO] {handle} wurde entfernt (LEAVE empfangen)")
      else:
            print(f"[WARNUNG] LEAVE empfangen, aber {handle} war nicht bekannt")
