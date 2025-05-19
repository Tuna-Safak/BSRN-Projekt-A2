from interface import (
    menue,
    nutzernamen_abfragen,
    eingabe_nachricht,
    eingabe_bild,
    autoreply_umschalten
)

from UI_utils import lade_config, finde_freien_port#, registriere_neuen_nutzer

def main():
    config = lade_config()
    handle = nutzernamen_abfragen()
    port = finde_freien_port()
    registriere_neuen_nutzer(handle, port)

    print(f"Willkommen, {handle}! Dein Port: {port}")

    while True:
        wahl = zeige_menü()

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

if __name__ == "__main__":
    main()
