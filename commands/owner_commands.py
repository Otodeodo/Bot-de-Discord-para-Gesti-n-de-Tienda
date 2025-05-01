import discord
from discord import app_commands
from typing import Optional
import uuid
import asyncio
from datetime import datetime

from data_manager import load_data, save_data
from utils import is_owner
from views.ticket_panel_view import TicketPanelView
from config import TICKET_CHANNEL_ID

def setup(tree: app_commands.CommandTree, client: discord.Client):
    @tree.command(name="add_product", description="Añade un nuevo producto")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def add_product(interaction: discord.Interaction, name: str, price: float, description: str, image_url: Optional[str] = None):
        if price <= 0:
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
        print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Producto {name} (ID: {product_id}) añadido por {interaction.user.name} (ID: {interaction.user.id}) - Precio: ${price:.2f} MXN")
        await interaction.response.send_message(f"Producto '{name}' añadido (ID: {product_id}).", ephemeral=True)

    @tree.command(name="edit_product", description="Edita un producto existente")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def edit_product(interaction: discord.Interaction, product_id: str, name: Optional[str], price: Optional[float], description: Optional[str], image_url: Optional[str] = None):
        data = load_data()
        if product_id not in data["products"]:
            await interaction.response.send_message("El producto no existe.", ephemeral=True)
            return
        if name:
            data["products"][product_id]["name"] = name
        if price is not None and price > 0:
            data["products"][product_id]["price"] = price
        if description:
            data["products"][product_id]["description"] = description
        if image_url is not None:
            data["products"][product_id]["image_url"] = image_url
        save_data(data)
        await interaction.response.send_message(f"Producto {product_id} actualizado.", ephemeral=True)

    @tree.command(name="delete_product", description="Elimina un producto")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def delete_product(interaction: discord.Interaction, product_id: str):
        data = load_data()
        if product_id not in data["products"]:
            await interaction.response.send_message("El producto no existe.", ephemeral=True)
            return
        product_name = data["products"][product_id]["name"]
        del data["products"][product_id]
        save_data(data)
        print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Producto {product_name} (ID: {product_id}) eliminado por {interaction.user.name} (ID: {interaction.user.id})")
        await interaction.response.send_message(f"Producto {product_id} eliminado.", ephemeral=True)

    @tree.command(name="close", description="Cierra el ticket actual (Owner only)")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def close(interaction: discord.Interaction):
        try:
            # Deferir la respuesta para evitar el timeout de 3 segundos
            await interaction.response.defer(ephemeral=True)

            data = load_data()
            channel_id = str(interaction.channel.id)
            
            # Buscar el ticket asociado con este canal
            ticket = None
            ticket_id = None
            for tid, t in data["tickets"].items():
                if t["channel_id"] == channel_id and t["status"] == "abierto":
                    ticket = t
                    ticket_id = tid
                    break
            
            if not ticket:
                await interaction.followup.send("Este canal no es un ticket abierto o no existe.", ephemeral=True)
                return
            
            # Actualizar el estado del ticket a "cerrado"
            data["tickets"][ticket_id]["status"] = "cerrado"
            data["tickets"][ticket_id]["closed_timestamp"] = datetime.utcnow().isoformat()
            save_data(data)
            print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Ticket #{ticket_id} cerrado por {interaction.user.name} (ID: {interaction.user.id})")
            
            # Notificar al usuario del ticket que se ha cerrado
            user_id = ticket["user_id"]
            try:
                user = await interaction.guild.fetch_member(int(user_id))
                await user.send(f"Tu ticket #{ticket_id} ha sido cerrado por un Owner.")
            except (discord.NotFound, discord.Forbidden):
                # Si no se puede notificar al usuario, ignorar
                pass
            
            # Eliminar el canal
            try:
                await interaction.channel.delete()
                return  # Salir después de eliminar el canal para evitar más interacciones
            except discord.Forbidden:
                await interaction.followup.send("Error: No tengo permisos para eliminar el canal.", ephemeral=True)
            except discord.NotFound:
                # El canal ya fue eliminado, ignorar
                pass
            except Exception as e:
                print(f"Error al eliminar el canal del ticket: {str(e)}")
                await interaction.followup.send(f"Error al eliminar el canal: {str(e)}", ephemeral=True)

        except Exception as e:
            print(f"Error en el comando close: {str(e)}")
            # Solo intentar enviar mensaje de error si la interacción no ha sido respondida
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Error al cerrar el ticket: {str(e)}", ephemeral=True)


    @tree.command(name="ticket_panel", description="Crea un panel para abrir tickets")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def ticket_panel(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎟️ Sistema de Tickets",
            description="Haz clic en el botón para abrir un ticket de compra.",
            color=0xA100F2
        )
        view = TicketPanelView()
        channel = client.get_channel(TICKET_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("Error: El canal de tickets no está configurado correctamente.", ephemeral=True)
            return
        try:
            await channel.send(embed=embed, view=view)
            await interaction.response.send_message("Panel de tickets creado exitosamente.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Error: No tengo permisos para enviar mensajes en el canal de tickets.", ephemeral=True)

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