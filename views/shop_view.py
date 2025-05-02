import discord

class ShopView(discord.ui.View):
    def __init__(self, gifts, last_updated, sync_success, pages, current_page=0):
        super().__init__(timeout=60)
        self.gifts = gifts
        self.last_updated = last_updated
        self.sync_success = sync_success
        self.pages = pages
        self.current_page = current_page
        self.update_buttons()

    def create_embed(self):
        embed = discord.Embed(
            title="🛒 Tienda de Regalos (Fortnite)",
            description=f"Mostrando {len(self.pages[self.current_page])} de {len(self.gifts)} ítems",
            color=0xA100F2
        )
        for gift_id, gift in self.pages[self.current_page]:
            source = " (API)" if gift.get("source") == "fortnite_api" else " (Manual)"
            embed.add_field(
                name=f"{gift['name']}{source} (ID: {gift_id})",
                value=f"Precio: {gift['price']} V-Bucks\n[Ver Imagen]({gift['image_url']})",
                inline=True
            )
        
        embed.set_footer(text=f"Página {self.current_page + 1}/{len(self.pages)} | Última actualización: {self.last_updated}")
        if not self.sync_success:
            embed.add_field(
                name="⚠️ Aviso",
                value="No se pudo sincronizar con la tienda de Fortnite. Mostrando ítems manuales o datos previos.",
                inline=False
            )
        
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