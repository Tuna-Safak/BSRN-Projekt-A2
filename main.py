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

from UI_utils import lade_config, finde_freien_port
from message_handler import send_who, send_join, send_leave, sendMSG, sendIMG, receive_MSG


from UI_utils import (
    lade_config,
    finde_freien_port
)
## Importiert Methoden aus dem message_handler
from message_handler import (
    send_join,
    send_leave,
    sendMSG,
    sendIMG
)

#registriere_neuen_nutzer
def registriere_neuen_nutzer(handle, port):
    send_join(handle, port)

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
        auswahl = menue()

        if auswahl == "Teilnehmer anzeigen":
            print("→ WHO wird gesendet ...")
            # hier später Netzwerkfunktion einbinden
            send_who()
        elif wahl == "2":
            empfaenger, text = eingabe_nachricht()
            print(f"→ MSG an {empfaenger}: {text}")
            # hier später Nachricht senden
            sendMSG(handle)
        elif wahl == "3":
            empfaenger, pfad = eingabe_bild()

        elif auswahl == "Nachricht senden":
            empfänger, text = eingabe_nachricht()
            print(f"→ MSG an {empfänger}: {text}")
            # hier später Nachricht senden
            sendMSG(handle, empfaenger, text)
        elif auswahl == "Bild senden":
            empfänger, pfad = eingabe_bild()
            print(f"→ Bild wird an {empfänger} gesendet: {pfad}")
            # hier später Bildversand einbinden
            sendIMG(handle, empfaenger, pfad)
        elif auswahl == "Autoreply ändern":
            config = autoreply_umschalten(config)
            print("→ Autoreply aktualisiert.")
        elif auswahl == "Konfiguration":
            print("→ Aktuelle Konfiguration:")
            for k, v in config.items():
                print(f"  {k}: {v}")
        elif auswahl == "Beenden":
            print(f"→ LEAVE {handle}")
            break
        else:
            print("Ungültige Eingabe. Bitte erneut versuchen.")

## beginnt das Programm
#  @note Beim starten wird name durch main ersetzt, erst wenn es stimmt, wird die Main Funktion gestartet
if __name__ == "__main__":
    main()
