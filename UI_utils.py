"""
@file UI_utils.py
@brief lädt eine TOML-Konfigurationsdatei und stellt sie als Dictionary bereit.
"""
import os          
#Für Datei- und Pfadprüfung (z. B. ob config.toml existiert)
import socket  
# Für Prüfung freier Ports per UDP-Socket
import toml        
#Modul zum Parsen von .toml-Dateien

#: @var KONFIGURATIONSDATEI
#: @brief Pfad zur standardmäßigen Konfigurationsdatei, wird großgeschrieben da Konstante 
KONFIGURATIONSDATEI = "config.toml"

def lade_config():
    """
    @brief lädt die TOML-Konfigurationsdatei und gibt sie als Dictionary zurück (Parsing).

    @return dict mit den Konfigurationswerten
    @raises FileNotFoundError wenn die Datei nicht existiert
    """
    if os.path.exists(KONFIGURATIONSDATEI):
       
        return toml.load(KONFIGURATIONSDATEI)
    else:
        raise FileNotFoundError("config.toml nicht gefunden.") 



def finde_freien_port(config):
    # config ist ein Dictionary mit Werten aus der config.toml.
    # config = lade_config muss erst in der main, also bei Aufruf der Funktion zugewisen werden.

    """
    @brief Durchsucht den in der Konfigurationsdatei angegebenen Portbereich nach einem freien UDP-Port.

    @param config dict mit den Konfigurationswerten, erwartet Schlüssel 'port_min' und 'port_max'
    @return int erster freier UDP-Port im Bereich
    @raises ValueError Wenn 'port_min' oder 'port_max' in der Konfiguration fehlen
    @raises RuntimeError wenn kein freier Port im Bereich gefunden wird
    """
    port_min = config["network"].get("port_min")
    port_max = config["network"].get("port_max")
#Holt die Konfigurationswerte port_min und port_max aus dem config-Dictionary.

    if port_min is None or port_max is None:
        raise ValueError("Konfigurationswerte 'port_min' und 'port_max' fehlen.")
#Fehlermeldung, falls einer der benötigten Ports in der Konfigurationsdatei fehlen.

    for port in range(port_min, port_max + 1):
#Schleife über alle Ports im Bereich.
#range(... + 1) ist notwendig, weil range die letzte Position nicht einbezieht.

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
#Erstellt einen Socket mit IPv4 (Adressfamilie= AF_INET) und UDP_Socket (Sockettyp= SOCK_DGRAM).
#with sorgt dafür, dass der Socket nach dem Block automatisch wieder geschlossen wird.
#Das ist wichtig, um Ports nicht versehentlich belegt zu lassen.

            try:
                sock.bind(("", port))
                return port
# Versucht, den Socket an einen bestimmten Port zu binden:

    #steht für „alle Netzwerk-Interfaces“ (z. B. localhost und LAN).
    #port ist der aktuell getestete Port.
    #Wenn das gelingt, ist der Port frei – also wird er sofort zurückgegeben.

            except OSError:
                continue
#Wenn der Bind-Vorgang fehlschlägt wird ein OSError ausgelöst und die Schleife wird fortgesetzt

    raise RuntimeError("Kein freier UDP-Port im Bereich {}–{} gefunden.".format(port_min, port_max))
# Wenn kein einziger Port im angegebenen Bereich verfügbar war, bricht die Funktion mit einem RuntimeError ab 



