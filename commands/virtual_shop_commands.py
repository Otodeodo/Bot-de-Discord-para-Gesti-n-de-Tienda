import discord
from discord import app_commands
from discord.ext import commands
import logging
from virtual_shop import virtual_shop
from views.virtual_shop_view import VirtualShopView
from config import OWNER_ROLE_ID

logger = logging.getLogger(__name__)

def setup(tree: app_commands.CommandTree, client: commands.Bot):
    """Configura los comandos de la tienda virtual"""
    
    def is_owner():
        async def predicate(interaction: discord.Interaction) -> bool:
            role = discord.utils.get(interaction.user.roles, id=OWNER_ROLE_ID)
            if role is None:
                await interaction.response.send_message("No tienes permisos para ejecutar este comando. Este comando está reservado para Owners.", ephemeral=True)
                return False
            return True
        return app_commands.check(predicate)
    
    @tree.command(name="añadir_producto_virtual", description="[OWNER] Añade un producto virtual a la tienda")
    @app_commands.describe(
        nombre="Nombre del producto",
        precio="Precio en GameCoins",
        descripcion="Descripción del producto",
        categoria="Categoría del producto",
        imagen_url="URL de la imagen (opcional)",
        rol_id="ID del rol a otorgar (opcional)",
        duracion_dias="Duración en días para productos temporales (opcional)"
    )
    @app_commands.choices(categoria=[
        app_commands.Choice(name="🎭 Roles", value="roles"),
        app_commands.Choice(name="⭐ Beneficios", value="perks"),
        app_commands.Choice(name="🎁 Items", value="items"),
        app_commands.Choice(name="✨ Cosméticos", value="cosmetics"),
        app_commands.Choice(name="📦 Otros", value="other")
    ])
    @is_owner()
    async def añadir_producto_virtual(interaction: discord.Interaction, nombre: str, precio: int, 
                                    descripcion: str, categoria: str, imagen_url: str = None, 
                                    rol_id: str = None, duracion_dias: int = None):
        """Añade un producto virtual a la tienda"""
        try:
            await interaction.response.defer()
            
            # Validaciones
            if precio <= 0:
                await interaction.followup.send("❌ El precio debe ser mayor a 0.", ephemeral=True)
                return
            
            if len(nombre) > 100:
                await interaction.followup.send("❌ El nombre no puede exceder 100 caracteres.", ephemeral=True)
                return
            
            if len(descripcion) > 500:
                await interaction.followup.send("❌ La descripción no puede exceder 500 caracteres.", ephemeral=True)
                return
            
            # Validar rol si se proporciona
            role = None
            if rol_id:
                try:
                    role = interaction.guild.get_role(int(rol_id))
                    if not role:
                        await interaction.followup.send("❌ No se encontró el rol especificado.", ephemeral=True)
                        return
                except ValueError:
                    await interaction.followup.send("❌ ID de rol inválido.", ephemeral=True)
                    return
            
            # Añadir producto
            product_id = virtual_shop.add_virtual_product(
                name=nombre,
                price=precio,
                description=descripcion,
                category=categoria,
                image_url=imagen_url,
                role_id=rol_id,
                duration_days=duracion_dias
            )
            
            # Crear embed de confirmación
            embed = discord.Embed(
                title="✅ Producto Añadido",
                description=f"El producto **{nombre}** ha sido añadido exitosamente a la tienda virtual.",
                color=0x00ff00
            )
            
            category_info = virtual_shop.categories.get(categoria, {"name": "Sin Categoría", "emoji": "📦"})
            
            embed.add_field(name="📦 Producto", value=nombre, inline=True)
            embed.add_field(name="💰 Precio", value=f"{precio:,} GameCoins", inline=True)
            embed.add_field(name="📂 Categoría", value=f"{category_info['emoji']} {category_info['name']}", inline=True)
            embed.add_field(name="📝 Descripción", value=descripcion, inline=False)
            
            if role:
                embed.add_field(name="🎭 Rol", value=role.mention, inline=True)
            
            if duracion_dias:
                embed.add_field(name="⏰ Duración", value=f"{duracion_dias} días", inline=True)
            
            if imagen_url:
                embed.set_thumbnail(url=imagen_url)
            
            embed.add_field(name="🆔 ID del Producto", value=f"`{product_id}`", inline=False)
            embed.set_footer(text=f"Añadido por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al añadir producto virtual: {e}")
            await interaction.followup.send("❌ Error al añadir el producto. Intenta de nuevo.", ephemeral=True)
    
    @tree.command(name="editar_producto_virtual", description="[OWNER] Edita un producto virtual")
    @app_commands.describe(
        product_id="ID del producto a editar",
        nombre="Nuevo nombre (opcional)",
        precio="Nuevo precio (opcional)",
        descripcion="Nueva descripción (opcional)",
        habilitado="Habilitar/deshabilitar producto"
    )
    @is_owner()
    async def editar_producto_virtual(interaction: discord.Interaction, product_id: str, 
                                     nombre: str = None, precio: int = None, 
                                     descripcion: str = None, habilitado: bool = None):
        """Edita un producto virtual existente"""
        try:
            await interaction.response.defer()
            
            # Verificar que el producto existe
            products = virtual_shop.get_virtual_products()
            if product_id not in products:
                await interaction.followup.send("❌ Producto no encontrado.", ephemeral=True)
                return
            
            # Preparar datos de actualización
            update_data = {}
            if nombre is not None:
                if len(nombre) > 100:
                    await interaction.followup.send("❌ El nombre no puede exceder 100 caracteres.", ephemeral=True)
                    return
                update_data['name'] = nombre
            
            if precio is not None:
                if precio <= 0:
                    await interaction.followup.send("❌ El precio debe ser mayor a 0.", ephemeral=True)
                    return
                update_data['price'] = precio
            
            if descripcion is not None:
                if len(descripcion) > 500:
                    await interaction.followup.send("❌ La descripción no puede exceder 500 caracteres.", ephemeral=True)
                    return
                update_data['description'] = descripcion
            
            if habilitado is not None:
                update_data['enabled'] = habilitado
            
            if not update_data:
                await interaction.followup.send("❌ No se especificaron cambios.", ephemeral=True)
                return
            
            # Actualizar producto
            success = virtual_shop.edit_virtual_product(product_id, **update_data)
            
            if success:
                product = products[product_id]
                embed = discord.Embed(
                    title="✅ Producto Actualizado",
                    description=f"El producto **{product['name']}** ha sido actualizado.",
                    color=0x00ff00
                )
                
                changes = []
                for field, value in update_data.items():
                    if field == 'name':
                        changes.append(f"📦 Nombre: {value}")
                    elif field == 'price':
                        changes.append(f"💰 Precio: {value:,} GameCoins")
                    elif field == 'description':
                        changes.append(f"📝 Descripción: {value}")
                    elif field == 'enabled':
                        status = "✅ Habilitado" if value else "❌ Deshabilitado"
                        changes.append(f"🔄 Estado: {status}")
                
                embed.add_field(name="Cambios realizados", value="\n".join(changes), inline=False)
                embed.set_footer(text=f"Editado por {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Error al actualizar el producto.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error al editar producto virtual: {e}")
            await interaction.followup.send("❌ Error al editar el producto. Intenta de nuevo.", ephemeral=True)
    
    @tree.command(name="eliminar_producto_virtual", description="[OWNER] Elimina un producto virtual")
    @app_commands.describe(product_id="ID del producto a eliminar")
    @is_owner()
    async def eliminar_producto_virtual(interaction: discord.Interaction, product_id: str):
        """Elimina un producto virtual de la tienda"""
        try:
            await interaction.response.defer()
            
            # Verificar que el producto existe
            products = virtual_shop.get_virtual_products()
            if product_id not in products:
                await interaction.followup.send("❌ Producto no encontrado.", ephemeral=True)
                return
            
            product_name = products[product_id]['name']
            
            # Eliminar producto
            success = virtual_shop.remove_virtual_product(product_id)
            
            if success:
                embed = discord.Embed(
                    title="🗑️ Producto Eliminado",
                    description=f"El producto **{product_name}** ha sido eliminado de la tienda virtual.",
                    color=0xff0000
                )
                embed.set_footer(text=f"Eliminado por {interaction.user.display_name}")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Error al eliminar el producto.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error al eliminar producto virtual: {e}")
            await interaction.followup.send("❌ Error al eliminar el producto. Intenta de nuevo.", ephemeral=True)
    
    @tree.command(name="gestionar_tienda_virtual", description="[OWNER] Panel de gestión de la tienda virtual")
    @is_owner()
    async def gestionar_tienda_virtual(interaction: discord.Interaction):
        """Muestra el panel de gestión de la tienda virtual"""
        try:
            await interaction.response.defer()
            
            products = virtual_shop.get_virtual_products()
            stats = virtual_shop.get_shop_stats()
            
            embed = discord.Embed(
                title="🛒 Gestión de Tienda Virtual",
                description="Gestión de la tienda virtual de GameCoins",
                color=0x3498db
            )
            
            # Estadísticas
            embed.add_field(
                name="📊 Estadísticas",
                value=f"📦 Productos: {stats['total_products']} ({stats['enabled_products']} activos)\n"
                      f"🛍️ Compras: {stats['total_purchases']}\n"
                      f"💰 Ingresos: {stats['total_revenue']:,} GameCoins",
                inline=True
            )
            
            # Productos por categoría
            categorized = virtual_shop.get_products_by_category()
            category_summary = []
            for category_id, category_info in virtual_shop.categories.items():
                count = len(categorized.get(category_id, []))
                if count > 0:
                    category_summary.append(f"{category_info['emoji']} {category_info['name']}: {count}")
            
            if category_summary:
                embed.add_field(
                    name="📂 Productos por Categoría",
                    value="\n".join(category_summary),
                    inline=True
                )
            
            # Comandos disponibles
            embed.add_field(
                name="⚙️ Comandos Disponibles",
                value="`/añadir_producto_virtual` - Añadir producto\n"
                      "`/editar_producto_virtual` - Editar producto\n"
                      "`/eliminar_producto_virtual` - Eliminar producto\n"
                      "`/listar_productos_virtuales` - Ver todos los productos",
                inline=False
            )
            
            embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error en gestión de tienda virtual: {e}")
            await interaction.followup.send("❌ Error al cargar el panel de gestión.", ephemeral=True)
    
    @tree.command(name="listar_productos_virtuales", description="[OWNER] Lista todos los productos virtuales")
    @is_owner()
    async def listar_productos_virtuales(interaction: discord.Interaction):
        """Lista todos los productos virtuales con detalles"""
        try:
            await interaction.response.defer()
            
            products = virtual_shop.get_virtual_products()
            
            if not products:
                await interaction.followup.send("📦 No hay productos en la tienda virtual.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📦 Lista de Productos Virtuales",
                description=f"Total: {len(products)} productos",
                color=0x3498db
            )
            
            for product_id, product in products.items():
                status = "✅" if product.get('enabled', True) else "❌"
                category_info = virtual_shop.categories.get(product.get('category', 'other'), {"name": "Sin Categoría", "emoji": "📦"})
                
                value = f"💰 **{product['price']:,}** GameCoins\n"
                value += f"📂 {category_info['emoji']} {category_info['name']}\n"
                value += f"🛍️ Compras: {product.get('purchases_count', 0)}\n"
                value += f"🆔 `{product_id}`"
                
                embed.add_field(
                    name=f"{status} {product['name']}",
                    value=value,
                    inline=True
                )
            
            embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al listar productos virtuales: {e}")
            await interaction.followup.send("❌ Error al cargar la lista de productos.", ephemeral=True)
    
    # Autocompletado para IDs de productos
    @eliminar_producto_virtual.autocomplete('product_id')
    @editar_producto_virtual.autocomplete('product_id')
    async def product_autocomplete(interaction: discord.Interaction, current: str):
        products = virtual_shop.get_virtual_products()
        choices = []
        
        for product_id, product in products.items():
            if current.lower() in product['name'].lower() or current.lower() in product_id.lower():
                choices.append(app_commands.Choice(
                    name=f"{product['name']} ({product['price']:,} GameCoins)",
                    value=product_id
                ))
                
                if len(choices) >= 25:  # Discord limit
                    break
        
        return choices
    
    logger.info("Comandos de tienda virtual cargados exitosamente")