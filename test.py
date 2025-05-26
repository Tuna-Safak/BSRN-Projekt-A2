import questionary

wahl = questionary.select(
    "Was möchtest du tun?",
    choices=[
        "Nachricht senden",
        "Bild senden",
        "Autoreply ändern",
        "Beenden"
    ]
).ask()

print("Du hast gewählt:", wahl)