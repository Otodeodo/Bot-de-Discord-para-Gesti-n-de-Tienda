import json
from datetime import datetime

from config import DATA_FILE

# Global ticket counter
TICKET_COUNTER = 0

def load_data():
    global TICKET_COUNTER
    default_data = {
        "users": {},
        "products": {},
        "tickets": {},
        "ticket_counter": 0,
        "payment_info": {
            "Transferencia": "CLABE: 123456789012345678 (Banco: Ejemplo)",
            "PayPal": "Correo: pagos@ejemplo.com",
            "Depósito Oxxo": "Número de cuenta: 9876543210 (Referencia: 12345)"
        },
        "gifts": {},
        "shop": {"last_updated": ""}
    }
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Ensure all keys exist
            for key in default_data:
                if key not in data:
                    data[key] = default_data[key]
            TICKET_COUNTER = data["ticket_counter"]
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return default_data

def save_data(data):
    global TICKET_COUNTER
    data["ticket_counter"] = TICKET_COUNTER
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)