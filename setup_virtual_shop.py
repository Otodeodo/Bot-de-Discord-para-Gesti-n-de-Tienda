#!/usr/bin/env python3
"""
Script para configurar productos iniciales en la tienda virtual
Ejecuta este script una vez para añadir productos de ejemplo
"""

from virtual_shop import virtual_shop
from data_manager import load_data, save_data

def setup_initial_products():
    """Configura productos iniciales para la tienda virtual"""
    
    print("🛒 Configurando tienda virtual con productos de ejemplo...")
    
    # Productos de ejemplo para cada categoría
    example_products = [
        # Roles Especiales
        {
            "name": "🌟 VIP Dorado",
            "price": 5000,
            "description": "Rol VIP exclusivo con color dorado y beneficios especiales",
            "category": "roles",
            "role_id": None  # Debes configurar esto con un ID de rol real
        },
        {
            "name": "💎 Miembro Premium",
            "price": 3000,
            "description": "Acceso a canales premium y funciones exclusivas",
            "category": "roles",
            "role_id": None
        },
        {
            "name": "🎮 Gamer Pro",
            "price": 2000,
            "description": "Rol especial para gamers dedicados con beneficios únicos",
            "category": "roles",
            "role_id": None
        },
        
        # Beneficios
        {
            "name": "🚀 Boost de XP (7 días)",
            "price": 1500,
            "description": "Duplica la ganancia de XP por 7 días",
            "category": "perks",
            "duration_days": 7,
            "multiplier": 2.0
        },
        {
            "name": "💰 Boost de GameCoins (3 días)",
            "price": 1000,
            "description": "Aumenta la ganancia de GameCoins en un 50% por 3 días",
            "category": "perks",
            "duration_days": 3,
            "multiplier": 1.5
        },
        {
            "name": "🎯 Suerte en Minijuegos (24h)",
            "price": 800,
            "description": "Aumenta las probabilidades de ganar en minijuegos por 24 horas",
            "category": "perks",
            "duration_days": 1,
            "multiplier": 1.3
        },
        
        # Cosméticos
        {
            "name": "🎨 Color de Nombre Personalizado",
            "price": 2500,
            "description": "Cambia el color de tu nombre en el servidor (permanente)",
            "category": "cosmetics"
        },
        {
            "name": "✨ Efecto de Brillo",
            "price": 1800,
            "description": "Añade un efecto de brillo especial a tu perfil",
            "category": "cosmetics"
        },
        {
            "name": "🏆 Insignia de Coleccionista",
            "price": 3500,
            "description": "Insignia exclusiva que muestra tu dedicación al servidor",
            "category": "cosmetics"
        },
        
        # Potenciadores
        {
            "name": "⚡ Mega Boost (30 días)",
            "price": 8000,
            "description": "Triplica todas las ganancias por 30 días completos",
            "category": "boosters",
            "duration_days": 30,
            "multiplier": 3.0
        },
        {
            "name": "🔥 Racha de Suerte (7 días)",
            "price": 4000,
            "description": "Aumenta significativamente la suerte en todos los juegos",
            "category": "boosters",
            "duration_days": 7,
            "multiplier": 2.5
        },
        {
            "name": "💫 Boost Diario Extendido",
            "price": 1200,
            "description": "Permite reclamar el bono diario dos veces por día durante 3 días",
            "category": "boosters",
            "duration_days": 3,
            "multiplier": 2.0
        }
    ]
    
    # Añadir productos a la tienda
    added_count = 0
    for product in example_products:
        try:
            product_id = virtual_shop.add_virtual_product(
                name=product["name"],
                price=product["price"],
                description=product["description"],
                category=product["category"],
                role_id=product.get("role_id"),
                duration_days=product.get("duration_days"),
                multiplier=product.get("multiplier")
            )
            print(f"✅ Añadido: {product['name']} (ID: {product_id[:8]}...)")
            added_count += 1
        except Exception as e:
            print(f"❌ Error añadiendo {product['name']}: {str(e)}")
    
    print(f"\n🎉 ¡Configuración completada! Se añadieron {added_count} productos a la tienda virtual.")
    print("\n📝 Notas importantes:")
    print("- Los productos de roles necesitan IDs de roles reales para funcionar completamente")
    print("- Puedes editar, eliminar o añadir más productos usando los comandos de owner")
    print("- Los usuarios pueden acceder a la tienda con el comando /tienda")
    
    # Mostrar estadísticas
    stats = virtual_shop.get_shop_stats()
    print(f"\n📊 Estadísticas de la tienda:")
    print(f"- Total de productos: {stats['total_products']}")
    print(f"- Productos activos: {stats['active_products']}")
    print(f"- Compras realizadas: {stats['total_purchases']}")
    print(f"- Ingresos totales: {stats['total_revenue']:,} GameCoins")

def show_categories():
    """Muestra las categorías disponibles"""
    print("\n📂 Categorías disponibles en la tienda virtual:")
    for category_id, category_info in virtual_shop.categories.items():
        print(f"- {category_info['emoji']} {category_info['name']}: {category_info['description']}")

if __name__ == "__main__":
    print("🛒 Configurador de Tienda Virtual GameCoins")
    print("=" * 50)
    
    # Verificar si ya hay productos
    existing_products = virtual_shop.get_virtual_products()
    if existing_products:
        print(f"⚠️  Ya existen {len(existing_products)} productos en la tienda.")
        response = input("¿Quieres añadir más productos de ejemplo? (s/n): ")
        if response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada.")
            exit()
    
    show_categories()
    setup_initial_products()
    
    print("\n🚀 ¡La tienda virtual está lista para usar!")
    print("Comandos disponibles:")
    print("- /tienda - Abrir la tienda virtual (usuarios)")
    print("- /añadir_producto_virtual - Añadir productos (owners)")
    print("- /editar_producto_virtual - Editar productos (owners)")
    print("- /eliminar_producto_virtual - Eliminar productos (owners)")
    print("- /listar_productos_virtuales - Ver todos los productos (owners)")