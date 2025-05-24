import discord
from discord import app_commands
import asyncio
from datetime import datetime

import logging
from data_manager import load_data, save_data, TICKET_COUNTER
from views.enhanced_product_view import EnhancedProductView
from views.enhanced_ticket_view import EnhancedTicketView
from views.shop_view import ShopView
from utils import sync_fortnite_shop, cache_fortnite_shop
from config import TICKET_CHANNEL_ID, OWNER_ROLE_ID

# Configuración del logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

def setup(tree: app_commands.CommandTree, client: discord.Client):
    @tree.command(name="products", description="Muestra los productos disponibles")
    async def products(interaction: discord.Interaction):
        data = load_data()
        products = list(data["products"].items())
        items_per_page = 24
        pages = [products[i:i + items_per_page] for i in range(0, len(products), items_per_page)] if products else [[]]
        
        view = EnhancedProductView(products, pages)
        await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)

    @tree.command(name="ticket", description="Abre un ticket para comprar un producto")
    async def ticket(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = load_data()
        user_id = str(interaction.user.id)
        
        # Verificar si ya tiene un ticket abierto
        for ticket_id, ticket in data["tickets"].items():
            if ticket["user_id"] == user_id and ticket["status"] == "abierto":
                await interaction.followup.send("Ya tienes un ticket abierto. Por favor, espera a que se resuelva.", ephemeral=True)
                return
        
        if not data["products"]:
            await interaction.followup.send("No hay productos disponibles. Contacta a un Owner.", ephemeral=True)
            return
        
        # Mostrar productos con vista mejorada
        items_per_page = 24
        products = list(data["products"].items())
        pages = [products[i:i + items_per_page] for i in range(0, len(products), items_per_page)]
        view = EnhancedProductView(products, pages)
        embed = view.create_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
        try:
            # Cargar datos y actualizar contador de tickets
            data = load_data()
            global TICKET_COUNTER
            TICKET_COUNTER = data.get("ticket_counter", 0) + 1
            ticket_id = f"ticket-{TICKET_COUNTER:04d}"
            data["ticket_counter"] = TICKET_COUNTER
            save_data(data)
            
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
            }
            
            owner_role = interaction.guild.get_role(OWNER_ROLE_ID)
            if owner_role:
                overwrites[owner_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
            
            guild = interaction.guild
            category = None
            ticket_channel = guild.get_channel(TICKET_CHANNEL_ID)
            if isinstance(ticket_channel, discord.CategoryChannel):
                category = ticket_channel
            elif ticket_channel:
                category = ticket_channel.category
            
            channel = await guild.create_text_channel(
                name=ticket_id,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket de {interaction.user.name} (ID: {ticket_id})"
            )
            
            data["tickets"][ticket_id] = {
                "user_id": user_id,
                "channel_id": str(channel.id),
                "details": details,
                "payment_method": payment_view.payment_method,
                "status": "abierto",
                "estado_detallado": "esperando_revision",
                "timestamp": datetime.utcnow().isoformat(),
                "historial": [{
                    "estado": "creado",
                    "timestamp": datetime.utcnow().isoformat(),
                    "detalles": "Ticket creado por el usuario"
                }]
            }
            save_data(data)
            
            embed = discord.Embed(
                title=f"🎟️ Ticket #{ticket_id}",
                color=0xA100F2
            )
            embed.add_field(name="Usuario", value=f"<@{user_id}>", inline=True)
            embed.add_field(name="Producto", value=f"{details['name']} (ID: {details['product_id']})\nPrecio: ${details['price']:.2f} MXN", inline=True)
            embed.add_field(name="Método de Pago", value=payment_view.payment_method, inline=True)
            embed.set_footer(text=f"Creado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
            await channel.send(f"<@&{OWNER_ROLE_ID}> Nuevo ticket creado:", embed=embed)
            
            await interaction.followup.send(f"Ticket #{ticket_id} creado en {channel.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("Error: No tengo permisos para crear el canal de ticket. Asegúrate de que tenga permisos para gestionar canales.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error al crear el ticket: {str(e)}", ephemeral=True)

    @tree.command(name="ver_tienda", description="Muestra los regalos disponibles de la tienda de Fortnite")
    async def ver_tienda(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            # Intentar usar caché primero
            data = load_data()
            cached_data = cache_fortnite_shop()
            
            if cached_data:
                logger.info("Usando datos en caché de la tienda de Fortnite")
                data["gifts"].update(cached_data)
                sync_success = True
            else:
                logger.info("Sincronizando datos frescos de la tienda de Fortnite")
                sync_success = sync_fortnite_shop()
            data = load_data()
            
            if not data or not isinstance(data, dict):
                await interaction.followup.send("Error al cargar los datos de la tienda. Por favor, intenta más tarde.", ephemeral=True)
                return
            
            # Asegurarse de que data tenga la estructura correcta
            if "shop" not in data:
                data["shop"] = {}
            if "gifts" not in data:
                data["gifts"] = {}
                save_data(data)
            
            gifts = data["gifts"]
            if not gifts:
                await interaction.followup.send("La tienda está vacía. Contacta a un Owner para añadir ítems manualmente.", ephemeral=True)
                return
            
            items_per_page = 24
            gifts_list = list(gifts.items())
            # Asegurarse de que la lista no esté vacía y manejar la paginación de forma segura
            if not gifts_list:
                pages = [[]]  # Si no hay regalos, crear una página vacía
            else:
                pages = [gifts_list[i:i + items_per_page] for i in range(0, len(gifts_list), items_per_page)]
            last_updated = data.get("shop", {}).get("last_updated", "Desconocida")
            
            view = ShopView(gifts_list, last_updated, sync_success, pages)
            await interaction.followup.send(embed=view.create_embed(), view=view, ephemeral=True)
        except Exception as e:
            print(f"Error en el comando ver_tienda: {str(e)}")
            await interaction.followup.send("Ocurrió un error al mostrar la tienda. Por favor, intenta más tarde.", ephemeral=True)