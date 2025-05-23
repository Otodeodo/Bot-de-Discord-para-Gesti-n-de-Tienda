import discord
from discord import app_commands
import logging

from data_manager import load_data, save_data
from utils import is_owner

# Configuración del logging
logger = logging.getLogger(__name__)

def setup(tree: app_commands.CommandTree, client: discord.Client):
    @client.event
    async def on_member_join(member):
        # Verificar si el canal de sistema existe antes de crear el embed
        system_channel = member.guild.system_channel
        if not system_channel:
            print(f"No se pudo enviar mensaje de bienvenida: No hay canal de sistema configurado")
            return

        embed = discord.Embed(
            title="👋 ¡Bienvenido a nuestro servidor!",
            description=f"¡Hola {member.mention}! Gracias por unirte a nuestra comunidad.",
            color=0xA100F2
        )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.add_field(
            name="🛍️ Ver Productos",
            value="Usa `/products` para ver todos los productos disponibles.",
            inline=False
        )
        embed.add_field(
            name="🎫 Crear Ticket",
            value="Usa `/ticket` para abrir un ticket y realizar una compra.",
            inline=False
        )
        embed.add_field(
            name="📜 Comandos",
            value="Usa `/help` para ver todos los comandos disponibles.",
            inline=False
        )
        embed.add_field(
            name="@AssistantMid",
            value="Pregúntale tus dudas a Mari!",
            inline=False
        )
        embed.set_footer(text=f"ID: {member.id}")
        
        try:
            await system_channel.send(embed=embed)
        except Exception as e:
            print(f"Error al enviar mensaje de bienvenida: {e}")


    @tree.command(name="pago", description="Muestra la información de pago para los métodos disponibles")
    async def pago(interaction: discord.Interaction):
        logger.info(f"Usuario {interaction.user.name} (ID: {interaction.user.id}) solicitó información de pago")
        data = load_data()
        payment_info = data.get("payment_info", {})
        
        if not payment_info:
            logger.warning("No hay información de pago configurada en el sistema")
            await interaction.response.send_message("No hay información de pago disponible. Contacta a un Owner.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💳 Información de Pago",
            description="Aquí tienes los detalles para realizar el pago:",
            color=0xA100F2
        )
        
        for method, info in payment_info.items():
            embed.add_field(
                name=method,
                value=info,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @tree.command(name="add_payment_info", description="Añade o actualiza la información de un método de pago")
    @is_owner()
    async def add_payment_info(interaction: discord.Interaction, method: str, info: str):
        logger.info(f"Owner {interaction.user.name} (ID: {interaction.user.id}) está actualizando información de pago para el método {method}")
        data = load_data()
        if "payment_info" not in data:
            data["payment_info"] = {}
        
        data["payment_info"][method] = info
        save_data(data)
        logger.info(f"Información de pago actualizada exitosamente para el método {method}")
        await interaction.response.send_message(f"Información de pago para '{method}' actualizada: {info}", ephemeral=True)

    @tree.command(name="remove_payment_info", description="Elimina la información de un método de pago")
    @is_owner()
    async def remove_payment_info(interaction: discord.Interaction, method: str):
        logger.info(f"Owner {interaction.user.name} (ID: {interaction.user.id}) está intentando eliminar información de pago para el método {method}")
        data = load_data()
        if "payment_info" not in data or method not in data["payment_info"]:
            logger.warning(f"Intento de eliminar método de pago inexistente: {method}")
            await interaction.response.send_message(f"No hay información de pago para '{method}'.", ephemeral=True)
            return
        
        del data["payment_info"][method]
        save_data(data)
        logger.info(f"Información de pago eliminada exitosamente para el método {method}")
        await interaction.response.send_message(f"Información de pago para '{method}' eliminada.", ephemeral=True)

    @tree.command(name="help", description="Muestra todos los comandos")
    async def help(interaction: discord.Interaction):
        logger.info(f"Usuario {interaction.user.name} (ID: {interaction.user.id}) solicitó ayuda con los comandos")
        message = """
        === Comandos del Bot ===
        **Usuarios:**
        /products - Muestra los productos disponibles.
        /ticket - Abre un ticket para comprar un producto.
        /ver-tienda - Muestra los regalos disponibles de la tienda de Fortnite.
        /pago - Muestra la información de pago para los métodos disponibles.
        @AssistantMid para responder tus dudas.
        **Owners:**
        /add-product [name] [price] [description] - Añade un producto.
        /edit-product [product_id] [name|price|description] - Edita un producto.
        /delete-product [product_id] - Elimina un producto.
        /close - Cierra el ticket (en el canal del ticket).
        /ticket-panel - Crea un panel para abrir tickets.
        /add-payment-info [method] [info] - Añade o actualiza la información de un método de pago.
        /remove-payment-info [method] - Elimina la información de un método de pago.
        /sync - Sincroniza manualmente los comandos del bot (Owner only).
        **General:**
        /help - Este mensaje.
        """
        await interaction.response.send_message(message, ephemeral=True)