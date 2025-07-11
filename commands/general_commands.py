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

    @tree.command(name="help", description="📚 Muestra todos los comandos disponibles")
    async def help(interaction: discord.Interaction):
        logger.info(f"Usuario {interaction.user.name} (ID: {interaction.user.id}) solicitó ayuda con los comandos")
        
        # Embed principal con todos los comandos organizados
        embed = discord.Embed(
            title="📚 Centro de Ayuda - GameMid",
            description="**¡Todos los comandos disponibles organizados por categorías!**\n*GameMid v2.0 - 34 comandos activos*",
            color=0xffd700
        )
        
        # Economía Virtual
        embed.add_field(
            name="🪙 **ECONOMÍA VIRTUAL**",
            value="**💰 Personal:** `/balance` `/daily` `/jobs`\n**⚒️ Trabajo:** `/work` `/apply_job` `/claim_task`\n**🎮 Juegos:** `/games` `/coinflip` `/dice` `/slots` `/blackjack` (interactivo) `/ruleta`\n**🏆 Social:** `/transfer` `/leaderboard`\n**🛒 Tienda:** `/tienda_virtual` `/mis_compras`",
            inline=True
        )
        
        # Tienda y Productos
        embed.add_field(
            name="🛒 **TIENDA & PRODUCTOS**",
            value="**👥 Usuario:** `/products` `/ticket` `/pago`\n**👑 Admin:** `/add-product` `/edit-product` `/delete-product` `/close` `/ticket-panel`\n**💳 Pagos:** `/add-payment-info` `/remove-payment-info`",
            inline=True
        )
        

        
        # Comandos Generales
        embed.add_field(
            name="⚙️ **COMANDOS GENERALES**",
            value="**📚 Ayuda:** `/help`\n**🔍 Info:** Comandos de información\n**🛠️ Utilidades:** Herramientas varias",
            inline=True
        )
        
        # Características destacadas
        embed.add_field(
            name="✨ **CARACTERÍSTICAS DESTACADAS**",
            value="🪙 **Sistema de GameCoins** completo\n🎮 **Minijuegos** interactivos\n🎫 **Sistema de tickets** automático\n📊 **Rankings** y estadísticas\n⏰ **Recordatorios** personalizados",
            inline=True
        )
        
        # Enlaces y documentación
        embed.add_field(
            name="📖 **DOCUMENTACIÓN**",
            value="📋 [Economía Virtual](https://github.com/tu-repo/ECONOMIA_VIRTUAL.md)\n⏰ [Sistema Recordatorios](https://github.com/tu-repo/REMINDER_SYSTEM.md)",
            inline=True
        )
        
        # Comandos de Owner (solo visible para owners)
        from utils import OWNER_IDS
        if str(interaction.user.id) in OWNER_IDS:
            embed.add_field(
                name="👑 Comandos de Owner",
                value="`/add_gamecoins` - Añadir GameCoins a un usuario\n"
                      "`/remove_gamecoins` - Quitar GameCoins a un usuario\n"
                      "`/set_gamecoins` - Establecer GameCoins de un usuario\n"
                      "`/reset_daily` - Resetear daily de un usuario\n"
                      "`/backup_data` - Crear respaldo de datos\n"
                      "`/restore_data` - Restaurar datos desde respaldo\n"
                      "`/clear_data` - Limpiar datos de usuario\n"
                      "`/bot_stats` - Estadísticas del bot",
                inline=False
            )
            
            embed.add_field(
                name="🛒 Gestión de Tienda Virtual",
                value="`/añadir_producto_virtual` - Añadir producto\n"
                      "`/editar_producto_virtual` - Editar producto\n"
                      "`/eliminar_producto_virtual` - Eliminar producto\n"
                      "`/listar_productos_virtuales` - Ver todos los productos\n"
                      "`/gestionar_tienda_virtual` - Panel de gestión",
                inline=False
            )
        
        embed.set_footer(text="💡 GameMid - Tu asistente completo para Discord | Desarrollado con ❤️")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1234567890/gamemid-logo.png")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)