#Argumente aus der Kommandozeile auslesen --handel
import sys
#Modul zum Parsen von .toml-Dateien
import toml
# Für Prüfung freier Ports per UDP-Socket
import socket
#Für Datei- und Pfadprüfung (z. B. ob config.toml existiert)
import os

#from UI_utils import erstelle_neue_config
## import questionary
## @file interface.py
# @brief interface der Kommmandozeile für das Chat-Programm
# @details Menüauswahl und Eingaben über das Terminal

## Fragte eine Auswahl ab
# @return Auswahl des Benutzers als String
#wird in der main aufgerufen
def menue():
    print("\nMenü\n")
    print("1. Teilnehmer anzeigen")
    print("2. Nachricht senden")
    print("3. Bild senden")
    print("4. Autoreply aktivieren/deaktivieren")
    print("5. Autoreply ändern")
    print("6. Konfiguration anzeigen/bearbeiten")
    print("7. Chat verlassen")
    return input("> Bitte wählen: ")

def menue():
    print("\n\033[1mMenü\033[0m\n")  # fette Überschrift

    print("\033[93m1. Teilnehmer anzeigen\033[0m")               # Gelb
    print("\033[96m2. Nachricht senden\033[0m")                   # Hellcyan
    print("\033[95m3. Bild senden\033[0m")                        # Magenta
    print("\033[92m4. Autoreply aktivieren/deaktivieren\033[0m") # Grün
    print("\033[92m5. Autoreply ändern\033[0m")                   # Grün
    print("\033[90m6. Konfiguration anzeigen/bearbeiten\033[0m") # Grau
    print("\033[91m7. Chat verlassen\033[0m")                     # Rot

    return input("\n> \033[1mBitte wählen:\033[0m ")


## Eingabe des Benutzernames
# @return Benutzername (Handle) als String
def nutzernamen_abfragen():
    """
    Fragt den Benutzernamen ab und erstellt bei Bedarf eine neue Konfigurationsdatei.
    
    @return Der Benutzername
    """
  
    handle = input("Bitte Benutzernamen eingeben: ")
        

    # Pfad zur Konfigurationsdatei des Benutzers
    konfig_pfad = f"Konfigurationsdateien/config_{handle.lower()}.toml"

    # Überprüfen, ob bereits eine Konfigurationsdatei für diesen Benutzer existiert
    if not os.path.exists(konfig_pfad):
        # Wenn nicht, erstelle eine neue Konfigurationsdatei
        erstelle_neue_config(handle)  # Dies ist die Funktion aus UI_utils.py
    
    return handle


## Eingabe der zu versendend Nachricht an eine bestimmten Empfänger
# @return 
def eingabe_nachricht():
    empfaenger = input("Empfänger-Handle: ")
    nachricht = input("Nachricht: ")
    return empfaenger, nachricht

## Eingabe des Bildpfads und des Empfängers
# @return 
def eingabe_bild():
    empfaenger = input("Empfänger-Handle: ")
    bildpfad = input("Pfad zum Bild: ")
    return empfaenger, bildpfad

## Eingabe der Autoreply Nachricht
# @return Die Config-Datei wird verändert
#gibt erst die aktuelle nachricht aus und fragt dann nach einer neuen
#nachricht in der Config einsehbar

def autoreply_umschalten(config, pfad):
    aktuell = config.get("client", {}).get("autoreply", "")  # Liest aktuellen Autoreply
    print(f"Aktueller Autoreply-Text: '{aktuell}'")
    
    neu = input("Neuer Autoreply-Text: ")
    config["client"]["autoreply"] = neu
    config["client"]["autoreply_aktiv"] = bool(neu.strip())  # Aktiv, wenn Text vorhanden
    print(f"Änderung wurde gespeichert in: {pfad}")

    # >>> Änderung hier: benutze den tatsächlich geladenen Pfad statt festem Dateinamen
    with open(pfad, "w") as f:
        toml.dump(config, f)

    return config

def autoreply_einschalten(config, pfad):
    aktuell = config.get("client", {}).get("autoreply_aktiv", False)
    neu = not aktuell  # Umschalten
    config["client"]["autoreply_aktiv"] = neu

    print(f"[INFO] Autoreply wurde {'aktiviert' if neu else 'deaktiviert'}.")

    # Speichern der aktualisierten config
    with open(pfad, "w", encoding="utf-8") as f:
        toml.dump(config, f)

    return config


