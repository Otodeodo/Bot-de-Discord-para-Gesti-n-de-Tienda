import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from data_manager import load_data, save_data
from economy_system import economy

class VirtualShop:
    def __init__(self):
        self.categories = {
            "roles": {"name": "Roles", "emoji": "🎭"},
            "perks": {"name": "Beneficios", "emoji": "⭐"},
            "items": {"name": "Items", "emoji": "🎁"},
            "cosmetics": {"name": "Cosméticos", "emoji": "✨"},
            "other": {"name": "Otros", "emoji": "📦"}
        }
    
    def get_virtual_products(self) -> Dict:
        """Obtiene todos los productos virtuales"""
        data = load_data()
        if "virtual_shop" not in data:
            data["virtual_shop"] = {
                "products": {},
                "purchases": {},
                "settings": {"enabled": True, "tax_rate": 0.0}
            }
            save_data(data)
        
        products = data["virtual_shop"]["products"]
        
        # Verificar si products es una lista, convertir a diccionario
        if isinstance(products, list):
            products_dict = {str(i): product for i, product in enumerate(products)}
            data["virtual_shop"]["products"] = products_dict
            save_data(data)
            return products_dict
        elif not isinstance(products, dict):
            # Si no es ni lista ni diccionario, inicializar como diccionario vacío
            data["virtual_shop"]["products"] = {}
            save_data(data)
            return {}
        
        return products
    
    def add_virtual_product(self, name: str, price: int, description: str, 
                           category: str = "other", image_url: str = None,
                           role_id: str = None, duration_days: int = None) -> str:
        """Añade un producto virtual a la tienda"""
        data = load_data()
        
        if "virtual_shop" not in data:
            data["virtual_shop"] = {"products": {}, "purchases": {}, "settings": {"enabled": True, "tax_rate": 0.0}}
        
        product_id = str(uuid.uuid4())
        
        product_data = {
            "id": product_id,
            "name": name,
            "price": price,
            "description": description,
            "category": category,
            "image_url": image_url,
            "role_id": role_id,
            "duration_days": duration_days,
            "created_at": datetime.utcnow().isoformat(),
            "enabled": True,
            "purchases_count": 0
        }
        
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
            allowed_fields = ['name', 'price', 'description', 'category', 'image_url', 
                            'role_id', 'duration_days', 'enabled']
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    product[field] = value
            
            save_data(data)
            return True
        return False
    
    def purchase_virtual_product(self, user_id: str, product_id: str) -> Dict[str, Any]:
        """Procesa la compra de un producto virtual"""
        data = load_data()
        
        # Verificar que el producto existe
        if "virtual_shop" not in data or product_id not in data["virtual_shop"]["products"]:
            return {"success": False, "message": "Producto no encontrado"}
        
        product = data["virtual_shop"]["products"][product_id]
        
        # Verificar que el producto está habilitado
        if not product.get("enabled", True):
            return {"success": False, "message": "Producto no disponible"}
        
        # Verificar balance del usuario
        user_balance = economy.get_balance(user_id)
        if user_balance < product["price"]:
            return {
                "success": False, 
                "message": f"Saldo insuficiente. Necesitas {product['price']:,} GameCoins, tienes {user_balance:,}"
            }
        
        # Procesar la compra
        try:
            # Deducir GameCoins
            economy.remove_coins(user_id, product["price"])
            
            # Registrar la compra
            purchase_id = str(uuid.uuid4())
            purchase_data = {
                "id": purchase_id,
                "user_id": user_id,
                "product_id": product_id,
                "product_name": product["name"],
                "price_paid": product["price"],
                "purchased_at": datetime.utcnow().isoformat(),
                "active": True
            }
            
            if "purchases" not in data["virtual_shop"]:
                data["virtual_shop"]["purchases"] = {}
            data["virtual_shop"]["purchases"][purchase_id] = purchase_data
            
            # Incrementar contador de compras del producto
            data["virtual_shop"]["products"][product_id]["purchases_count"] += 1
            
            save_data(data)
            
            return {
                "success": True,
                "message": f"¡Compra exitosa! Has adquirido **{product['name']}**",
                "purchase_id": purchase_id,
                "product": product
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error al procesar la compra: {str(e)}"}
    
    def get_user_purchases(self, user_id: str) -> List[Dict]:
        """Obtiene las compras de un usuario"""
        data = load_data()
        
        if "virtual_shop" not in data or "purchases" not in data["virtual_shop"]:
            return []
        
        purchases = data["virtual_shop"]["purchases"]
        
        # Verificar si purchases es una lista, convertir a diccionario
        if isinstance(purchases, list):
            purchases_dict = {str(i): purchase for i, purchase in enumerate(purchases)}
            data["virtual_shop"]["purchases"] = purchases_dict
            save_data(data)
            purchases = purchases_dict
        elif not isinstance(purchases, dict):
            return []
        
        user_purchases = []
        for purchase_id, purchase in purchases.items():
            if isinstance(purchase, dict) and purchase.get("user_id") == user_id and purchase.get("active", True):
                user_purchases.append(purchase)
        
        return sorted(user_purchases, key=lambda x: x.get("purchased_at", ""), reverse=True)
    
    def deactivate_purchase(self, purchase_id: str) -> bool:
        """Desactiva una compra (para productos temporales)"""
        data = load_data()
        
        if "virtual_shop" in data and "purchases" in data["virtual_shop"] and purchase_id in data["virtual_shop"]["purchases"]:
            data["virtual_shop"]["purchases"][purchase_id]["active"] = False
            save_data(data)
            return True
        return False
    
    def get_products_by_category(self) -> Dict[str, List[Dict]]:
        """Organiza productos por categoría"""
        products = self.get_virtual_products()
        categorized = {cat: [] for cat in self.categories.keys()}
        
        for product_id, product in products.items():
            if product.get("enabled", True):
                category = product.get("category", "other")
                if category not in categorized:
                    category = "other"
                categorized[category].append(product)
        
        return categorized
    
    def get_shop_stats(self) -> Dict:
        """Obtiene estadísticas de la tienda virtual"""
        data = load_data()
        if "virtual_shop" not in data:
            return {"total_products": 0, "total_purchases": 0, "total_revenue": 0, "enabled_products": 0}
        
        products = data["virtual_shop"].get("products", {})
        purchases = data["virtual_shop"].get("purchases", {})
        
        # Verificar si purchases es un diccionario, si no, convertirlo
        if isinstance(purchases, list):
            # Si es una lista, convertir a diccionario usando índices
            purchases = {str(i): purchase for i, purchase in enumerate(purchases)}
        elif not isinstance(purchases, dict):
            purchases = {}
        
        # Verificar si products es un diccionario
        if isinstance(products, list):
            products = {str(i): product for i, product in enumerate(products)}
        elif not isinstance(products, dict):
            products = {}
        
        total_revenue = sum(purchase["price_paid"] for purchase in purchases.values() if isinstance(purchase, dict) and purchase.get("active", True))
        active_purchases = len([p for p in purchases.values() if isinstance(p, dict) and p.get("active", True)])
        
        return {
            "total_products": len(products),
            "total_purchases": active_purchases,
            "total_revenue": total_revenue,
            "enabled_products": len([p for p in products.values() if isinstance(p, dict) and p.get("enabled", True)])
        }

# Instancia global de la tienda virtual
virtual_shop = VirtualShop()