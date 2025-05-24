import discord
from typing import Optional
from datetime import datetime
import uuid
from utils import check_user_permissions, handle_interaction_response, logger
from data_manager import load_data, save_data
from config import TICKET_CHANNEL_ID, OWNER_ROLE_ID

class EnhancedTicketView(discord.ui.View):
    payment_emojis = {
        "Paypal": "💳",
        "OXXO": "💸",
        "Transferencia": "🏦"
    }

    def __init__(self, user_id: str, product_id: Optional[str] = None, product_name: Optional[str] = None):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.user_id = user_id
        self.product_id = product_id
        self.product_name = product_name
        self.payment_method = None
        self.confirmed = False
        logger.info(f'Vista de ticket mejorada creada para usuario {user_id}')

    def create_confirmation_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🌟 Confirmación de Ticket",
            description="**Por favor, verifica los detalles de tu ticket:**\n━━━━━━━━━━━━━━━━━━━━━━━━",
            color=0xA100F2,
            timestamp=datetime.utcnow()
        )

        if self.product_name and self.product_id:
            embed.add_field(
                name="📦 Producto Seleccionado",
                value=f"```\n🏷️ {self.product_name}\n🔑 ID: {self.product_id}```",
                inline=False
            )

        if self.payment_method:
            emoji = self.payment_emojis.get(self.payment_method, "💰")
            embed.add_field(
                name="💳 Método de Pago Seleccionado",
                value=f"```\n{emoji} {self.payment_method}```",
                inline=False
            )

        status = "✅ Listo para crear" if self.payment_method else "⏳ Pendiente de método de pago"
        embed.add_field(
            name="📋 Estado del Ticket",
            value=f"```\n{status}```",
            inline=False
        )
        
        embed.set_footer(text="• Selecciona un método de pago y confirma para crear el ticket •")
        return embed

    @discord.ui.button(label="💳 Paypal", style=discord.ButtonStyle.primary, row=0)
    async def card_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_user_permissions(interaction.user.id, self.user_id):
            await handle_interaction_response(interaction, "No puedes usar este botón.")
            return

        self.payment_method = "Paypal"
        await interaction.response.edit_message(embed=self.create_confirmation_embed(), view=self)

    @discord.ui.button(label="💸 OXXO", style=discord.ButtonStyle.success, row=0)
    async def oxxo_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_user_permissions(interaction.user.id, self.user_id):
            await handle_interaction_response(interaction, "No puedes usar este botón.")
            return

        self.payment_method = "OXXO"
        await interaction.response.edit_message(embed=self.create_confirmation_embed(), view=self)

    @discord.ui.button(label="🏦 Transferencia", style=discord.ButtonStyle.secondary, row=0)
    async def transfer_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_user_permissions(interaction.user.id, self.user_id):
            await handle_interaction_response(interaction, "No puedes usar este botón.")
            return

        self.payment_method = "Transferencia"
        await interaction.response.edit_message(embed=self.create_confirmation_embed(), view=self)

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success, row=1)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_user_permissions(interaction.user.id, self.user_id):
            await handle_interaction_response(interaction, "No puedes usar este botón.")
            return

        if not self.payment_method:
            await interaction.response.send_message(
                "❌ Por favor, selecciona un método de pago antes de confirmar.",
                ephemeral=True
            )
            return

        try:
            # Crear el ticket en el canal apropiado
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
            }
            
            owner_role = interaction.guild.get_role(OWNER_ROLE_ID)
            if owner_role:
                overwrites[owner_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
            
            # Obtener o crear el canal del ticket
            guild = interaction.guild
            category = None
            ticket_channel = guild.get_channel(TICKET_CHANNEL_ID)
            if isinstance(ticket_channel, discord.CategoryChannel):
                category = ticket_channel
            elif ticket_channel:
                category = ticket_channel.category

            # Generar ID único para el ticket
            ticket_id = f"ticket-{uuid.uuid4().hex[:8]}"
            
            # Crear el canal del ticket
            channel = await guild.create_text_channel(
                name=ticket_id,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket de {interaction.user.name} (ID: {ticket_id})"
            )
            
            # Guardar la información del ticket
            data = load_data()
            data["tickets"][ticket_id] = {
                "user_id": str(interaction.user.id),
                "channel_id": str(channel.id),
                "product_id": self.product_id,
                "product_name": self.product_name,
                "payment_method": self.payment_method,
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
            
            # Actualizar la vista
            self.confirmed = True
            for child in self.children:
                child.disabled = True

            embed = discord.Embed(
                title="✅ Ticket Creado",
                description=f"Tu ticket ha sido creado exitosamente en {channel.mention}.",
                color=0x00FF00
            )
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Enviar mensaje inicial en el canal del ticket
            ticket_embed = discord.Embed(
                title=f"🌟 Nuevo Ticket | {ticket_id}",
                description=f"¡Hola <@&{OWNER_ROLE_ID}>! Un nuevo ticket requiere tu atención.",
                color=0xA100F2,
                timestamp=datetime.utcnow()
            )
            ticket_embed.add_field(
                name="👤 Cliente",
                value=f"{interaction.user.mention}\nID: `{interaction.user.id}`",
                inline=True
            )
            ticket_embed.add_field(
                name="📦 Producto",
                value=f"**{self.product_name}**\nID: `{self.product_id}`",
                inline=True
            )
            ticket_embed.add_field(
                name="💳 Método de Pago",
                value=f"{self.payment_emojis.get(self.payment_method, '💰')} **{self.payment_method}**",
                inline=True
            )
            ticket_embed.add_field(
                name="📋 Estado Actual",
                value="🔍 Esperando revisión del owner",
                inline=False
            )
            ticket_embed.set_footer(text=f"Ticket ID: {ticket_id} • Creado")
            # Crear y enviar la vista de gestión del ticket
            from views.ticket_management_view import TicketManagementView
            management_view = TicketManagementView(ticket_id)
            await channel.send(f"<@&{OWNER_ROLE_ID}>", embed=ticket_embed, view=management_view)
            
            logger.info(f'Ticket {ticket_id} creado para usuario {interaction.user.id}')
            
        except Exception as e:
            logger.error(f'Error al crear ticket: {str(e)}')
            await interaction.response.send_message(
                "❌ Hubo un error al crear el ticket. Por favor, contacta a un owner.",
                ephemeral=True
            )
            return
        
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger, row=1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_user_permissions(interaction.user.id, self.user_id):
            await handle_interaction_response(interaction, "No puedes usar este botón.")
            return

        embed = discord.Embed(
            title="❌ Ticket Cancelado",
            description="Has cancelado la creación del ticket.",
            color=0xFF0000
        )
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()