import os          


#: @brief Pfad zur standardmäßigen Konfigurationsdatei, wird großgeschrieben da Konstante 
KONFIGURATIONSDATEI = "Konfigurationsdateien/config.toml"

def lade_config(pfad=None):
    # @brief lädt die TOML-Konfigurationsdatei und gibt sie als Dictionary zurück (Parsing).
    # @return dict mit den Konfigurationswerten
    # @raises FileNotFoundError wenn die Datei nicht existiert
    if pfad is None:
        pfad = "Konfigurationsdateien/config.toml"

    if os.path.exists(pfad):
       
        return toml.load(pfad)
    else:
        raise FileNotFoundError("config.toml nicht gefunden.") 

def erstelle_neue_config(handle):
    # @brief Erstellt eine neue Konfigurationsdatei für den Benutzer, falls sie noch nicht existiert.
    # @param handle: Der Benutzername für den die Konfiguration erstellt wird.
    # Standard-Konfigurationswerte für den Benutzer
    config = {
        "client": {
            "handle": handle,
            "port":5000,
            "whoisport": 4000,
            "autoreply": "Bin nicht da",  # Standardwert für autoreply
            "autoreply_aktiv": False,
            "imagepath":"images/"
        },
        "network": {
            "whoisdiscoveryport":4000,
            "port_min": 5000,
            "port_max": 5100
        }
    }

    # Dateipfad für die neue Konfigurationsdatei
    konfig_pfad = f"Konfigurationsdateien/config_{handle.lower()}.toml"

    # Speichern der Konfigurationsdatei im TOML-Format
    with open(konfig_pfad, "w") as f:
        toml.dump(config, f)
    
## @brief Findet einen freien TCP-Port auf dem lokalen System.
#  Diese Funktion erstellt einen temporären TCP-Socket, der sich an Port 0 bindet.
#  Die Angabe von Port 0 signalisiert dem Betriebssystem, dass ein beliebiger freier Port
#  automatisch zugewiesen werden soll. Nachdem der Socket gebunden ist, wird der
#  tatsächlich zugewiesene Port abgefragt und zurückgegeben.
#  @return int Ein freier TCP-Port, der aktuell nicht verwendet wird.
def finde_freien_tcp_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Port 0 = automatisch freien Port finden
        return s.getsockname()[1]

# @brief Durchsucht den in der Konfigurationsdatei angegebenen Portbereich nach einem freien UDP-Port.
# @param config dict mit den Konfigurationswerten, erwartet Schlüssel 'port_min' und 'port_max'
# @return int erster freier UDP-Port im Bereich
# @raises ValueError Wenn 'port_min' oder 'port_max' in der Konfiguration fehlen
# @raises RuntimeError wenn kein freier Port im Bereich gefunden wird
def finde_freien_port(config):
    #Holt die Konfigurationswerte port_min und port_max aus dem config-Dictionary
    port_min = config["network"].get("port_min")
    port_max = config["network"].get("port_max")

    # Fehlermeldung, falls einer der benötigten Ports in der Konfigurationsdatei fehlen.
    if port_min is None or port_max is None:
        raise ValueError("Konfigurationswerte 'port_min' und 'port_max' fehlen.")
   
    # Schleife über alle Ports im Bereich.
    # range(... + 1) ist notwendig, weil range die letzte Position nicht einbezieht.
    for port in range(port_min, port_max + 1):
   
      try:
        # Erstellt einen Socket mit IPv4 (Adressfamilie = AF_INET) und UDP (Sockettyp = SOCK_DGRAM).
        # Kein 'with', damit der Socket erhalten bleibt und der Port reserviert bleibt.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


        # Versucht, den Socket an einen bestimmten Port zu binden:
        # "" steht für „alle Netzwerk-Interfaces“ (z. B. localhost und LAN).
        # port ist der aktuell getestete Port.
        # Wenn das gelingt, ist der Port frei – also wird er sofort zurückgegeben.
        sock.bind(("", port))
        
        return port, sock

      except OSError:
        # Wenn der Bind-Vorgang fehlschlägt, wird ein OSError ausgelöst und die Schleife wird fortgesetzt.
        continue 

    # Wenn kein einziger Port im angegebenen Bereich verfügbar war, bricht die Funktion mit einem RuntimeError ab
    raise RuntimeError("Kein freier UDP-Port im Bereich {} {} gefunden.".format(port_min, port_max))
 





