import discord
from discord import app_commands
from typing import Dict, List, Optional, Tuple
from data_manager import load_data, save_data
from economy_system import economy
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class VirtualShop:
    def __init__(self):
        pass
    
    def get_virtual_products(self) -> Dict:
        """Obtiene todos los productos virtuales"""
        data = load_data()
        if "virtual_shop" not in data:
            data["virtual_shop"] = {
                "products": {},
                "purchases": {},
                "settings": {
                    "enabled": True,
                    "tax_rate": 0.0
                }
            }
            save_data(data)
        return data["virtual_shop"]["products"]
    
    def add_virtual_product(self, name: str, price: int, description: str, 
                          role_id: Optional[str] = None, duration_days: Optional[int] = None,
                          multiplier: Optional[float] = None) -> str:
        """Añade un producto virtual a la tienda"""
        data = load_data()
        if "virtual_shop" not in data:
            data["virtual_shop"] = {"products": {}, "purchases": {}, "settings": {"enabled": True, "tax_rate": 0.0}}
        
        product_id = str(uuid.uuid4())
        product_data = {
            "name": name,
            "price": price,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "enabled": True,
            "purchases_count": 0
        }
        
        # Añadir campos específicos según el tipo de producto
        if role_id:
            product_data["role_id"] = role_id
            product_data["category"] = "roles"
        if duration_days:
            product_data["duration_days"] = duration_days
        if multiplier:
            product_data["multiplier"] = multiplier
            if not product_data.get("category"):
                product_data["category"] = "multipliers"
        
        # Si no se ha asignado categoría, usar "other"
        if "category" not in product_data:
            product_data["category"] = "other"
        
        data["virtual_shop"]["products"][product_id] = product_data
        save_data(data)
        return product_id
    
    def remove_virtual_product(self, product_id: str) -> bool:
        """Elimina un producto virtual"""
        data = load_data()
        if "virtual_shop" in data and product_id in data["virtual_shop"]["products"]:
            del data["virtual_shop"]["products"][product_id]
            save_data(data)
            return True
        return False
    
    def edit_virtual_product(self, product_id: str, **kwargs) -> bool:
        """Edita un producto virtual"""
        data = load_data()
        if "virtual_shop" in data and product_id in data["virtual_shop"]["products"]:
            product = data["virtual_shop"]["products"][product_id]
            
            # Actualizar campos permitidos
            allowed_fields = ["name", "price", "description", "enabled", 
                            "role_id", "duration_days", "multiplier"]
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    product[field] = value
            
            product["updated_at"] = datetime.now().isoformat()
            save_data(data)
            return True
        return False
    
    def purchase_virtual_product(self, user_id: str, product_id: str) -> Dict:
        """Compra un producto virtual"""
        data = load_data()
        
        # Verificar que el producto existe
        if "virtual_shop" not in data or product_id not in data["virtual_shop"]["products"]:
            return {"success": False, "error": "Producto no encontrado"}
        
        product = data["virtual_shop"]["products"][product_id]
        
        # Verificar que el producto está habilitado
        if not product.get("enabled", True):
            return {"success": False, "error": "Producto no disponible"}
        
        # Verificar que el usuario tiene suficientes GameCoins
        user_economy = economy.get_user_economy(user_id)
        price = product["price"]
        
        if user_economy["coins"] < price:
            return {
                "success": False, 
                "error": f"GameCoins insuficientes. Necesitas {price} GameCoins, tienes {user_economy['coins']}"
            }
        
        # Verificar si ya tiene el producto (para roles permanentes)
        # Determinar categoría basada en los campos del producto
        product_category = product.get("category")
        if not product_category:
            if product.get("role_id"):
                product_category = "roles"
            elif product.get("multiplier"):
                product_category = "multipliers"
            else:
                product_category = "other"
        
        if product_category == "roles" and not product.get("duration_days"):
            user_purchases = self.get_user_purchases(user_id)
            for purchase in user_purchases:
                if purchase["product_id"] == product_id and purchase.get("active", True):
                    return {"success": False, "error": "Ya posees este producto"}
        
        # Realizar la compra
        if economy.remove_coins(user_id, price, f"Compra: {product['name']}"):
            # Registrar la compra
            purchase_id = str(uuid.uuid4())
            purchase_data = {
                "user_id": user_id,
                "product_id": product_id,
                "product_name": product["name"],
                "price_paid": price,
                "purchased_at": datetime.now().isoformat(),
                "active": True
            }
            
            # Añadir fecha de expiración si es temporal
            if product.get("duration_days"):
                from datetime import timedelta
                expiry_date = datetime.now() + timedelta(days=product["duration_days"])
                purchase_data["expires_at"] = expiry_date.isoformat()
            
            # Guardar la compra
            if "purchases" not in data["virtual_shop"]:
                data["virtual_shop"]["purchases"] = {}
            data["virtual_shop"]["purchases"][purchase_id] = purchase_data
            
            # Incrementar contador de compras del producto
            data["virtual_shop"]["products"][product_id]["purchases_count"] += 1
            
            save_data(data)
            
            # Obtener balance actualizado directamente de datos frescos
            fresh_data = load_data()
            new_balance = fresh_data["economy"]["users"][user_id]["coins"]
            
            return {
                "success": True,
                "purchase_id": purchase_id,
                "product": product,
                "new_balance": new_balance
            }
        
        return {"success": False, "error": "Error al procesar el pago"}
    
    def get_user_purchases(self, user_id: str) -> List[Dict]:
        """Obtiene todas las compras de un usuario"""
        data = load_data()
        if "virtual_shop" not in data or "purchases" not in data["virtual_shop"]:
            return []
        
        user_purchases = []
        for purchase_id, purchase in data["virtual_shop"]["purchases"].items():
            if purchase["user_id"] == user_id:
                purchase_copy = purchase.copy()
                purchase_copy["purchase_id"] = purchase_id
                
                # Verificar si el producto temporal ha expirado
                if "expires_at" in purchase:
                    expiry_date = datetime.fromisoformat(purchase["expires_at"])
                    if datetime.now() > expiry_date:
                        purchase_copy["active"] = False
                        # Actualizar en la base de datos
                        data["virtual_shop"]["purchases"][purchase_id]["active"] = False
                        save_data(data)
                
                user_purchases.append(purchase_copy)
        
        return user_purchases
    
    def get_products_by_category(self, category: str = None) -> List[Tuple[str, Dict]]:
        """Obtiene todos los productos habilitados"""
        products = self.get_virtual_products()
        filtered_products = []
        
        for product_id, product in products.items():
            if product.get("enabled", True):
                filtered_products.append((product_id, product))
        
        # Ordenar por precio
        filtered_products.sort(key=lambda x: x[1]["price"])
        return filtered_products
    
    def get_shop_stats(self) -> Dict:
        """Obtiene estadísticas de la tienda virtual"""
        data = load_data()
        if "virtual_shop" not in data:
            return {"total_products": 0, "total_purchases": 0, "total_revenue": 0}
        
        products = data["virtual_shop"].get("products", {})
        purchases = data["virtual_shop"].get("purchases", {})
        
        total_revenue = sum(purchase["price_paid"] for purchase in purchases.values())
        active_products = sum(1 for product in products.values() if product.get("enabled", True))
        
        return {
            "total_products": len(products),
            "active_products": active_products,
            "total_purchases": len(purchases),
            "total_revenue": total_revenue
        }

# Instancia global de la tienda virtual
virtual_shop = VirtualShop()