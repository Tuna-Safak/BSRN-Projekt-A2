## @file main.py
##  @brief Start des Programms

## Importiert Methoden aus dem interface.py
import threading
## Importiert Methoden aus dem interface.py
from interface import (
    menue,
    nutzernamen_abfragen,
    eingabe_nachricht,
    eingabe_bild,
    autoreply_umschalten
)

## Importiert Methoden aus dem UI_utils.py, discovery und message_handler
from discovery import sende_join, sende_leave, sende_who,nutzerspeichern, zeige_bekannte_nutzer
from UI_utils import lade_config, finde_freien_port
from message_handler import send_who, send_join, send_leave, sendMSG, sendIMG, receive_MSG, get_socket


sock = get_socket()

config = lade_config()

threading.Thread(target=receive_MSG, args=(sock, config), daemon=True).start()


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
    threading.Thread(target=nutzerspeichern, daemon=True).start()
    
    print(f"Willkommen, {handle}! Dein Port: {port}")

    while True:
        ## aufrufen der Main methode
        #kommt aus dem interface
        auswahl = menue()

        if auswahl == "1":
            print("→ WHO wird gesendet ...")
            # hier später Netzwerkfunktion einbinden
            send_who()
            continue
        elif auswahl == "2":
            empfaenger, text = eingabe_nachricht()
            print(f"→ MSG an {empfaenger}: {text}")
            sendMSG(sock, handle, empfaenger, text)
            continue
        elif auswahl == "3":
        #    empfaenger, pfad = eingabe_bild()
        #    print(f"→ Bild wird an {empfaenger} gesendet: {pfad}")
            # hier später Bildversand einbinden
            sendIMG(handle, empfaenger, pfad)
            continue
        elif auswahl == "4":
            config = autoreply_umschalten(config)
            print("→ Autoreply aktualisiert.")
            continue
        elif auswahl == "5":
            print("→ Aktuelle Konfiguration:")
            for k, v in config.items():
                print(f"  {k}: {v}")
            continue    
        elif auswahl == "6":
            print(f"→ LEAVE {handle}")
            break
            
       

## beginnt das Programm
#  @note Beim starten wird name durch main ersetzt, erst wenn es stimmt, wird die Main Funktion gestartet
if __name__ == "__main__":
    main()