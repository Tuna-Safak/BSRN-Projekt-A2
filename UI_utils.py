import os          # Für Datei- und Pfadprüfung (z. B. ob config.toml existiert)
import toml        # Für das Lesen und Schreiben von TOML-Dateien

# Wird großgeschrieben, da es sich um eine Konstante handelt (nicht zur Laufzeit änderbar)
# Diese Variable enthält den Pfad zur Konfigurationsdatei
KONFIGURATIONSDATEI = "config.toml"

# Definiert eine Funktion zum Laden der Konfigurationsdatei
# Gibt den Inhalt als Python-Dictionary zurück
def lade_config():
    # Prüft, ob die Datei config.toml im aktuellen Verzeichnis existiert
    if os.path.exists(KONFIGURATIONSDATEI):
        # Falls sie existiert wird sie mit toml.load() eingelesen
        # Der Inhalt (TOML-Text) wird in ein Python-Objekt umgewandelt
        return toml.load(KONFIGURATIONSDATEI)
    else:
        # Falls die Datei nicht existiert wird ein Fehler ausgelöst
        raise FileNotFoundError("config.toml nicht gefunden.")
