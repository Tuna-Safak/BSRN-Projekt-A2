## @file discovery.py
## @brief Discovery-Dienst für SLCP – empfängt JOIN, WHO, LEAVE
## @details Verwaltet bekannte Nutzer und antwortet auf WHO-Anfragen

import socket
import toml
import threading
#Für Datei- und Pfadprüfung (z. B. ob config.toml existiert)
import os

## woerterbuch zum speichern bekannter teilnehmer (aehnlich wie HashMap)
known_users = {}  

## open(...) = Python-Funktion, mit der du Dateien öffnen kannst
## "config.toml" = Pfad zur Datei → in diesem Fall die Datei config.toml im aktuellen Verzeichnis
## "r" = Öffnen im Lese-Modus (read) → (lesen, nicht verändern)
## as f = die geöffnete Datei wird unter dem Namen f gespeichert → f ist ab jetzt eine Datei-Variable
## with ... as = sogenannter "Kontext-Manager":
## Öffnet die Datei
## Führt den eingerückten Block aus
## Schließt die Datei automatisch wieder, sobald der Block fertig ist


with open("Konfigurationsdateien/config.toml", "r") as f: 
    config = toml.load(f)  

## lädt aus dem config-file den Port für den Discovery-Dienst (whoisdiscoveryport) 
## DISCOVERY_PORT = die neue Variable, in der der Port gespeichert wird
## config["network"]["whoisdiscoveryport"] = der Wert, der aus config.toml herausgelesen wird

DISCOVERY_PORT = config["network"]["whoisdiscoveryport"] 

## socket erstellen
## variable namens 'sock', datentyp socket
## socket.socket() = socket = modul/package, socket() = funktion/klasse
## socket.AF_INET, socket.SOCK_DGRAM = argumente/parameter
## socket.AF_INET = Netzwerk-Typ: IPv4
## socket.SOCK_DGRAM	= UDP-Socket statt TCP

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

## sock.setsockopt = option/einstellung setzen fuer socket
## SOL_SOCKET = option gilt nur auf Socket-Ebene (nicht zB für TCP selbst) -> (SOL = Socket Option Level)
## socket.SO_BROADCAST = erlaube Senden/Empfangen von Broadcasts
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
## socket.SO_REUSEADDR = erlaube Wiederverwendung einer Port-Adresse
## 1 = aktivieren (True / Ja)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


## Liste die nur erlaubt, dass diese 3 Funktionen importiert werden
__all__ = ["sende_join", "sende_leave", "sende_who"] 

## 255.255.255.255 broadcast adresse (Sendet Nachricht an alle Geräte im lokalen Netzwerk egal welche IP)

## zusammenfassen des codes für den import 

## discovery prozess starten
def discovery_main():
    print("[INFO] Discovery-Prozess gestartet. Läuft auf Port 4000")
    nutzerspeichern()

def nutzerspeichern(): 
## bindet den Socket an eine IP-Adresse und einen Port
## sock	= Variable, die den UDP-Socket enthält
## bind()	= Methode, um dem Socket eine Adresse (IP + Port) zu geben
## ('', DISCOVERY_PORT) = '' bedeutet: alle lokalen IP-Adressen, Port kommt aus der Konfigurationsdatei
  try:
    sock.bind(('', DISCOVERY_PORT))
  except OSError:
    print(f"[INFO] Discovery-Dienst läuft bereits auf Port {DISCOVERY_PORT} – kein erneuter Start.")
    return  # bricht Funktion ab → kein zweiter Listener startet


  while True:
      ## recvfrom() = Methode für UDP-Sockets, liefert zwei Werte zurueck, 
      ## nachricht = in bytes (inhalt der nachricht), absender = IP-Adresse und Port des Absenders
      ## empfängt bis zu 1024 Bytes, Max. Nachrichtenlänge: 512 Zeichen, 1024 = doppelte Menge (Sicherheitsreserve)
        nachricht, absender = sock.recvfrom(1024)
      
      ## message = enthält die Nachricht als Bytes
      ## .decode() = wandelt Bytes in String um
      ## strip() = entfernt leerzeichen und zeilechumbrueche, vorne und hinten
        message = nachricht.decode('utf-8').strip()

      ## ueberpruefung 
        if len(nachricht) > 512:
          print("Nachricht zu lang - Verstoß gegen SLCP-Protokoll!")
          continue
      
      ## nachrichtTeilen = datentyp: list 
      ## split() = teilt die nachricht in Teilstrings 
        nachrichtTeilen = message.split()
      ## SLCP-Regel: Nachricht muss mindestens 1 Teil enthalten
      ## wenn Liste leer ist, dann überspringe den Rest der Schleife
      ## und mache mit nächster empfangenen Nachricht weiter
        if not nachrichtTeilen:
          continue
      
      ## erstes Wort aus der Nachricht holen, also den Befehl, den der Absender geschickt hat
        befehl = nachrichtTeilen[0]

        if befehl == "JOIN" and len(nachrichtTeilen) == 3:
       ## handle = benutzername
          handle = nachrichtTeilen[1]
          port = nachrichtTeilen[2]

       ## IP-Adresse aus dem Datenpaket "absender" holen
          ip = absender[0]   
          print(f"\n{handle} ist dem Chat beigetreten")
       ## benutzer im Woerterbuch speichern
          known_users[handle] = (ip, port)


          #print(f" [INFO: ] {handle} ist jetzt bekannt unter {ip}: {port}")
       ## who-block

        elif befehl == "WHO" and len(nachrichtTeilen) == 1:
          antwort = "KNOWNUSERS "

         ## join() = alle Elemente in der Liste verbinden zu einem Teilstring 
         ## items() =  liste von Tupeln mit Schlüssel und Wert
          antwort += ", ".join(
            f"{handle} {ip} {port}" for handle, (ip, port) in known_users.items()
          )
          
         ## sendto() = methode zum versenden von UDP-Nachrichten
         ## encode() = wandelt string in bytes um
         ## absender = IP-Adresse und Port an dem die Nachricht gehen soll

          sock.sendto(antwort.encode('utf-8'), absender)
         
#Löschen
#def zeige_bekannte_nutzer():
 #   print(" Bekannte Nutzer:")
  #  for handle, (ip, port) in known_users.items():
   #     print(f"  {handle} → {ip}:{port}")     

def gebe_nutzerliste_zurück():
   return known_users


#if __name__ == "__main__":
 #   discovery_main()