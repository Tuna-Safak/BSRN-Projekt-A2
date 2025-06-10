# Benutzername abfragen
benutzername = input("Wie heißt du? ")

# Dateipfad zusammenbauen
konfig_pfad = f"Konfigurationsdateien/config_{benutzername.lower()}.toml"


# Debug-Ausgabe zur Kontrolle
print(f"[INFO] Konfiguration geladen aus: {konfig_pfad}")