import discord
from discord import app_commands
from typing import Optional
import uuid
import asyncio
from datetime import datetime
import logging
from data_manager import load_data, save_data
from utils import is_owner
from reminder_system import get_reminder_system


# Configuración del logging
logger = logging.getLogger(__name__)

def setup(tree: app_commands.CommandTree, client: discord.Client):
    @tree.command(name="add_product", description="Añade un nuevo producto")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def add_product(interaction: discord.Interaction, name: str, price: float, description: str, image_url: Optional[str] = None):
        logger.info(f"Owner {interaction.user.name} (ID: {interaction.user.id}) está añadiendo un nuevo producto: {name}")
        if price <= 0:
            logger.warning(f"Intento de añadir producto con precio inválido: {price}")
            await interaction.response.send_message("El precio debe ser positivo.", ephemeral=True)
            return
        data = load_data()
        product_id = str(uuid.uuid4())
        data["products"][product_id] = {
            "name": name,
            "price": price,
            "description": description,
            "image_url": image_url
        }
        save_data(data)
        logger.info(f"Producto {name} (ID: {product_id}) añadido exitosamente - Precio: ${price:.2f} MXN")
        await interaction.response.send_message(f"Producto '{name}' añadido (ID: {product_id}).", ephemeral=True)

    @tree.command(name="edit_product", description="Edita un producto existente")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def edit_product(interaction: discord.Interaction, product_id: str, name: Optional[str], price: Optional[float], description: Optional[str], image_url: Optional[str] = None):
        logger.info(f"Owner {interaction.user.name} (ID: {interaction.user.id}) está editando el producto {product_id}")
        data = load_data()
        if product_id not in data["products"]:
            logger.warning(f"Intento de editar producto inexistente con ID: {product_id}")
            await interaction.response.send_message("El producto no existe.", ephemeral=True)
            return
        if name:
            data["products"][product_id]["name"] = name
        if price is not None:
            if price <= 0:
                logger.warning(f"Intento de actualizar producto con precio inválido: {price}")
                await interaction.response.send_message("El precio debe ser positivo.", ephemeral=True)
                return
            data["products"][product_id]["price"] = price
        if description:
            data["products"][product_id]["description"] = description
        if image_url is not None:
            data["products"][product_id]["image_url"] = image_url
        save_data(data)
        logger.info(f"Producto {product_id} actualizado exitosamente")
        await interaction.response.send_message(f"Producto {product_id} actualizado.", ephemeral=True)


    @tree.command(name="delete_product", description="Elimina un producto")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def delete_product(interaction: discord.Interaction, product_id: str):
        logger.info(f"Owner {interaction.user.name} (ID: {interaction.user.id}) está intentando eliminar el producto {product_id}")
        data = load_data()
        if product_id not in data["products"]:
            logger.warning(f"Intento de eliminar producto inexistente con ID: {product_id}")
            await interaction.response.send_message("El producto no existe.", ephemeral=True)
            return
        product_name = data["products"][product_id]["name"]
        del data["products"][product_id]
        save_data(data)
        logger.info(f"Producto {product_name} (ID: {product_id}) eliminado exitosamente")
        await interaction.response.send_message(f"Producto {product_id} eliminado.", ephemeral=True)


    @tree.command(name="create_announcement", description="Crea un anuncio con un embed personalizado")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def create_announcement(
        interaction: discord.Interaction, 
        channel: discord.TextChannel, 
        title: str, 
        description: str, 
        color: Optional[str] = None, 
        image_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        author_name: Optional[str] = None,
        author_icon_url: Optional[str] = None,
        fields: Optional[str] = None
    ):
        try:
            # Validar el color si se proporciona
            embed_color = None
            if color:
                try:
                    # Convertir el color de hex a decimal
                    color = color.strip('#')
                    embed_color = int(color, 16)
                except ValueError:
                    await interaction.response.send_message("El color debe estar en formato hexadecimal (ejemplo: #FF0000)", ephemeral=True)
                    return
            
            # Crear el embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=embed_color or 0xA100F2  # Usar el color predeterminado si no se proporciona uno
            )
            
            # Añadir imagen principal si se proporciona
            if image_url:
                embed.set_image(url=image_url)
            
            # Añadir thumbnail si se proporciona
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            
            # Añadir autor si se proporciona
            if author_name:
                embed.set_author(
                    name=author_name,
                    icon_url=author_icon_url if author_icon_url else None
                )
            
            # Añadir campos si se proporcionan (formato: "nombre1|valor1;nombre2|valor2")
            if fields:
                try:
                    field_pairs = fields.split(';')
                    for pair in field_pairs:
                        name, value = pair.split('|')
                        embed.add_field(name=name.strip(), value=value.strip(), inline=True)
                except ValueError:
                    await interaction.response.send_message(
                        "Error: El formato de los campos debe ser 'nombre1|valor1;nombre2|valor2'",
                        ephemeral=True
                    )
                    return
            
            # Añadir pie de página con la fecha
            embed.set_footer(text=f"Anuncio creado el {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Enviar el embed al canal especificado
            await channel.send(embed=embed)
            await interaction.response.send_message(f"Anuncio enviado exitosamente en {channel.mention}", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message("Error: No tengo permisos para enviar mensajes en ese canal.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error al crear el anuncio: {str(e)}", ephemeral=True)

    @tree.command(name="sync", description="Sincroniza manualmente los comandos del bot (Owner only)")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def sync(interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            guild = discord.Object(id=interaction.guild.id)
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
            await tree.sync()
            await interaction.followup.send("Comandos sincronizados exitosamente en este servidor y globalmente.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error al sincronizar comandos: {str(e)}", ephemeral=True)

    @tree.command(name="reminder_stats", description="Muestra estadísticas del sistema de recordatorios (Owner only)")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def reminder_stats(interaction: discord.Interaction):
        """Muestra estadísticas del sistema de recordatorios de Robux."""
        try:
            reminder_system = get_reminder_system()
            if not reminder_system:
                await interaction.response.send_message("❌ Sistema de recordatorios no inicializado.", ephemeral=True)
                return
                
            stats = reminder_system.get_reminder_stats()
            if not stats:
                await interaction.response.send_message("❌ Error al obtener estadísticas.", ephemeral=True)
                return
                
            embed = discord.Embed(
                title="📊 Estadísticas del Sistema de Recordatorios",
                color=0x00FF00 if stats['is_running'] else 0xFF0000
            )
            
            embed.add_field(
                name="🔄 Estado del Sistema",
                value=f"```yaml\n"
                      f"Estado: {'🟢 Activo' if stats['is_running'] else '🔴 Inactivo'}\n"
                      f"```",
                inline=False
            )
            
            embed.add_field(
                name="📈 Estadísticas Generales",
                value=f"```yaml\n"
                      f"Cuentas vinculadas: {stats['total_linked_accounts']}\n"
                      f"Usuarios recordados: {stats['total_reminded']}\n"
                      f"Elegibles sin recordar: {stats['eligible_not_reminded']}\n"
                      f"```",
                inline=False
            )
            
            embed.set_footer(
                text="Sistema de Recordatorios • GameMid",
                icon_url="https://cdn.discordapp.com/attachments/1234567890/roblox_icon.png"
            )
            embed.timestamp = datetime.utcnow()
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en reminder_stats: {e}")
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

    @tree.command(name="reminder_control", description="Controla el sistema de recordatorios (Owner only)")
    @app_commands.describe(action="Acción a realizar: start, stop, restart")
    @app_commands.choices(action=[
        app_commands.Choice(name="Iniciar", value="start"),
        app_commands.Choice(name="Detener", value="stop"),
        app_commands.Choice(name="Reiniciar", value="restart")
    ])
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def reminder_control(interaction: discord.Interaction, action: str):
        """Controla el estado del sistema de recordatorios."""
        try:
            reminder_system = get_reminder_system()
            if not reminder_system:
                await interaction.response.send_message("❌ Sistema de recordatorios no inicializado.", ephemeral=True)
                return
                
            await interaction.response.defer(ephemeral=True)
            
            if action == "start":
                if reminder_system.is_running:
                    await interaction.followup.send("⚠️ El sistema de recordatorios ya está ejecutándose.", ephemeral=True)
                else:
                    await reminder_system.start_reminder_system()
                    await interaction.followup.send("✅ Sistema de recordatorios iniciado exitosamente.", ephemeral=True)
                    
            elif action == "stop":
                if not reminder_system.is_running:
                    await interaction.followup.send("⚠️ El sistema de recordatorios ya está detenido.", ephemeral=True)
                else:
                    await reminder_system.stop_reminder_system()
                    await interaction.followup.send("🛑 Sistema de recordatorios detenido exitosamente.", ephemeral=True)
                    
            elif action == "restart":
                await reminder_system.stop_reminder_system()
                await asyncio.sleep(2)  # Esperar un poco antes de reiniciar
                await reminder_system.start_reminder_system()
                await interaction.followup.send("🔄 Sistema de recordatorios reiniciado exitosamente.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error en reminder_control: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

    @tree.command(name="send_manual_reminder", description="Envía un recordatorio manual a un usuario (Owner only)")
    @app_commands.describe(user="Usuario al que enviar el recordatorio")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def send_manual_reminder(interaction: discord.Interaction, user: discord.User):
        """Envía un recordatorio manual de elegibilidad para Robux a un usuario específico."""
        try:
            reminder_system = get_reminder_system()
            if not reminder_system:
                await interaction.response.send_message("❌ Sistema de recordatorios no inicializado.", ephemeral=True)
                return
                
            await interaction.response.defer(ephemeral=True)
            
            success, message = await reminder_system.send_manual_reminder(str(user.id))
            
            if success:
                embed = discord.Embed(
                    title="✅ Recordatorio Enviado",
                    description=f"Recordatorio de elegibilidad para Robux enviado exitosamente a {user.mention}.",
                    color=0x00FF00
                )
                embed.add_field(
                    name="👤 Usuario",
                    value=f"**Nombre:** {user.display_name}\n**ID:** {user.id}",
                    inline=False
                )
                embed.set_footer(text="Sistema de Recordatorios • GameMid")
                embed.timestamp = datetime.utcnow()
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="❌ Error al Enviar Recordatorio",
                    description=f"No se pudo enviar el recordatorio a {user.mention}.",
                    color=0xFF0000
                )
                embed.add_field(
                    name="🔍 Razón",
                    value=message,
                    inline=False
                )
                embed.set_footer(text="Sistema de Recordatorios • GameMid")
                embed.timestamp = datetime.utcnow()
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error en send_manual_reminder: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

    @tree.command(name="add_coins", description="Añade GameCoins a un usuario (Owner only)")
    @app_commands.describe(
        user="Usuario al que añadir GameCoins",
        amount="Cantidad de GameCoins a añadir",
        reason="Razón para añadir las monedas (opcional)"
    )
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def add_coins(interaction: discord.Interaction, user: discord.User, amount: int, reason: Optional[str] = "Añadido por el owner"):
        """Añade GameCoins a un usuario específico."""
        try:
            from economy_system import economy
            
            if amount <= 0:
                await interaction.response.send_message("❌ La cantidad debe ser positiva.", ephemeral=True)
                return
            
            # Obtener balance anterior
            user_economy = economy.get_user_economy(str(user.id))
            old_balance = user_economy["coins"]
            
            # Añadir las monedas
            new_balance = economy.add_coins(str(user.id), amount, reason)
            
            # Crear embed de confirmación
            embed = discord.Embed(
                title="💰 GameCoins Añadidas",
                description=f"Se han añadido **{amount:,} GameCoins** a {user.mention}",
                color=0x00FF00
            )
            embed.add_field(
                name="👤 Usuario",
                value=f"**Nombre:** {user.display_name}\n**ID:** {user.id}",
                inline=True
            )
            embed.add_field(
                name="💰 Balance",
                value=f"**Anterior:** {old_balance:,} GameCoins\n**Nuevo:** {new_balance:,} GameCoins",
                inline=True
            )
            embed.add_field(
                name="📝 Razón",
                value=reason,
                inline=False
            )
            embed.set_footer(text="Sistema Económico • GameMid")
            embed.timestamp = datetime.utcnow()
            
            logger.info(f"Owner {interaction.user.name} (ID: {interaction.user.id}) añadió {amount} GameCoins a {user.name} (ID: {user.id}). Razón: {reason}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en add_coins: {e}")
            await interaction.response.send_message(f"❌ Error al añadir GameCoins: {str(e)}", ephemeral=True)