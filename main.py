## @file main.py
#  @brief Start des Programms

## Importiert Methoden aus dem interface.py
from interface import (
    menue,
    nutzernamen_abfragen,
    eingabe_nachricht,
    eingabe_bild,
    autoreply_umschalten
)

## Importiert Methoden aus dem UI_utils.py
from UI_utils import lade_config, finde_freien_port, registriere_neuen_nutzer
 
## Hauptfunktion
#  @brief ruft funktionen aus den importierten Datei auf
#  @details lädt das Menü und verwaltet den Ablauf
def main():
    config = lade_config()
    handle = nutzernamen_abfragen()
    port = finde_freien_port(config)
    registriere_neuen_nutzer(handle, port)
    
    print(f"Willkommen, {handle}! Dein Port: {port}")

    while True:
        wahl = menue()

        if wahl == "1":
            print("→ WHO wird gesendet ...")
            # hier später Netzwerkfunktion einbinden
        elif wahl == "2":
            empfänger, text = eingabe_nachricht()
            print(f"→ MSG an {empfänger}: {text}")
            # hier später Nachricht senden
        elif wahl == "3":
            empfänger, pfad = eingabe_bild()
            print(f"→ Bild wird an {empfänger} gesendet: {pfad}")
            # hier später Bildversand einbinden
        elif wahl == "4":
            config = autoreply_umschalten(config)
            print("→ Autoreply aktualisiert.")
        elif wahl == "5":
            print("→ Aktuelle Konfiguration:")
            for k, v in config.items():
                print(f"  {k}: {v}")
        elif wahl == "6":
            print(f"→ LEAVE {handle}")
            break
        else:
            print("Ungültige Eingabe. Bitte erneut versuchen.")

## beginnt das Programm
#  @note Beim starten wird name durch main ersetzt, erst wenn es stimmt, wird die Main Funktion gestartet
if __name__ == "__main__":
    main()
