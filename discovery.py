import socket

# socket erstellen
# variable namens 'sock', datentyp socket
# socket.socket() = socket = modul/package, socket() = funktion/klasse
# socket.AF_INET, socket.SOCK_DGRAM = argumente/parameter
# socket.AF_INET = Netzwerk-Typ: IPv4
# socket.SOCK_DGRAM	= UDP-Socket statt TCP

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# sock.setsockopt = option/einstellung setzen fuer socket
# SOL_SOCKET = option gilt nur auf Socket-Ebene (nicht zB für TCP selbst) -> (SOL = Socket Option Level)
# socket.SO_BROADCAST = erlaube Senden/Empfangen von Broadcasts
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# socket.SO_REUSEADDR = erlaube Wiederverwendung einer Port-Adresse
# 1 = aktivieren (True / Ja)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)



