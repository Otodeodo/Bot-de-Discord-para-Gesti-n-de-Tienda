import discord

class ProductView(discord.ui.View):
    def __init__(self, products, pages, current_page=0):
        super().__init__(timeout=120)
        self.products = products
        self.pages = pages
        self.current_page = current_page
        self.update_buttons()

    def create_embed(self):
        embed = discord.Embed(
            title="📋 Lista de Productos",
            description=f"Mostrando {len(self.pages[self.current_page])} de {len(self.products)} productos",
            color=0xA100F2
        )
        
        # Add products from the current page
        for product_id, product in self.pages[self.current_page]:
            embed.add_field(
                name=f"{product['name']} (ID: ||{product_id}||)",
                value=f"💰 Precio: ${product['price']:.2f} MXN\n📝 Descripción: {product.get('description', 'Sin descripción')}",
                inline=True
            )
        
        embed.set_footer(text=f"Página {self.current_page + 1}/{len(self.pages)}")
        return embed

    def update_buttons(self):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Siguiente ➡️", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)