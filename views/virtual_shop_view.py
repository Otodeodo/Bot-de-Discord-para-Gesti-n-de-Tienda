import discord
from discord import ui
from typing import List, Dict, Tuple, Optional
from virtual_shop import virtual_shop
from economy_system import economy
import math

class VirtualShopView(discord.ui.View):
    def __init__(self, user_id: str, page: int = 0):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.page = page
        self.items_per_page = 5
        
        # Obtener productos
        self.products = virtual_shop.get_products_by_category()
        self.total_pages = max(1, math.ceil(len(self.products) / self.items_per_page))
        
        # Ajustar página si está fuera de rango
        if self.page >= self.total_pages:
            self.page = 0
        
        self.update_buttons()
    
    def get_current_products(self) -> List[Tuple[str, Dict]]:
        """Obtiene los productos de la página actual"""
        start_idx = self.page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return self.products[start_idx:end_idx]
    
    def create_embed(self) -> discord.Embed:
        """Crea el embed de la tienda virtual"""
        user_economy = economy.get_user_economy(self.user_id)
        
        title = "🛒 Tienda Virtual GameCoins"
        description = "Compra productos virtuales con tus GameCoins"
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x00ff88
        )
        
        # Mostrar balance del usuario
        embed.add_field(
            name="💰 Tu Balance",
            value=f"{user_economy['coins']:,} GameCoins",
            inline=True
        )
        
        # Mostrar información de página
        if self.total_pages > 1:
            embed.add_field(
                name="📄 Página",
                value=f"{self.page + 1}/{self.total_pages}",
                inline=True
            )
        
        embed.add_field(
            name="📊 Total Productos",
            value=f"{len(self.products)} disponibles",
            inline=True
        )
        
        # Mostrar productos de la página actual
        current_products = self.get_current_products()
        
        if not current_products:
            embed.add_field(
                name="❌ Sin Productos",
                value="No hay productos disponibles en esta categoría.",
                inline=False
            )
        else:
            for i, (product_id, product) in enumerate(current_products, 1):
                # Crear descripción del producto
                product_desc = product['description']
                
                # Añadir información específica según el tipo
                if product.get('role_id'):
                    product_desc += f"\n🎭 Rol: <@&{product['role_id']}>"
                
                if product.get('duration_days'):
                    product_desc += f"\n⏰ Duración: {product['duration_days']} días"
                
                if product.get('multiplier'):
                    product_desc += f"\n🚀 Multiplicador: x{product['multiplier']}"
                
                embed.add_field(
                    name=f"📦 {product['name']}",
                    value=f"{product_desc}\n\n💰 **{product['price']:,} GameCoins**",
                    inline=False
                )
        
        embed.set_footer(text="Usa los botones para navegar y comprar productos")
        return embed
    
    def update_buttons(self):
        """Actualiza los botones según el estado actual"""
        self.clear_items()
        
        # Botones de navegación
        if self.total_pages > 1:
            if self.page > 0:
                prev_button = discord.ui.Button(
                    label="◀️ Anterior",
                    style=discord.ButtonStyle.secondary,
                    custom_id="prev_page"
                )
                prev_button.callback = self.previous_page
                self.add_item(prev_button)
            
            if self.page < self.total_pages - 1:
                next_button = discord.ui.Button(
                    label="Siguiente ▶️",
                    style=discord.ButtonStyle.secondary,
                    custom_id="next_page"
                )
                next_button.callback = self.next_page
                self.add_item(next_button)
        
        # Selector de productos para comprar
        current_products = self.get_current_products()
        if current_products:
            product_select = ProductSelect(self.user_id, current_products)
            self.add_item(product_select)
        
        # Botón de inventario
        inventory_button = discord.ui.Button(
            label="🎒 Mi Inventario",
            style=discord.ButtonStyle.primary,
            custom_id="view_inventory"
        )
        inventory_button.callback = self.view_inventory
        self.add_item(inventory_button)
        
        # Botón de actualizar
        refresh_button = discord.ui.Button(
            label="🔄 Actualizar",
            style=discord.ButtonStyle.secondary,
            custom_id="refresh"
        )
        refresh_button.callback = self.refresh
        self.add_item(refresh_button)
    
    async def previous_page(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Solo quien abrió la tienda puede navegar.", ephemeral=True)
            return
        
        self.page = max(0, self.page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Solo quien abrió la tienda puede navegar.", ephemeral=True)
            return
        
        self.page = min(self.total_pages - 1, self.page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    

    
    async def view_inventory(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Solo puedes ver tu propio inventario.", ephemeral=True)
            return
        
        inventory_view = InventoryView(self.user_id)
        await interaction.response.send_message(embed=inventory_view.create_embed(), view=inventory_view, ephemeral=True)
    
    async def refresh(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Solo quien abrió la tienda puede actualizar.", ephemeral=True)
            return
        
        # Recrear la vista con datos actualizados
        new_view = VirtualShopView(self.user_id, self.page)
        await interaction.response.edit_message(embed=new_view.create_embed(), view=new_view)



class ProductSelect(discord.ui.Select):
    def __init__(self, user_id: str, products: List[Tuple[str, Dict]]):
        self.user_id = user_id
        self.products = {product_id: product for product_id, product in products}
        
        options = []
        for product_id, product in products:
            # Verificar si el usuario puede comprar el producto
            user_economy = economy.get_user_economy(user_id)
            can_afford = user_economy["coins"] >= product["price"]
            
            label = product["name"]
            if not can_afford:
                label += " (Sin GameCoins)"
            
            options.append(
                discord.SelectOption(
                    label=label[:100],  # Límite de Discord
                    description=f"{product['price']:,} GameCoins - {product['description'][:50]}...",
                    value=product_id,
                    emoji="💰" if can_afford else "❌"
                )
            )
        
        super().__init__(
            placeholder="Selecciona un producto para comprar...",
            options=options,
            custom_id="product_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Solo quien abrió la tienda puede comprar productos.", ephemeral=True)
            return
        
        product_id = self.values[0]
        product = self.products[product_id]
        
        # Crear modal de confirmación
        modal = PurchaseConfirmModal(self.user_id, product_id, product)
        await interaction.response.send_modal(modal)

class PurchaseConfirmModal(discord.ui.Modal):
    def __init__(self, user_id: str, product_id: str, product: Dict):
        self.user_id = user_id
        self.product_id = product_id
        self.product = product
        
        super().__init__(title=f"Confirmar Compra: {product['name']}")
        
        self.confirmation = discord.ui.TextInput(
            label="Confirma escribiendo 'COMPRAR'",
            placeholder="Escribe COMPRAR para confirmar la compra",
            required=True,
            max_length=10
        )
        self.add_item(self.confirmation)
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.confirmation.value.upper() != "COMPRAR":
            await interaction.response.send_message("❌ Compra cancelada. Debes escribir 'COMPRAR' para confirmar.", ephemeral=True)
            return
        
        # Realizar la compra
        result = virtual_shop.purchase_virtual_product(self.user_id, self.product_id)
        
        if result["success"]:
            embed = discord.Embed(
                title="✅ Compra Exitosa",
                description=f"Has comprado **{self.product['name']}** exitosamente!",
                color=0x00ff88
            )
            embed.add_field(
                name="💰 Precio Pagado",
                value=f"{self.product['price']:,} GameCoins",
                inline=True
            )
            embed.add_field(
                name="💳 Nuevo Balance",
                value=f"{result['new_balance']:,} GameCoins",
                inline=True
            )
            
            if self.product.get('duration_days'):
                embed.add_field(
                    name="⏰ Duración",
                    value=f"{self.product['duration_days']} días",
                    inline=True
                )
            
            embed.set_footer(text="¡Gracias por tu compra! Revisa tu inventario para ver tus productos.")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="❌ Error en la Compra",
                description=result["error"],
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class InventoryView(discord.ui.View):
    def __init__(self, user_id: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.purchases = virtual_shop.get_user_purchases(user_id)
    
    def create_embed(self) -> discord.Embed:
        """Crea el embed del inventario"""
        embed = discord.Embed(
            title="🎒 Mi Inventario Virtual",
            description="Tus productos comprados con GameCoins",
            color=0x9932cc
        )
        
        if not self.purchases:
            embed.add_field(
                name="📦 Inventario Vacío",
                value="No has comprado ningún producto virtual aún.\nVisita la tienda para comprar productos con GameCoins.",
                inline=False
            )
        else:
            active_purchases = [p for p in self.purchases if p.get('active', True)]
            expired_purchases = [p for p in self.purchases if not p.get('active', True)]
            
            if active_purchases:
                embed.add_field(
                    name="✅ Productos Activos",
                    value=f"Tienes {len(active_purchases)} productos activos",
                    inline=True
                )
                
                for purchase in active_purchases[:5]:  # Mostrar máximo 5
                    value = f"💰 Pagado: {purchase['price_paid']:,} GameCoins"
                    if 'expires_at' in purchase:
                        from datetime import datetime
                        expiry = datetime.fromisoformat(purchase['expires_at'])
                        value += f"\n⏰ Expira: {expiry.strftime('%d/%m/%Y %H:%M')}"
                    
                    embed.add_field(
                        name=f"📦 {purchase['product_name']}",
                        value=value,
                        inline=False
                    )
            
            if expired_purchases:
                embed.add_field(
                    name="⏰ Productos Expirados",
                    value=f"Tienes {len(expired_purchases)} productos expirados",
                    inline=True
                )
        
        total_spent = sum(p['price_paid'] for p in self.purchases)
        embed.add_field(
            name="💸 Total Gastado",
            value=f"{total_spent:,} GameCoins",
            inline=True
        )
        
        embed.set_footer(text="Los productos temporales expiran automáticamente")
        return embed