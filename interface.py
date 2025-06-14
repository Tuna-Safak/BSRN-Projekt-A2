#Argumente aus der Kommandozeile auslesen --handel
import sys
import toml
## import questionary
## @file interface.py
# @brief interface der Kommmandozeile für das Chat-Programm
# @details Menüauswahl und Eingaben über das Terminal

## Fragte eine Auswahl ab
# @return Auswahl des Benutzers als String
#wird in der main aufgerufen
def menue():
    print("\nMenü\n")
    print("0. Join")
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
    benutzername=input("Bitte Benutzernamen eingeben: ")
    return benutzername

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
def autoreply_umschalten(config, handle):
    aktuell = config.get("client", {}).get("autoreply", "")#ließt den Wert von autoreply aus. Wenn er nicht vorhalen ist, kommt ein leerer
    print(f"Aktueller Autoreply-Text: '{aktuell}'")
    neu = input("Neuer Autoreply-Text (leer für deaktivieren): ")
    config["client"]["autoreply"] = neu #greift auf die zeile autoreply in der config zu und ändert sie
    pfad = f"Konfigurationsdateien/config_{handle}.toml"
    with open(pfad, "w") as f:
        toml.dump(config, f)
    return config
