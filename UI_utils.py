import os          # Für Datei- und Pfadprüfung (z. B. ob config.toml existiert)
import toml        # Für das Lesen und Schreiben von TOML-Dateien


#: @var KONFIGURATIONSDATEI
#: @brief Pfad zur standardmäßigen Konfigurationsdatei, wird großgeschrieben da Konstante 
KONFIGURATIONSDATEI = "config.toml"

# Definiert eine Funktion zum Laden der Konfigurationsdatei
# Gibt den Inhalt als Python-Dictionary zurück

def lade_config():
    # Prüft, ob die Datei config.toml im aktuellen Verzeichnis existiert
    if os.path.exists(KONFIGURATIONSDATEI):
      
        """
    Lädt die TOML-Konfigurationsdatei und gibt sie als Dictionary zurück

    @brief Liest die Datei 'config.toml' ein und parst sie
    @return dict mit den Konfigurationswerten
    @raises FileNotFoundError wenn die Datei nicht existiert
    """
        return toml.load(KONFIGURATIONSDATEI)
    else:
        # Falls die Datei nicht existiert wird ein Fehler ausgelöst
        raise FileNotFoundError("config.toml nicht gefunden.")
