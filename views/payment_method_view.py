import discord

class PaymentMethodView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)  # 2 minutos de timeout
        self.user_id = user_id
        self.payment_method = None

    @discord.ui.button(label="💳 Tarjeta", style=discord.ButtonStyle.primary, custom_id="card_payment")
    async def card_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != str(self.user_id):
            await interaction.response.send_message("No puedes usar este botón.", ephemeral=True)
            return
        
        self.payment_method = "Tarjeta"
        await interaction.response.send_message("Has seleccionado pago con Tarjeta.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="💸 Efectivo", style=discord.ButtonStyle.success, custom_id="cash_payment")
    async def cash_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != str(self.user_id):
            await interaction.response.send_message("No puedes usar este botón.", ephemeral=True)
            return
        
        self.payment_method = "Efectivo"
        await interaction.response.send_message("Has seleccionado pago en Efectivo.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="🏦 Transferencia", style=discord.ButtonStyle.secondary, custom_id="transfer_payment")
    async def transfer_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != str(self.user_id):
            await interaction.response.send_message("No puedes usar este botón.", ephemeral=True)
            return
        
        self.payment_method = "Transferencia"
        await interaction.response.send_message("Has seleccionado pago por Transferencia.", ephemeral=True)
        self.stop()