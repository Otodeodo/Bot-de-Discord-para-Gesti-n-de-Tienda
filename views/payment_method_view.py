import discord
from utils import check_user_permissions, handle_interaction_response, logger

class PaymentMethodView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)  # 2 minutos de timeout
        self.user_id = user_id
        self.payment_method = None
        logger.info(f'Vista de método de pago creada para usuario {user_id}')

    @discord.ui.button(label="💳 Tarjeta", style=discord.ButtonStyle.primary, custom_id="card_payment")
    async def card_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_user_permissions(interaction.user.id, self.user_id):
            await handle_interaction_response(interaction, "No puedes usar este botón.")
            return
        
        self.payment_method = "Tarjeta"
        await handle_interaction_response(interaction, "Has seleccionado pago con Tarjeta.")
        logger.info(f'Usuario {self.user_id} seleccionó método de pago: Tarjeta')
        self.stop()

    @discord.ui.button(label="💸 OXXO", style=discord.ButtonStyle.success, custom_id="cash_payment")
    async def cash_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_user_permissions(interaction.user.id, self.user_id):
            await handle_interaction_response(interaction, "No puedes usar este botón.")
            return
        
        self.payment_method = "Efectivo"
        await handle_interaction_response(interaction, "Has seleccionado pago en OXXO.")
        logger.info(f'Usuario {self.user_id} seleccionó método de pago: OXXO')
        self.stop()

    @discord.ui.button(label="🏦 Transferencia", style=discord.ButtonStyle.secondary, custom_id="transfer_payment")
    async def transfer_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_user_permissions(interaction.user.id, self.user_id):
            await handle_interaction_response(interaction, "No puedes usar este botón.")
            return
        
        self.payment_method = "Transferencia"
        await handle_interaction_response(interaction, "Has seleccionado pago por Transferencia.")
        logger.info(f'Usuario {self.user_id} seleccionó método de pago: Transferencia')
        self.stop()