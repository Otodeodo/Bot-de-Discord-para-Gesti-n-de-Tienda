import asyncio
import discord
from datetime import datetime, timedelta
from data_manager import get_all_roblox_accounts, load_data, save_data
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobuxReminderSystem:
    def __init__(self, client):
        self.client = client
        self.is_running = False
        self.reminder_task = None
        
    async def start_reminder_system(self):
        """Inicia el sistema de recordatorios automáticos."""
        if self.is_running:
            logger.warning("El sistema de recordatorios ya está ejecutándose")
            return
            
        self.is_running = True
        self.reminder_task = asyncio.create_task(self._reminder_loop())
        logger.info("Sistema de recordatorios iniciado")
        
    async def stop_reminder_system(self):
        """Detiene el sistema de recordatorios."""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.reminder_task:
            self.reminder_task.cancel()
            try:
                await self.reminder_task
            except asyncio.CancelledError:
                pass
        logger.info("Sistema de recordatorios detenido")
        
    async def _reminder_loop(self):
        """Loop principal del sistema de recordatorios."""
        while self.is_running:
            try:
                await self._check_and_send_reminders()
                # Esperar 24 horas antes de la siguiente verificación
                await asyncio.sleep(24 * 60 * 60)  # 24 horas en segundos
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en el loop de recordatorios: {e}")
                # Esperar 1 hora antes de reintentar en caso de error
                await asyncio.sleep(60 * 60)
                
    async def _check_and_send_reminders(self):
        """Verifica y envía recordatorios a usuarios elegibles."""
        try:
            data = load_data()
            roblox_accounts = data.get('roblox_accounts', {})
            reminded_users = data.get('reminded_users', set())
            
            current_time = datetime.utcnow()
            newly_reminded = set()
            
            for discord_user_id, account_data in roblox_accounts.items():
                try:
                    # Verificar si ya se le envió recordatorio
                    if discord_user_id in reminded_users:
                        continue
                        
                    # Obtener fecha de creación de la cuenta
                    created_date_str = account_data.get('created')
                    if not created_date_str:
                        continue
                        
                    # Parsear la fecha de creación
                    created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
                    
                    # Calcular días desde la creación
                    days_since_creation = (current_time - created_date).days
                    
                    # Verificar si cumple exactamente 15 días (con margen de 1 día)
                    if 15 <= days_since_creation <= 16:
                        success = await self._send_robux_eligibility_reminder(discord_user_id, account_data, days_since_creation)
                        if success:
                            newly_reminded.add(discord_user_id)
                            
                except Exception as e:
                    logger.error(f"Error procesando usuario {discord_user_id}: {e}")
                    continue
                    
            # Actualizar la lista de usuarios recordados
            if newly_reminded:
                data['reminded_users'] = list(reminded_users.union(newly_reminded))
                save_data(data)
                logger.info(f"Recordatorios enviados a {len(newly_reminded)} usuarios")
                
        except Exception as e:
            logger.error(f"Error en _check_and_send_reminders: {e}")
            
    async def _send_robux_eligibility_reminder(self, discord_user_id: str, account_data: dict, days_since_creation: int):
        """Envía un recordatorio de elegibilidad para Robux a un usuario específico."""
        try:
            user = await self.client.fetch_user(int(discord_user_id))
            if not user:
                logger.warning(f"No se pudo encontrar el usuario {discord_user_id}")
                return False
                
            # Crear embed del recordatorio
            embed = discord.Embed(
                title="🎉 ¡Felicidades! Ya eres elegible para Robux",
                description=f"Tu cuenta de Roblox **{account_data.get('display_name', 'N/A')}** ya tiene {days_since_creation} días y ahora es elegible para recibir Robux.",
                color=0x00FF00
            )
            
            # Agregar información de la cuenta
            embed.add_field(
                name="👤 Información de tu Cuenta",
                value=f"```yaml\n"
                      f"Usuario: {account_data.get('display_name', 'N/A')}\n"
                      f"ID: {account_data.get('id', 'N/A')}\n"
                      f"Días desde creación: {days_since_creation}\n"
                      f"Estado: ✅ Elegible para Robux\n"
                      f"```",
                inline=False
            )
            
            # Agregar instrucciones
            embed.add_field(
                name="📋 ¿Qué puedes hacer ahora?",
                value="• Usar el comando `/micuenta` para ver tu estado\n"
                      "• Participar en eventos y sorteos de Robux\n"
                      "• Acceder a beneficios exclusivos del servidor",
                inline=False
            )
            
            # Agregar thumbnail del avatar
            if account_data.get('avatar_url'):
                embed.set_thumbnail(url=account_data['avatar_url'])
                
            embed.set_footer(
                text="Sistema de Recordatorios Automáticos • GameMid",
                icon_url="https://cdn.discordapp.com/attachments/1234567890/roblox_icon.png"
            )
            
            embed.timestamp = datetime.utcnow()
            
            # Enviar mensaje directo
            await user.send(embed=embed)
            logger.info(f"Recordatorio enviado exitosamente a {user.name} ({discord_user_id})")
            return True
            
        except discord.Forbidden:
            logger.warning(f"No se pudo enviar DM al usuario {discord_user_id} (DMs cerrados)")
            return False
        except Exception as e:
            logger.error(f"Error enviando recordatorio a {discord_user_id}: {e}")
            return False
            
    async def send_manual_reminder(self, discord_user_id: str):
        """Envía un recordatorio manual a un usuario específico."""
        try:
            data = load_data()
            account_data = data.get('roblox_accounts', {}).get(discord_user_id)
            
            if not account_data:
                return False, "Usuario no tiene cuenta de Roblox vinculada"
                
            # Calcular días desde la creación
            created_date_str = account_data.get('created')
            if not created_date_str:
                return False, "No se pudo obtener la fecha de creación de la cuenta"
                
            created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
            days_since_creation = (datetime.utcnow() - created_date).days
            
            if days_since_creation < 15:
                return False, f"La cuenta aún no es elegible (faltan {15 - days_since_creation} días)"
                
            success = await self._send_robux_eligibility_reminder(discord_user_id, account_data, days_since_creation)
            
            if success:
                # Marcar como recordado
                reminded_users = set(data.get('reminded_users', []))
                reminded_users.add(discord_user_id)
                data['reminded_users'] = list(reminded_users)
                save_data(data)
                return True, "Recordatorio enviado exitosamente"
            else:
                return False, "Error al enviar el recordatorio"
                
        except Exception as e:
            logger.error(f"Error en send_manual_reminder: {e}")
            return False, f"Error: {str(e)}"
            
    def get_reminder_stats(self):
        """Obtiene estadísticas del sistema de recordatorios."""
        try:
            data = load_data()
            roblox_accounts = data.get('roblox_accounts', {})
            reminded_users = set(data.get('reminded_users', []))
            
            total_linked = len(roblox_accounts)
            total_reminded = len(reminded_users)
            
            # Contar usuarios elegibles no recordados
            current_time = datetime.utcnow()
            eligible_not_reminded = 0
            
            for discord_user_id, account_data in roblox_accounts.items():
                if discord_user_id in reminded_users:
                    continue
                    
                created_date_str = account_data.get('created')
                if not created_date_str:
                    continue
                    
                try:
                    created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
                    days_since_creation = (current_time - created_date).days
                    
                    if days_since_creation >= 15:
                        eligible_not_reminded += 1
                except:
                    continue
                    
            return {
                'total_linked_accounts': total_linked,
                'total_reminded': total_reminded,
                'eligible_not_reminded': eligible_not_reminded,
                'is_running': self.is_running
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return None

# Instancia global del sistema de recordatorios
reminder_system = None

def initialize_reminder_system(client):
    """Inicializa el sistema de recordatorios global."""
    global reminder_system
    reminder_system = RobuxReminderSystem(client)
    return reminder_system

def get_reminder_system():
    """Obtiene la instancia del sistema de recordatorios."""
    return reminder_system