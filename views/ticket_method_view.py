import discord

class PaymentMethodView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.payment_method = None

    @discord.ui.button(label="PayPal", style=discord.ButtonStyle.gray)
    async def paypal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Solo el creador del ticket puede usar estos botones.", ephemeral=True)
            return
        self.payment_method = "PayPal"
        await interaction.response.send_message("Método de pago seleccionado: PayPal", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Tarjeta", style=discord.ButtonStyle.gray)
    async def card_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Solo el creador del ticket puede usar estos botones.", ephemeral=True)
            return
        self.payment_method = "Tarjeta"
        await interaction.response.send_message("Método de pago seleccionado: Tarjeta", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Transferencia", style=discord.ButtonStyle.gray)
    async def transfer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Solo el creador del ticket puede usar estos botones.", ephemeral=True)
            return
        self.payment_method = "Transferencia"
        await interaction.response.send_message("Método de pago seleccionado: Transferencia", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Depósito Oxxo", style=discord.ButtonStyle.gray)
    async def oxxo_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Solo el creador del ticket puede usar estos botones.", ephemeral=True)
            return
        self.payment_method = "Depósito Oxxo"
        await interaction.response.send_message("Método de pago seleccionado: Depósito Oxxo", ephemeral=True)
        self.stop()