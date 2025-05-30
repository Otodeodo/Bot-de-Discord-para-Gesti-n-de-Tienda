import discord
from discord import app_commands
from typing import Optional
import uuid
import asyncio
from datetime import datetime
import logging
from data_manager import load_data, save_data
from utils import is_owner


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