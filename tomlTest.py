import toml

config = toml.load("config.toml")

network_cfg = config.get("network")
if network_cfg is None:
    raise ValueError("Abschnitt [network] fehlt in config.toml")

port_min = network_cfg.get("port_min")
if port_min is None:
    raise ValueError("port_min fehlt im Abschnitt [network]")

print(f"Port-Min: {port_min}")
