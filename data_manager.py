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
        "categories": {},  
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


def update_product_availability(product_id, is_available):
    """Actualiza la disponibilidad de un producto."""
    data = load_data()
    if product_id in data["products"]:
        data["products"][product_id]["available"] = is_available
        save_data(data)
        return True
    return False

def save_data(data):
    global TICKET_COUNTER
    data["ticket_counter"] = TICKET_COUNTER
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_category_by_id(category_id: str):
    """Obtiene una categoría por su ID."""
    data = load_data()
    return data['categories'].get(category_id)

def get_all_categories():
    """Obtiene todas las categorías."""
    data = load_data()
    return data['categories']

def add_category(name: str, description: str = "", icon: str = ""):
    """Añade una nueva categoría y retorna su ID."""
    data = load_data()
    category_id = str(len(data['categories']) + 1)
    
    data['categories'][category_id] = {
        "name": name,
        "description": description,
        "icon": icon,
        "created_at": datetime.utcnow().isoformat(),
        "products": []  # Lista de IDs de productos en esta categoría
    }
    
    save_data(data)
    return category_id

def update_category(category_id: str, name: str = None, description: str = None, icon: str = None):
    """Actualiza una categoría existente."""
    data = load_data()
    if category_id not in data['categories']:
        return False
        
    if name is not None:
        data['categories'][category_id]['name'] = name
    if description is not None:
        data['categories'][category_id]['description'] = description
    if icon is not None:
        data['categories'][category_id]['icon'] = icon
        
    save_data(data)
    return True

def delete_category(category_id: str):
    """Elimina una categoría y actualiza los productos asociados."""
    data = load_data()
    if category_id not in data['categories']:
        return False
        
    # Eliminar la categoría de todos los productos asociados
    for product_id in data['categories'][category_id]['products']:
        if product_id in data['products']:
            data['products'][product_id]['category_id'] = None
            
    del data['categories'][category_id]
    save_data(data)
    return True

def assign_product_to_category(product_id: str, category_id: str):
    """Asigna un producto a una categoría."""
    data = load_data()
    if product_id not in data['products'] or category_id not in data['categories']:
        return False
        
    # Remover el producto de su categoría actual si tiene una
    current_category_id = data['products'][product_id].get('category_id')
    if current_category_id and current_category_id in data['categories']:
        data['categories'][current_category_id]['products'].remove(product_id)
        
    # Asignar el producto a la nueva categoría
    data['products'][product_id]['category_id'] = category_id
    if product_id not in data['categories'][category_id]['products']:
        data['categories'][category_id]['products'].append(product_id)
        
    save_data(data)
    return True