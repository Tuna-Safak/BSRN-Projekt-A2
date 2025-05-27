#Argumente aus der Kommandozeile auslesen --handel
import sys
#für schönere eingabeauffordungen, muss zuerst installiert werden
import questionary
## @file interface.py
# @brief interface der Kommmandozeile für das Chat-Programm
# @details Menüauswahl und Eingaben über das Terminal

## Fragte eine Auswahl ab
# @return Auswahl des Benutzers als String
#wird in der main aufgerufen
def menue():
    print("\n===== Simple Chat CLI =====")
    print("1. Teilnehmer anzeigen")
    print("2. Nachricht senden")
    print("3. Bild senden")
    print("4. Autoreply aktivieren/deaktivieren")
    print("5. Konfiguration anzeigen/bearbeiten")
    print("6. Chat verlassen")
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
    '''if '--handle' in sys.argv:
        index = sys.argv.index('--handle') + 1
        if index < len(sys.argv):
            return sys.argv[index]'''
    return input("Bitte Benutzernamen eingeben: ")

## Eingabe der zu versendend Nachricht an eine bestimmten Empfänger
# @return 
def eingabe_nachricht():
    empfänger = input("Empfänger-Handle: ")
    nachricht = input("Nachricht: ")
    return empfänger, nachricht

## Eingabe des Bildpfads und des Empfängers
# @return 
def eingabe_bild():
    empfänger = input("Empfänger-Handle: ")
    bildpfad = input("Pfad zum Bild: ")
    return empfänger, bildpfad

## Eingabe der Autoreply Nachricht
# @return Die Config-Datei wird verändert
#gibt erst die aktuelle nachricht aus und fragt dann nach einer neuen
#nachricht in der Config einsehbar
def autoreply_umschalten(config):
    aktuell = config.get("autoreply", "")
    print(f"Aktueller Autoreply-Text: '{aktuell}'")
    neu = input("Neuer Autoreply-Text (leer für deaktivieren): ")
    config["autoreply"] = neu#greift auf die zeile autoreply in der config zu und ändert sie
    return config
