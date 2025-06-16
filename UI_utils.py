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
KONFIGURATIONSDATEI = "Konfigurationsdateien/config.toml"


def lade_config(pfad=None):
    """
    @brief lädt die TOML-Konfigurationsdatei und gibt sie als Dictionary zurück (Parsing).

    @return dict mit den Konfigurationswerten
    @raises FileNotFoundError wenn die Datei nicht existiert
    """
    if pfad is None:
        pfad = "Konfigurationsdateien/config.toml"

    if os.path.exists(pfad):
       
        return toml.load(pfad)
    else:
        raise FileNotFoundError("config.toml nicht gefunden.") 

def erstelle_neue_config(handle):
    """
    @brief Erstellt eine neue Konfigurationsdatei für den Benutzer, falls sie noch nicht existiert.
    
    @param handle: Der Benutzername für den die Konfiguration erstellt wird.
    """
    # Standard-Konfigurationswerte für den Benutzer
    config = {
        "client": {
            "name": handle,
            "autoreply": "",  # Standardwert für autoreply
            "autoreply_aktiv": False
        },
        "network": {
            "port_min": 5000,
            "port_max": 5100
        }
    }

    # Dateipfad für die neue Konfigurationsdatei
    konfig_pfad = f"Konfigurationsdateien/config_{handle.lower()}.toml"

    # Speichern der Konfigurationsdatei im TOML-Format
    with open(konfig_pfad, "w") as f:
        toml.dump(config, f)
    
    print(f"Neue Konfigurationsdatei für {handle} wurde erstellt.")   

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
    # Fehlermeldung, falls einer der benötigten Ports in der Konfigurationsdatei fehlen.

    for port in range(port_min, port_max + 1):
    # Schleife über alle Ports im Bereich.
    # range(... + 1) ist notwendig, weil range die letzte Position nicht einbezieht.

      try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Erstellt einen Socket mit IPv4 (Adressfamilie = AF_INET) und UDP (Sockettyp = SOCK_DGRAM).
        # Kein 'with', damit der Socket erhalten bleibt und der Port reserviert bleibt.

        sock.bind(("", port))
        # Versucht, den Socket an einen bestimmten Port zu binden:
        # "" steht für „alle Netzwerk-Interfaces“ (z. B. localhost und LAN).
        # port ist der aktuell getestete Port.
        # Wenn das gelingt, ist der Port frei – also wird er sofort zurückgegeben.

        return port, sock

      except OSError:
        continue
        # Wenn der Bind-Vorgang fehlschlägt, wird ein OSError ausgelöst und die Schleife wird fortgesetzt.

        


    raise RuntimeError("Kein freier UDP-Port im Bereich {}–{} gefunden.".format(port_min, port_max))
# Wenn kein einziger Port im angegebenen Bereich verfügbar war, bricht die Funktion mit einem RuntimeError ab 



