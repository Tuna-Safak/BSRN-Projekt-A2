## @file nutzerliste.py
# @brief Verwaltung der gemeinsam genutzten Nutzerliste im SLCP-Chatprojekt.
# @details es wird eine nutzerliste gespeichert, die vom Discovery und netzwerkprozess bearbeitet wird.

# --------Nutzerliste--------
_shared_dict = None # Globale Variable für die geteilte Nutzerliste

## @brief Erstellt die globale Nutzerliste mit einem gemeinsam nutzbaren Dictionary.
# @param shared_dict--> wird von multiprocessing.Manager() erzeugte
def initialisiere_nutzerliste(shared_dict):
    global _shared_dict
    _shared_dict = shared_dict

## @brief gibt nutzerliste zurück
# @return nutzerliste
def gebe_nutzerliste_zurück():
    return _shared_dict
