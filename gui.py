import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import toml
import os
from main import sende_befehl_an_netzwerkprozess
from UI_utils import lade_config, erstelle_neue_config

FARBEN = {
    "eigene": "lightgreen",
    "fremd": "lightblue",
    "system": "lightgray",
    "fehler": "lightcoral"
}

class ChatGUI:
    def __init__(self, root, handle):
        self.root = root
        self.root.title(f"SLCP Chat - {handle}")
        self.handle = handle
        self.konfig_pfad = f"Konfigurationsdateien/config_{handle.lower()}.toml"
        self.config = lade_config(self.konfig_pfad)

        self.chatfenster = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', width=70, height=20)
        self.chatfenster.pack(padx=10, pady=10)

        for typ, farbe in FARBEN.items():
            self.chatfenster.tag_config(typ, background=farbe)

        self.empfaenger_var = tk.StringVar()
        self.empfaenger_entry = tk.Entry(root, textvariable=self.empfaenger_var, width=50)
        self.empfaenger_entry.insert(0, "Empfänger-Handle eingeben")
        self.empfaenger_entry.pack(padx=10, pady=(0, 5))

        self.nachricht_entry = tk.Entry(root, width=50)
        self.nachricht_entry.pack(padx=10, pady=(0, 10))
        self.nachricht_entry.bind("<Return>", self.nachricht_absenden)

        self.send_button = tk.Button(root, text="Nachricht senden", command=self.nachricht_absenden)
        self.send_button.pack()

        self.menu_frame = tk.Frame(root)
        self.menu_frame.pack(pady=10)

        tk.Button(self.menu_frame, text="0. Join", command=self.join_chat).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(self.menu_frame, text="1. Teilnehmer anzeigen", command=self.zeige_teilnehmer).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.menu_frame, text="2. Bild senden", command=self.bild_senden).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(self.menu_frame, text="3. Autoreply ändern", command=self.autoreply_aendern).grid(row=0, column=3, padx=5, pady=5)
        tk.Button(self.menu_frame, text="4. Konfiguration anzeigen", command=self.zeige_konfiguration).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        tk.Button(self.menu_frame, text="5. Chat verlassen", command=self.chat_verlassen).grid(row=1, column=2, columnspan=2, padx=5, pady=5)

        self.zeige_nachricht("GUI erfolgreich gestartet", "system")

    def zeige_nachricht(self, text, typ="fremd"):
        self.chatfenster.config(state='normal')
        self.chatfenster.insert(tk.END, text + "\n", typ)
        self.chatfenster.config(state='disabled')
        self.chatfenster.see(tk.END)

    def nachricht_absenden(self, event=None):
        empfaenger = self.empfaenger_var.get().strip()
        text = self.nachricht_entry.get().strip()
        if not empfaenger or not text:
            self.zeige_nachricht("Empfänger und Nachricht dürfen nicht leer sein.", "fehler")
            return
        befehl = f"MSG {empfaenger} {text}"
        try:
            sende_befehl_an_netzwerkprozess(befehl, tcp_port)
            self.zeige_nachricht(f"Du an {empfaenger}: {text}", "eigene")
            self.nachricht_entry.delete(0, tk.END)
        except Exception as e:
            self.zeige_nachricht(f"Fehler beim Senden: {e}", "fehler")

    def join_chat(self):
        port = self.config["client"]["port"]
        befehl = f"JOIN {self.handle} {port}"
        sende_befehl_an_netzwerkprozess(befehl, tcp_port)
        self.zeige_nachricht("JOIN gesendet.", "system")

    def zeige_teilnehmer(self):
        try:
            import socket
            with socket.create_connection(("localhost", 6001)) as sock:
                sock.sendall(b"WHO")
                antwort = sock.recv(4096).decode().strip()
                if antwort.startswith("KNOWNUSERS"):
                    teile = antwort.split(" ", 1)
                    if len(teile) == 2:
                        eintraege = teile[1].split(", ")
                        self.zeige_nachricht("Bekannte Nutzer:", "system")
                        for eintrag in eintraege:
                            self.zeige_nachricht(f"  {eintrag}", "system")
                else:
                    self.zeige_nachricht(f"Unerwartete Antwort: {antwort}", "fehler")
        except Exception as e:
            self.zeige_nachricht(f"Fehler bei WHO: {e}", "fehler")

    def bild_senden(self):
        empfaenger = self.empfaenger_var.get().strip()
        if not empfaenger:
            self.zeige_nachricht("Empfänger angeben!", "fehler")
            return
        pfad = filedialog.askopenfilename(title="Bild auswählen", filetypes=[("Bilddateien", "*.jpg *.png *.jpeg")])
        if pfad:
            befehl = f"IMG {empfaenger} {pfad}"
            try:
                sende_befehl_an_netzwerkprozess(befehl, tcp_port)
                self.zeige_nachricht(f"Bild an {empfaenger} gesendet.", "eigene")
            except Exception as e:
                self.zeige_nachricht(f"Fehler beim Bildversand: {e}", "fehler")

    def autoreply_aendern(self):
        neu = tk.simpledialog.askstring("Autoreply", "Neuer Autoreply-Text (leer für deaktivieren):")
        if neu is not None:
            self.config["client"]["autoreply"] = neu
            with open(self.konfig_pfad, "w") as f:
                toml.dump(self.config, f)
            self.zeige_nachricht("Autoreply aktualisiert.", "system")

    def zeige_konfiguration(self):
        self.zeige_nachricht("Aktuelle Konfiguration:", "system")
        for k, v in self.config.items():
            self.zeige_nachricht(f"{k}: {v}", "system")

    def chat_verlassen(self):
        befehl = f"LEAVE {self.handle}"
        sende_befehl_an_netzwerkprozess(befehl, tcp_port)
        self.zeige_nachricht("LEAVE gesendet. Fenster wird geschlossen.", "system")
        self.root.after(1000, self.root.destroy)

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        handle = sys.argv[1]
    else:
        handle = input("Bitte Benutzernamen eingeben: ")
        if not os.path.exists(f"Konfigurationsdateien/config_{handle.lower()}.toml"):
            erstelle_neue_config(handle)

    root = tk.Tk()
    app = ChatGUI(root, handle)
    root.mainloop()