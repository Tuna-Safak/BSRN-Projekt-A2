#Argumente aus der Kommandozeile auslesen --handel
import sys
import toml
import os
from UI_utils import erstelle_neue_config
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
    
    
'''wahl= questionary.select(
    "Was möchtest du tun?",
    choices=[
        "Teilnehmer anzeigen",
        "Nachricht senden",
        "Bild senden",
        "Autoreply ändern",
        "Konfiguration",
        "Beenden"
    ]
).ask()

print("Du hast gewählt:", wahl)'''

## Eingabe des Benutzernames
# @return Benutzername (Handle) als String
def nutzernamen_abfragen():
    """
    Fragt den Benutzernamen ab und erstellt bei Bedarf eine neue Konfigurationsdatei.
    
    @return Der Benutzername
    """
    # Prüfen, ob das Argument '--handle' in der Kommandozeile übergeben wurde
    if '--handle' in sys.argv:
        index = sys.argv.index('--handle') + 1
        if index < len(sys.argv):
            handle = sys.argv[index]
        else:
            print("Fehler: Der Parameter '--handle' wurde ohne Wert angegeben.")
            sys.exit(1)
    else:
        # Wenn kein '--handle' Argument vorhanden ist, Benutzernamen interaktiv abfragen
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

