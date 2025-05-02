import discord
from discord import app_commands
import asyncio
from datetime import datetime

from data_manager import load_data, save_data, TICKET_COUNTER
from views.product_view import ProductView
from views.payment_method_view import PaymentMethodView
from views.shop_view import ShopView
from utils import sync_fortnite_shop
from config import TICKET_CHANNEL_ID, OWNER_ROLE_ID

def setup(tree: app_commands.CommandTree, client: discord.Client):
    @tree.command(name="products", description="Muestra los productos disponibles")
    async def products(interaction: discord.Interaction):
        data = load_data()
        products = list(data["products"].items())
        items_per_page = 24
        pages = [products[i:i + items_per_page] for i in range(0, len(products), items_per_page)] if products else [[]]
        
        view = ProductView(products, pages)
        await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)

    @tree.command(name="ticket", description="Abre un ticket para comprar un producto")
    async def ticket(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = load_data()
        user_id = str(interaction.user.id)
        
        for ticket_id, ticket in data["tickets"].items():
            if ticket["user_id"] == user_id and ticket["status"] == "abierto":
                await interaction.followup.send("Ya tienes un ticket abierto. Por favor, espera a que se resuelva.", ephemeral=True)
                return
        
        if not data["products"]:
            await interaction.followup.send("No hay productos disponibles. Contacta a un Owner.", ephemeral=True)
            return
        
        items_per_page = 24
        products = list(data["products"].items())
        pages = [products[i:i + items_per_page] for i in range(0, len(products), items_per_page)]
        view = ProductView(products, pages)
        embed = view.create_embed()
        embed.description += "\n\nPor favor, ingresa el **nombre del producto** que deseas comprar (por ejemplo, `crunchyroll`). Si hay productos con nombres similares, te pediremos que uses el ID para confirmar:"
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        try:
            message = await client.wait_for(
                "message",
                check=lambda m: m.author.id == interaction.user.id and m.channel.id == interaction.channel.id,
                timeout=120
            )
        except asyncio.TimeoutError:
            await interaction.followup.send("Tiempo agotado para seleccionar el producto.", ephemeral=True)
            return
        
        product_name = message.content.strip().lower()
        matching_products = [(pid, prod) for pid, prod in data["products"].items() if prod["name"].lower() == product_name]

        if not matching_products:
            await interaction.followup.send("No se encontró un producto con ese nombre. Usa /products para ver la lista de productos.", ephemeral=True)
            return
        
        if len(matching_products) > 1:
            embed = discord.Embed(
                title="⚠️ Múltiples Productos Encontrados",
                description="Se encontraron varios productos con ese nombre. Por favor, ingresa el **ID** del producto que deseas (copia y pega el ID):",
                color=0xA100F2
            )
            for product_id, product in matching_products:
                embed.add_field(
                    name=f"{product['name']} (ID: {product_id})",
                    value=f"Precio: ${product['price']:.2f} MXN\nDescripción: {product['description']}",
                    inline=True
                )
            await interaction.followup.send(embed=embed, ephemeral=True)

            try:
                message = await client.wait_for(
                    "message",
                    check=lambda m: m.author.id == interaction.user.id and m.channel.id == interaction.channel.id,
                    timeout=120
                )
            except asyncio.TimeoutError:
                await interaction.followup.send("Tiempo agotado para seleccionar el producto.", ephemeral=True)
                return
            
            product_id = message.content.strip()
            if product_id not in data["products"]:
                await interaction.followup.send("El ID del producto no es válido. Usa /products para ver los IDs.", ephemeral=True)
                return
        else:
            product_id, _ = matching_products[0]

        product = data["products"][product_id]
        details = {"product_id": product_id, "name": product["name"], "price": product["price"]}

        embed = discord.Embed(
            title="💳 Seleccionar Método de Pago",
            description="Elige tu método de pago preferido:",
            color=0xA100F2
        )
        payment_view = PaymentMethodView(interaction.user.id)
        await interaction.followup.send(embed=embed, view=payment_view, ephemeral=True)
        
        await payment_view.wait()
        if payment_view.payment_method is None:
            await interaction.followup.send("No se seleccionó un método de pago. Ticket cancelado.", ephemeral=True)
            return
        
        try:
            global TICKET_COUNTER
            TICKET_COUNTER += 1
            ticket_id = f"ticket-{TICKET_COUNTER:04d}"
            
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
                "timestamp": datetime.utcnow().isoformat()
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
        sync_success = sync_fortnite_shop()
        data = load_data()
        
        if not data["gifts"]:
            await interaction.followup.send("La tienda está vacía. Contacta a un Owner para añadir ítems manualmente.", ephemeral=True)
            return
        
        items_per_page = 24
        gifts = list(data["gifts"].items())
        pages = [gifts[i:i + items_per_page] for i in range(0, len(gifts), items_per_page)]
        last_updated = data["shop"].get("last_updated", "Desconocida")
        
        view = ShopView(gifts, last_updated, sync_success, pages)
        await interaction.followup.send(embed=view.create_embed(), view=view, ephemeral=True)