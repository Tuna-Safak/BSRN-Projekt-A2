"""
@file UI_utils.py
@brief lädt eine TOML-Konfigurationsdatei und stellt sie als Dictionary bereit.
"""
import os          
#Für Datei- und Pfadprüfung (z. B. ob config.toml existiert)
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
