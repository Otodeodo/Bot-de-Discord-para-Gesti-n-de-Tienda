import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from data_manager import load_data
from virtual_shop import virtual_shop
from views.virtual_shop_view import VirtualShopView
from config import OWNER_ROLE_ID
import logging

logger = logging.getLogger(__name__)

def is_owner(interaction: discord.Interaction) -> bool:
    """Verifica si el usuario es owner"""
    return any(role.id == OWNER_ROLE_ID for role in interaction.user.roles)

def setup(tree: app_commands.CommandTree, client: discord.Client):
    

    
    @tree.command(name="añadir_producto_virtual", description="[OWNER] Añade un producto virtual a la tienda")
    @app_commands.describe(
        nombre="Nombre del producto",
        precio="Precio en GameCoins",
        descripcion="Descripción del producto",
        rol_id="ID del rol (opcional)",
        duracion_dias="Duración en días (opcional)",
        multiplicador="Multiplicador (opcional)"
    )
    async def add_virtual_product(interaction: discord.Interaction,
                                nombre: str,
                                precio: int,
                                descripcion: str,
                                rol_id: Optional[str] = None,
                                duracion_dias: Optional[int] = None,
                                multiplicador: Optional[float] = None):
        """Añade un producto virtual a la tienda"""
        if not is_owner(interaction):
            await interaction.response.send_message("❌ Solo los owners pueden usar este comando.", ephemeral=True)
            return
        
        try:
            # Validaciones
            if precio <= 0:
                await interaction.response.send_message("❌ El precio debe ser mayor a 0.", ephemeral=True)
                return
            

            
            if duracion_dias is not None and duracion_dias <= 0:
                await interaction.response.send_message("❌ La duración debe ser mayor a 0 días.", ephemeral=True)
                return
            
            if multiplicador is not None and multiplicador <= 0:
                await interaction.response.send_message("❌ El multiplicador debe ser mayor a 0.", ephemeral=True)
                return
            
            # Verificar que el rol existe si se especifica
            if rol_id:
                try:
                    role = interaction.guild.get_role(int(rol_id))
                    if not role:
                        await interaction.response.send_message("❌ El rol especificado no existe.", ephemeral=True)
                        return
                except ValueError:
                    await interaction.response.send_message("❌ ID de rol inválido.", ephemeral=True)
                    return
            
            # Añadir el producto
            product_id = virtual_shop.add_virtual_product(
                name=nombre,
                price=precio,
                description=descripcion,
                role_id=rol_id,
                duration_days=duracion_dias,
                multiplier=multiplicador
            )
            
            # Crear embed de confirmación
            embed = discord.Embed(
                title="✅ Producto Virtual Añadido",
                description=f"El producto **{nombre}** ha sido añadido exitosamente a la tienda virtual.",
                color=0x00ff88
            )
            
            embed.add_field(name="🏷️ Nombre", value=nombre, inline=True)
            embed.add_field(name="💰 Precio", value=f"{precio:,} GameCoins", inline=True)
            embed.add_field(name="📝 Descripción", value=descripcion, inline=False)
            embed.add_field(name="🔑 ID del Producto", value=f"`{product_id}`", inline=False)
            
            if rol_id:
                embed.add_field(name="🎭 Rol", value=f"<@&{rol_id}>", inline=True)
            if duracion_dias:
                embed.add_field(name="⏰ Duración", value=f"{duracion_dias} días", inline=True)
            if multiplicador:
                embed.add_field(name="🚀 Multiplicador", value=f"x{multiplicador}", inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            logger.info(f"Owner {interaction.user.name} añadió producto virtual: {nombre} (ID: {product_id})")
            
        except Exception as e:
            logger.error(f"Error al añadir producto virtual: {str(e)}")
            await interaction.response.send_message("❌ Error al añadir el producto virtual.", ephemeral=True)
    
    @tree.command(name="editar_producto_virtual", description="[OWNER] Edita un producto virtual")
    @app_commands.describe(
        product_id="ID del producto a editar",
        nombre="Nuevo nombre (opcional)",
        precio="Nuevo precio en GameCoins (opcional)",
        descripcion="Nueva descripción (opcional)",
        habilitado="Habilitar/deshabilitar producto"
    )
    async def edit_virtual_product(interaction: discord.Interaction,
                                 product_id: str,
                                 nombre: Optional[str] = None,
                                 precio: Optional[int] = None,
                                 descripcion: Optional[str] = None,
                                 habilitado: Optional[bool] = None):
        """Edita un producto virtual"""
        if not is_owner(interaction):
            await interaction.response.send_message("❌ Solo los owners pueden usar este comando.", ephemeral=True)
            return
        
        try:
            # Verificar que el producto existe
            products = virtual_shop.get_virtual_products()
            if product_id not in products:
                await interaction.response.send_message("❌ Producto no encontrado.", ephemeral=True)
                return
            
            # Validaciones
            if precio is not None and precio <= 0:
                await interaction.response.send_message("❌ El precio debe ser mayor a 0.", ephemeral=True)
                return
            
            # Preparar datos para actualizar
            update_data = {}
            if nombre is not None:
                update_data["name"] = nombre
            if precio is not None:
                update_data["price"] = precio
            if descripcion is not None:
                update_data["description"] = descripcion
            if habilitado is not None:
                update_data["enabled"] = habilitado
            
            if not update_data:
                await interaction.response.send_message("❌ Debes especificar al menos un campo para editar.", ephemeral=True)
                return
            
            # Actualizar el producto
            success = virtual_shop.edit_virtual_product(product_id, **update_data)
            
            if success:
                product = products[product_id]
                embed = discord.Embed(
                    title="✅ Producto Virtual Editado",
                    description=f"El producto **{product['name']}** ha sido actualizado exitosamente.",
                    color=0x00ff88
                )
                
                embed.add_field(name="🔑 ID", value=f"`{product_id}`", inline=False)
                
                for field, value in update_data.items():
                    if field == "name":
                        embed.add_field(name="🏷️ Nuevo Nombre", value=value, inline=True)
                    elif field == "price":
                        embed.add_field(name="💰 Nuevo Precio", value=f"{value:,} GameCoins", inline=True)
                    elif field == "description":
                        embed.add_field(name="📝 Nueva Descripción", value=value, inline=False)
                    elif field == "enabled":
                        status = "Habilitado" if value else "Deshabilitado"
                        embed.add_field(name="🔄 Estado", value=status, inline=True)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                logger.info(f"Owner {interaction.user.name} editó producto virtual: {product_id}")
            else:
                await interaction.response.send_message("❌ Error al editar el producto.", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error al editar producto virtual: {str(e)}")
            await interaction.response.send_message("❌ Error al editar el producto virtual.", ephemeral=True)
    
    @tree.command(name="eliminar_producto_virtual", description="[OWNER] Elimina un producto virtual")
    @app_commands.describe(product_id="ID del producto a eliminar")
    async def delete_virtual_product(interaction: discord.Interaction, product_id: str):
        """Elimina un producto virtual"""
        if not is_owner(interaction):
            await interaction.response.send_message("❌ Solo los owners pueden usar este comando.", ephemeral=True)
            return
        
        try:
            # Verificar que el producto existe
            products = virtual_shop.get_virtual_products()
            if product_id not in products:
                await interaction.response.send_message("❌ Producto no encontrado.", ephemeral=True)
                return
            
            product_name = products[product_id]["name"]
            
            # Eliminar el producto
            success = virtual_shop.remove_virtual_product(product_id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Producto Virtual Eliminado",
                    description=f"El producto **{product_name}** ha sido eliminado de la tienda virtual.",
                    color=0xff6b6b
                )
                embed.add_field(name="🔑 ID Eliminado", value=f"`{product_id}`", inline=False)
                embed.add_field(
                    name="⚠️ Nota",
                    value="Los usuarios que ya compraron este producto conservan sus compras.",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                logger.info(f"Owner {interaction.user.name} eliminó producto virtual: {product_name} (ID: {product_id})")
            else:
                await interaction.response.send_message("❌ Error al eliminar el producto.", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error al eliminar producto virtual: {str(e)}")
            await interaction.response.send_message("❌ Error al eliminar el producto virtual.", ephemeral=True)
    
    @tree.command(name="listar_productos_virtuales", description="[OWNER] Lista todos los productos virtuales")
    async def list_virtual_products(interaction: discord.Interaction):
        """Lista todos los productos virtuales"""
        if not is_owner(interaction):
            await interaction.response.send_message("❌ Solo los owners pueden usar este comando.", ephemeral=True)
            return
        
        try:
            products = virtual_shop.get_virtual_products()
            stats = virtual_shop.get_shop_stats()
            
            embed = discord.Embed(
                title="📋 Lista de Productos Virtuales",
                description="Gestión de la tienda virtual de GameCoins",
                color=0x9932cc
            )
            
            # Estadísticas generales
            embed.add_field(
                name="📊 Estadísticas",
                value=f"**Total:** {stats['total_products']} productos\n"
                      f"**Activos:** {stats['active_products']} productos\n"
                      f"**Compras:** {stats['total_purchases']} realizadas\n"
                      f"**Ingresos:** {stats['total_revenue']:,} GameCoins",
                inline=False
            )
            
            if not products:
                embed.add_field(
                    name="❌ Sin Productos",
                    value="No hay productos virtuales creados.",
                    inline=False
                )
            else:
                # Agrupar por categoría
                by_category = {}
                for product_id, product in products.items():
                    category = product.get('category', 'sin_categoria')
                    if category not in by_category:
                        by_category[category] = []
                    by_category[category].append((product_id, product))
                
                for category, category_products in by_category.items():
                    category_info = virtual_shop.categories.get(category, {"name": "Sin Categoría", "emoji": "📦"})
                    
                    products_text = ""
                    for product_id, product in category_products[:3]:  # Máximo 3 por categoría
                        status = "✅" if product.get('enabled', True) else "❌"
                        products_text += f"{status} **{product['name']}** - {product['price']:,} GC\n"
                        products_text += f"   `{product_id}`\n"
                    
                    if len(category_products) > 3:
                        products_text += f"   ... y {len(category_products) - 3} más\n"
                    
                    embed.add_field(
                        name=f"{category_info['emoji']} {category_info['name']} ({len(category_products)})",
                        value=products_text or "Sin productos",
                        inline=False
                    )
            
            embed.set_footer(text="Usa los comandos de gestión para añadir, editar o eliminar productos")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error al listar productos virtuales: {str(e)}")
            await interaction.response.send_message("❌ Error al obtener la lista de productos.", ephemeral=True)
    

    
    # Autocompletado para IDs de productos
    @edit_virtual_product.autocomplete('product_id')
    @delete_virtual_product.autocomplete('product_id')
    async def product_id_autocomplete(interaction: discord.Interaction, current: str):
        if not is_owner(interaction):
            return []
        
        products = virtual_shop.get_virtual_products()
        return [
            app_commands.Choice(name=f"{product['name']} ({product_id[:8]}...)", value=product_id)
            for product_id, product in products.items()
            if current.lower() in product['name'].lower() or current.lower() in product_id.lower()
        ][:25]

    logger.info("Comandos de tienda virtual cargados exitosamente")