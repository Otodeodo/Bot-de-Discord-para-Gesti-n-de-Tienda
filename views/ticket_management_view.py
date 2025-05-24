import discord
import asyncio
from datetime import datetime
from utils import check_user_permissions, handle_interaction_response, logger
from data_manager import load_data, save_data
from config import OWNER_ROLE_ID

class TicketManagementView(discord.ui.View):
    def __init__(self, ticket_id: str):
        super().__init__(timeout=None)  # Sin timeout para botones persistentes
        self.ticket_id = ticket_id

    @discord.ui.button(label="🔒 Cerrar Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificar si el usuario tiene el rol de owner
        if not interaction.user.get_role(OWNER_ROLE_ID):
            await handle_interaction_response(interaction, "❌ Solo los owners pueden cerrar tickets.")
            return

        try:
            # Cargar datos del ticket
            data = load_data()
            if self.ticket_id not in data["tickets"]:
                await handle_interaction_response(interaction, "❌ No se encontró el ticket.")
                return

            ticket_data = data["tickets"][self.ticket_id]
            
            # Actualizar estado del ticket
            ticket_data["status"] = "cerrado"
            ticket_data["estado_detallado"] = "cerrado_por_owner"
            ticket_data["closed_by"] = str(interaction.user.id)
            ticket_data["closed_at"] = datetime.utcnow().isoformat()
            
            # Agregar al historial
            ticket_data["historial"].append({
                "estado": "cerrado",
                "timestamp": datetime.utcnow().isoformat(),
                "detalles": f"Ticket cerrado por {interaction.user.name}"
            })
            
            save_data(data)

            # Crear embed de cierre
            embed = discord.Embed(
                title="🔒 Ticket Cerrado",
                description=f"Este ticket ha sido cerrado por {interaction.user.mention}. El canal será eliminado en 5 segundos.",
                color=0xFF0000,
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="📋 Detalles",
                value=f"**ID del Ticket:** {self.ticket_id}\n**Cerrado por:** {interaction.user.name}",
                inline=False
            )
            embed.set_footer(text="El ticket será archivado próximamente")

            # Deshabilitar el botón
            button.disabled = True
            button.label = "Ticket Cerrado"
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Esperar 5 segundos y eliminar el canal
            await asyncio.sleep(5)
            await interaction.channel.delete(reason=f"Ticket {self.ticket_id} cerrado por {interaction.user.name}")
            
            # Opcional: Enviar mensaje de notificación al usuario original
            if ticket_data.get("user_id"):
                try:
                    user = await interaction.guild.fetch_member(int(ticket_data["user_id"]))
                    if user:
                        user_embed = discord.Embed(
                            title="📬 Ticket Cerrado",
                            description=f"Tu ticket `{self.ticket_id}` ha sido cerrado por un owner.",
                            color=0xFF0000
                        )
                        await user.send(embed=user_embed)
                except Exception as e:
                    logger.error(f"Error al notificar al usuario: {str(e)}")

            logger.info(f'Ticket {self.ticket_id} cerrado por {interaction.user.id}')

        except Exception as e:
            logger.error(f'Error al cerrar ticket: {str(e)}')
            await handle_interaction_response(
                interaction,
                "❌ Hubo un error al cerrar el ticket. Por favor, inténtalo de nuevo."
            )