# nutzerliste.py
# Gemeinsame Nutzerliste für alle Module (Discovery, Netzwerkprozess, etc.)

known_users = {}  # zentrales Dictionary

def gebe_nutzerliste_zurück():
    return known_users