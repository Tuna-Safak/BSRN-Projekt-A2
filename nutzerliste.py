_shared_dict = None

def initialisiere_nutzerliste(shared_dict):
    global _shared_dict
    _shared_dict = shared_dict

def gebe_nutzerliste_zurück():
    return _shared_dict
