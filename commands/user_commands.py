import discord
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import aiohttp
import json
import random
import string

import logging
from data_manager import (load_data, save_data, get_next_ticket_id, 
                         get_roblox_account, link_roblox_account, 
                         get_pending_verification, add_pending_verification, 
                         remove_pending_verification, cleanup_expired_verifications)
from views.enhanced_product_view import EnhancedProductView
from views.enhanced_ticket_view import EnhancedTicketView
from views.shop_view import ShopView
from utils import sync_fortnite_shop, cache_fortnite_shop
from config import (TICKET_CHANNEL_ID, OWNER_ROLE_ID, FORTNITE_API_KEY, FORTNITE_API_URL, 
                   FORTNITE_HEADERS, ROBLOX_GROUP_ID, ROBLOX_API_BASE, ROBLOX_GROUPS_API)

# Configuración del logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

def calculate_days_since_creation(created_date: str):
    """Calcula los días desde la creación de la cuenta"""
    try:
        # Formato: 2020-01-15T00:00:00.000Z
        creation_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
        current_date = datetime.now(creation_date.tzinfo)
        return (current_date - creation_date).days
    except Exception as e:
        logger.error(f"Error calculando días desde creación: {e}")
        return 0

def setup(tree: app_commands.CommandTree, client: discord.Client):
    @tree.command(name="products", description="Ver todos los productos disponibles")
    async def products(interaction: discord.Interaction):
        try:
            data = load_data()
            products = list(data["products"].items())
            items_per_page = 24
            pages = [products[i:i + items_per_page] for i in range(0, len(products), items_per_page)] if products else [[]]
            
            view = EnhancedProductView(products, pages)
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)
        except discord.NotFound:
            # Interacción expirada, no hacer nada
            print(f"Interacción de products expirada para usuario {interaction.user.id}")
        except Exception as e:
            print(f"Error en comando products: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.response.send_message(
                        "❌ Ha ocurrido un error. Inténtalo de nuevo.",
                        ephemeral=True
                    )
                except:
                    pass

    @tree.command(name="ticket", description="Abre un ticket para comprar un producto")
    async def ticket(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = load_data()
        user_id = str(interaction.user.id)
        
        # Verificar si ya tiene un ticket abierto
        has_open_ticket = False
        for ticket_id, ticket in data["tickets"].items():
            if ticket["user_id"] == user_id and ticket["status"] == "abierto" and ticket.get("estado_detallado") not in ["cerrado_por_owner", "cerrado"]:
                has_open_ticket = True
                await interaction.followup.send("Ya tienes un ticket abierto. Por favor, espera a que se resuelva.", ephemeral=True)
                return
        
        if not data["products"]:
            await interaction.followup.send("No hay productos disponibles. Contacta a un Owner.", ephemeral=True)
            return
        
        # Mostrar productos con vista mejorada
        items_per_page = 24
        products = list(data["products"].items())
        pages = [products[i:i + items_per_page] for i in range(0, len(products), items_per_page)]
        view = EnhancedProductView(products, pages)
        embed = view.create_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @tree.command(name="ver_tienda", description="Muestra los regalos disponibles de la tienda de Fortnite")
    async def ver_tienda(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            # Intentar usar caché primero
            data = load_data()
            cached_data = cache_fortnite_shop()
            
            if cached_data:
                logger.info("Usando datos en caché de la tienda de Fortnite")
                data["gifts"].update(cached_data)
                sync_success = True
            else:
                logger.info("Sincronizando datos frescos de la tienda de Fortnite")
                sync_success = sync_fortnite_shop()
            data = load_data()
            
            if not data or not isinstance(data, dict):
                await interaction.followup.send("Error al cargar los datos de la tienda. Por favor, intenta más tarde.", ephemeral=True)
                return
            
            # Asegurarse de que data tenga la estructura correcta
            if "shop" not in data:
                data["shop"] = {}
            if "gifts" not in data:
                data["gifts"] = {}
                save_data(data)
            
            gifts = data["gifts"]
            if not gifts:
                await interaction.followup.send("La tienda está vacía. Contacta a un Owner para añadir ítems manualmente.", ephemeral=True)
                return
            
            items_per_page = 24
            gifts_list = list(gifts.items())
            # Asegurarse de que la lista no esté vacía y manejar la paginación de forma segura
            if not gifts_list:
                pages = [[]]  # Si no hay regalos, crear una página vacía
            else:
                pages = [gifts_list[i:i + items_per_page] for i in range(0, len(gifts_list), items_per_page)]
            last_updated = data.get("shop", {}).get("last_updated", "Desconocida")
            
            view = ShopView(gifts_list, last_updated, sync_success, pages)
            await interaction.followup.send(embed=view.create_embed(), view=view, ephemeral=True)
        except Exception as e:
            print(f"Error en el comando ver_tienda: {str(e)}")
            await interaction.followup.send("Ocurrió un error al mostrar la tienda. Por favor, intenta más tarde.", ephemeral=True)

    # Funciones auxiliares para Roblox API
    async def get_roblox_user_info(username: str):
        """Obtiene información del usuario de Roblox por nombre de usuario"""
        try:
            async with aiohttp.ClientSession() as session:
                # Primero obtener el ID del usuario por nombre
                url = f"https://users.roblox.com/v1/usernames/users"
                data = {"usernames": [username]}
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('data') and len(result['data']) > 0:
                            user_id = result['data'][0]['id']
                            
                            # Ahora obtener información detallada del usuario
                            user_url = f"https://users.roblox.com/v1/users/{user_id}"
                            async with session.get(user_url) as user_response:
                                if user_response.status == 200:
                                    user_data = await user_response.json()
                                    return user_data
                    return None
        except Exception as e:
            logger.error(f"Error obteniendo información de usuario Roblox: {e}")
            return None

    async def check_group_membership(user_id: int, group_id: int):
        """Verifica si un usuario está en un grupo específico"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://groups.roblox.com/v1/groups/{group_id}/users?limit=100"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        members = data.get('data', [])
                        for member in members:
                            if member.get('user', {}).get('userId') == user_id:
                                return {
                                    'is_member': True,
                                    'join_date': member.get('joinDate'),
                                    'role': member.get('role', {})
                                }
                        return {'is_member': False}
                    return {'is_member': False}
        except Exception as e:
            logger.error(f"Error verificando membresía de grupo: {e}")
            return {'is_member': False}

    def generate_verification_code():
        """Genera un código de verificación aleatorio"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))



    class VerificationView(discord.ui.View):
        def __init__(self, user_id: str, verification_code: str, roblox_info: dict):
            super().__init__(timeout=600)  # 10 minutos
            self.user_id = user_id
            self.verification_code = verification_code
            self.roblox_info = roblox_info
        
        @discord.ui.button(label='🔍 Verificar Cuenta', style=discord.ButtonStyle.success, emoji='✅')
        async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message("❌ Solo el usuario que inició la verificación puede usar este botón.", ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True)
            
            try:
                data = load_data()
                
                # Verificar si hay una verificación pendiente
                if "pending_verifications" not in data or self.user_id not in data["pending_verifications"]:
                    await interaction.followup.send("❌ No tienes ninguna verificación pendiente.", ephemeral=True)
                    return
                
                pending = data["pending_verifications"][self.user_id]
                
                # Verificar si no ha expirado
                expires_at = datetime.fromisoformat(pending["expires_at"])
                if datetime.now() > expires_at:
                    del data["pending_verifications"][self.user_id]
                    save_data(data)
                    await interaction.followup.send("❌ La verificación ha expirado. Usa `/vincular` nuevamente.", ephemeral=True)
                    return
                
                # Obtener información actualizada del usuario
                user_info = await get_roblox_user_info(pending["roblox_username"])
                if not user_info:
                    await interaction.followup.send("❌ Error al obtener información del usuario de Roblox.", ephemeral=True)
                    return
                
                # Verificar si el código está en la descripción
                description = user_info.get("description", "")
                if pending["verification_code"] not in description:
                    embed = discord.Embed(
                        title="❌ Código No Encontrado",
                        description=f"No se encontró el código `{pending['verification_code']}` en tu descripción de Roblox.",
                        color=0xff4757
                    )
                    embed.add_field(
                        name="🔧 Instrucciones",
                        value=f"1. Ve a tu [perfil de Roblox](https://www.roblox.com/users/{user_info['id']}/profile)\n2. Edita tu descripción\n3. Agrega el código: `{pending['verification_code']}`\n4. Guarda los cambios\n5. Haz clic en 'Verificar Cuenta' nuevamente",
                        inline=False
                    )
                    embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={user_info['id']}&width=420&height=420&format=png")
                    embed.set_footer(text="💡 Asegúrate de que tu perfil sea público")
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                # Verificación exitosa - guardar datos
                if "roblox_accounts" not in data:
                    data["roblox_accounts"] = {}
                
                data["roblox_accounts"][self.user_id] = {
                    "roblox_user_id": user_info["id"],
                    "roblox_username": user_info["name"],
                    "roblox_display_name": user_info["displayName"],
                    "roblox_description": user_info.get("description", ""),
                    "roblox_created": user_info.get("created", ""),
                    "verified_at": datetime.now().isoformat(),
                    "is_verified": True
                }
                
                # Limpiar verificación pendiente
                del data["pending_verifications"][self.user_id]
                save_data(data)
                
                # Crear embed de éxito con diseño mejorado
                embed = discord.Embed(
                    title="🎉 ¡Cuenta Vinculada Exitosamente!",
                    description=f"Tu cuenta de Discord ha sido vinculada con **{user_info['displayName']}**",
                    color=0x2ecc71
                )
                
                embed.add_field(
                    name="👤 Usuario Roblox",
                    value=f"```yaml\nNombre: {user_info['displayName']}\nUsuario: @{user_info['name']}\nID: {user_info['id']}```",
                    inline=False
                )
                
                embed.add_field(
                    name="📅 Fecha de Vinculación",
                    value=f"```diff\n+ {datetime.now().strftime('%d/%m/%Y a las %H:%M')}```",
                    inline=True
                )
                
                embed.add_field(
                    name="🔐 Estado",
                    value="```css\n[VERIFICADO]```",
                    inline=True
                )
                
                embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={user_info['id']}&width=420&height=420&format=png")
                embed.set_footer(text="🎮 GameMid Bot • Vinculación completada", icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
                embed.timestamp = datetime.now()
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Deshabilitar el botón después de la verificación exitosa
                button.disabled = True
                button.label = "✅ Verificado"
                await interaction.edit_original_response(view=self)
                
            except Exception as e:
                logger.error(f"Error en verificación: {e}")
                await interaction.followup.send("❌ Ocurrió un error durante la verificación. Inténtalo más tarde.", ephemeral=True)
        
        @discord.ui.button(label='❌ Cancelar', style=discord.ButtonStyle.danger)
        async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message("❌ Solo el usuario que inició la verificación puede usar este botón.", ephemeral=True)
                return
            
            try:
                data = load_data()
                if "pending_verifications" in data and self.user_id in data["pending_verifications"]:
                    del data["pending_verifications"][self.user_id]
                    save_data(data)
                
                embed = discord.Embed(
                    title="❌ Verificación Cancelada",
                    description="La verificación de tu cuenta de Roblox ha sido cancelada.",
                    color=0xe74c3c
                )
                embed.set_footer(text="Puedes usar /vincular nuevamente cuando quieras")
                
                await interaction.response.edit_message(embed=embed, view=None)
                
            except Exception as e:
                logger.error(f"Error cancelando verificación: {e}")
                await interaction.response.send_message("❌ Error al cancelar la verificación.", ephemeral=True)

    class UnlinkAccountView(discord.ui.View):
        def __init__(self, user_id: str, roblox_info: dict):
            super().__init__(timeout=300)  # 5 minutos
            self.user_id = user_id
            self.roblox_info = roblox_info
        
        @discord.ui.button(label='🔓 Desvincular Cuenta', style=discord.ButtonStyle.danger, emoji='⚠️')
        async def unlink_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message("❌ Solo el propietario de la cuenta puede desvincularla.", ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True)
            
            try:
                data = load_data()
                
                # Verificar si la cuenta existe
                if "roblox_accounts" not in data or self.user_id not in data["roblox_accounts"]:
                    await interaction.followup.send("❌ No se encontró una cuenta vinculada.", ephemeral=True)
                    return
                
                # Obtener información antes de eliminar
                account_info = data["roblox_accounts"][self.user_id]
                roblox_username = account_info.get("roblox_username", "Usuario desconocido")
                roblox_display_name = account_info.get("roblox_display_name", "Nombre desconocido")
                
                # Eliminar la cuenta vinculada
                del data["roblox_accounts"][self.user_id]
                save_data(data)
                
                # Crear embed de confirmación
                embed = discord.Embed(
                    title="🔓 Cuenta Desvinculada Exitosamente",
                    description=f"Tu cuenta de Discord ha sido desvinculada de **{roblox_display_name}** (@{roblox_username})",
                    color=0xe74c3c
                )
                
                embed.add_field(
                    name="✅ Proceso Completado",
                    value="```yaml\n🔹 Datos eliminados: Sí\n🔹 Vinculación: Removida\n🔹 Estado: Desconectado```",
                    inline=False
                )
                
                embed.add_field(
                    name="🔄 ¿Quieres volver a vincular?",
                    value="Puedes usar `/vincular <usuario_roblox>` en cualquier momento para crear una nueva vinculación.",
                    inline=False
                )
                
                embed.set_footer(text="🛡️ Tus datos han sido eliminados de forma segura", icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
                embed.timestamp = datetime.now()
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Deshabilitar el botón después de desvincular
                button.disabled = True
                button.label = "🔓 Desvinculado"
                await interaction.edit_original_response(view=self)
                
            except Exception as e:
                logger.error(f"Error desvinculando cuenta: {e}")
                await interaction.followup.send("❌ Ocurrió un error al desvincular la cuenta. Inténtalo más tarde.", ephemeral=True)
        
        @discord.ui.button(label='❌ Cancelar', style=discord.ButtonStyle.secondary)
        async def cancel_unlink_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message("❌ Solo el propietario de la cuenta puede usar este botón.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="✅ Operación Cancelada",
                description="La desvinculación ha sido cancelada. Tu cuenta sigue vinculada.",
                color=0x95a5a6
            )
            embed.set_footer(text="Tu cuenta de Roblox permanece vinculada")
            
            await interaction.response.edit_message(embed=embed, view=None)

    @tree.command(name="vincular", description="Vincula tu cuenta de Discord con tu cuenta de Roblox")
    async def vincular(interaction: discord.Interaction, username: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            data = load_data()
            user_id = str(interaction.user.id)
            
            # Verificar si ya está vinculado
            if "roblox_accounts" not in data:
                data["roblox_accounts"] = {}
            
            if user_id in data["roblox_accounts"]:
                embed = discord.Embed(
                    title="⚠️ Cuenta Ya Vinculada",
                    description="Ya tienes una cuenta de Roblox vinculada a tu Discord.",
                    color=0xf39c12
                )
                embed.add_field(
                    name="🎮 Cuenta Actual",
                    value=f"**{data['roblox_accounts'][user_id]['roblox_display_name']}** (@{data['roblox_accounts'][user_id]['roblox_username']})",
                    inline=False
                )
                embed.add_field(
                    name="💡 ¿Necesitas cambiarla?",
                    value="Contacta a un administrador para desvincular tu cuenta actual.",
                    inline=False
                )
                embed.set_footer(text="🔒 Solo se permite una cuenta por usuario")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obtener información del usuario de Roblox
            user_info = await get_roblox_user_info(username)
            if not user_info:
                embed = discord.Embed(
                    title="❌ Usuario No Encontrado",
                    description=f"No se pudo encontrar el usuario **{username}** en Roblox.",
                    color=0xe74c3c
                )
                embed.add_field(
                    name="🔍 Verifica que:",
                    value="• El nombre de usuario sea correcto\n• No incluyas espacios extra\n• El usuario exista en Roblox",
                    inline=False
                )
                embed.set_footer(text="💡 Intenta con el nombre exacto del perfil")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Generar código de verificación
            verification_code = generate_verification_code()
            
            # Guardar datos temporales de verificación
            if "pending_verifications" not in data:
                data["pending_verifications"] = {}
            
            data["pending_verifications"][user_id] = {
                "roblox_user_id": user_info["id"],
                "roblox_username": user_info["name"],
                "roblox_display_name": user_info["displayName"],
                "verification_code": verification_code,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
            }
            
            save_data(data)
            
            # Crear embed con diseño mejorado
            embed = discord.Embed(
                title="🔗 Verificación de Cuenta Roblox",
                description=f"Para completar la vinculación con **{user_info['displayName']}**, sigue estos pasos:",
                color=0x3498db
            )
            
            embed.add_field(
                name="📝 Paso 1: Editar Descripción",
                value=f"Ve a tu [perfil de Roblox](https://www.roblox.com/users/{user_info['id']}/profile) y agrega este código a tu descripción:\n```yaml\nCódigo: {verification_code}```",
                inline=False
            )
            
            embed.add_field(
                name="✅ Paso 2: Verificar",
                value="Haz clic en el botón **'🔍 Verificar Cuenta'** cuando hayas agregado el código.",
                inline=False
            )
            
            embed.add_field(
                name="⏰ Tiempo Límite",
                value="```diff\n- Expira en 10 minutos```",
                inline=True
            )
            
            embed.add_field(
                name="🔒 Requisitos",
                value="```yaml\nPerfil: Público\nDescripción: Editable```",
                inline=True
            )
            
            embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={user_info['id']}&width=420&height=420&format=png")
            embed.set_footer(text="🎮 GameMid Bot • Sistema de Verificación", icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
            embed.timestamp = datetime.now()
            
            # Crear vista con botones
            view = VerificationView(user_id, verification_code, user_info)
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en comando vincular: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Ocurrió un error al procesar la vinculación.",
                color=0xe74c3c
            )
            embed.add_field(
                name="🔧 Solución",
                value="Inténtalo nuevamente en unos momentos.",
                inline=False
            )
            embed.set_footer(text="Si el problema persiste, contacta a un administrador")
            await interaction.followup.send(embed=embed, ephemeral=True)



    @tree.command(name="micuenta", description="Muestra información de tu cuenta de Roblox vinculada")
    async def micuenta(interaction: discord.Interaction, grupo_id: int = None):
        await interaction.response.defer(ephemeral=True)
        
        try:
            data = load_data()
            user_id = str(interaction.user.id)
            
            # Verificar si tiene cuenta vinculada
            if "roblox_accounts" not in data or user_id not in data["roblox_accounts"]:
                error_embed = discord.Embed(
                    title="🚫 Cuenta No Vinculada",
                    description="No tienes una cuenta de Roblox vinculada a tu perfil de Discord.",
                    color=0xff4444
                )
                error_embed.add_field(
                    name="💡 ¿Cómo vincular?",
                    value="Usa el comando `/vincular <usuario_roblox>` para comenzar el proceso de vinculación.",
                    inline=False
                )
                error_embed.set_footer(text="💡 Tip: La vinculación es gratuita y segura")
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            account_info = data["roblox_accounts"][user_id]
            
            # Obtener información actualizada del usuario
            user_info = await get_roblox_user_info(account_info["roblox_username"])
            if not user_info:
                await interaction.followup.send("❌ Error al obtener información actualizada de tu cuenta de Roblox.", ephemeral=True)
                return
            
            # Determinar color basado en la antigüedad de la cuenta
            created_date = user_info.get('created', '')
            days_since = 0
            if created_date:
                try:
                    days_since = calculate_days_since_creation(created_date)
                except:
                    pass
            
            # Color dinámico basado en la antigüedad
            if days_since >= 365:  # 1+ años
                embed_color = 0xffd700  # Dorado
            elif days_since >= 180:  # 6+ meses
                embed_color = 0x9932cc  # Púrpura
            elif days_since >= 30:   # 1+ mes
                embed_color = 0x00bfff  # Azul cielo
            else:
                embed_color = 0x32cd32  # Verde lima
            
            embed = discord.Embed(
                title="🎮 Mi Cuenta de Roblox",
                color=embed_color
            )
            
            # Header con información principal
            display_name = user_info['displayName']
            username = user_info['name']
            user_id_roblox = user_info['id']
            
            embed.description = f"""```yaml
🎯 Usuario: {display_name} (@{username})
🆔 ID: {user_id_roblox}
```"""
            
            # Thumbnail del avatar (si está disponible)
            try:
                avatar_url = f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id_roblox}&width=420&height=420&format=png"
                embed.set_thumbnail(url=avatar_url)
            except:
                pass
            
            # Información de la cuenta con diseño mejorado
            if created_date:
                try:
                    creation_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    formatted_date = creation_date.strftime("%d/%m/%Y")
                    
                    # Calcular años, meses y días
                    years = days_since // 365
                    months = (days_since % 365) // 30
                    days = (days_since % 365) % 30
                    
                    age_text = []
                    if years > 0:
                        age_text.append(f"{years} año{'s' if years != 1 else ''}")
                    if months > 0:
                        age_text.append(f"{months} mes{'es' if months != 1 else ''}")
                    if days > 0 or not age_text:
                        age_text.append(f"{days} día{'s' if days != 1 else ''}")
                    
                    age_display = ", ".join(age_text)
                    
                    embed.add_field(
                        name="📅 Fecha de Creación",
                        value=f"```📆 {formatted_date}\n⏰ {age_display}\n📊 {days_since:,} días totales```",
                        inline=True
                    )
                    
                    # Elegibilidad para Robux con diseño mejorado
                    if days_since >= 15:
                        robux_status = "```diff\n+ ✅ ELEGIBLE\n+ Cuenta verificada\n+ 15+ días cumplidos```"
                        robux_color = "✅"
                    else:
                        days_remaining = 15 - days_since
                        robux_status = f"```diff\n- ❌ NO ELEGIBLE\n- Faltan {days_remaining} días\n- Mínimo: 15 días```"
                        robux_color = "❌"
                    
                    embed.add_field(
                        name=f"{robux_color} Elegibilidad Robux",
                        value=robux_status,
                        inline=True
                    )
                except:
                    embed.add_field(
                        name="📅 Fecha de Creación",
                        value="```❓ No disponible```",
                        inline=True
                    )
            
            # Estado de verificación con diseño premium
            verified_at = datetime.fromisoformat(account_info['verified_at'])
            verification_text = f"```yaml\n🔐 Estado: VERIFICADO\n📅 Desde: {verified_at.strftime('%d/%m/%Y')}\n⏰ Hora: {verified_at.strftime('%H:%M')}```"
            
            embed.add_field(
                name="🛡️ Verificación",
                value=verification_text,
                inline=True
            )
            
            # Verificar membresía en grupo con diseño mejorado
            if grupo_id:
                group_info = await check_group_membership(user_info['id'], grupo_id)
                if group_info['is_member']:
                    join_date = group_info.get('join_date', 'Desconocida')
                    role_name = group_info.get('role', {}).get('name', 'Miembro')
                    
                    group_text = f"```yaml\n👥 Estado: MIEMBRO ACTIVO\n🎭 Rol: {role_name}\n📅 Unido: {join_date}```"
                    group_emoji = "🟢"
                else:
                    group_text = f"```diff\n- ❌ NO ES MIEMBRO\n- Grupo ID: {grupo_id}\n- Estado: Externo```"
                    group_emoji = "🔴"
                
                embed.add_field(
                    name=f"{group_emoji} Grupo {grupo_id}",
                    value=group_text,
                    inline=False
                )
            
            # Descripción con formato mejorado
            description = user_info.get('description', '')
            if description:
                if len(description) > 150:
                    description = description[:150] + "..."
                desc_text = f"```{description}```"
            else:
                desc_text = "```❌ Sin descripción configurada```"
            
            embed.add_field(
                name="📝 Descripción del Perfil",
                value=desc_text,
                inline=False
            )
            
            # Estadísticas adicionales
            stats_text = f"```yaml\n🔗 Vinculado con: {interaction.user.display_name}\n🌐 Perfil público: Sí\n🔄 Última actualización: Ahora```"
            embed.add_field(
                name="📊 Estadísticas",
                value=stats_text,
                inline=False
            )
            
            # Footer mejorado con más información
            embed.set_footer(
                text=f"🎮 Roblox ID: {user_id_roblox} • 🔄 Actualizado automáticamente • 🛡️ Datos seguros",
                icon_url="https://images-ext-1.discordapp.net/external/RoC4w8jOJB8gOOjOYP3xOOhJKJmqo_8Hn6Gg_Gg_Gg/https/cdn.discordapp.com/emojis/123456789.png"
            )
            
            # Agregar autor con avatar del usuario de Discord
            embed.set_author(
                name=f"Perfil de {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Crear vista con botón de desvincular
            unlink_view = UnlinkAccountView(user_id, account_info)
            
            await interaction.followup.send(embed=embed, view=unlink_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en comando micuenta: {e}")
            error_embed = discord.Embed(
                title="⚠️ Error del Sistema",
                description="Ocurrió un error inesperado al procesar tu solicitud.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔧 Soluciones",
                value="• Intenta nuevamente en unos segundos\n• Verifica que tu cuenta esté vinculada\n• Contacta al soporte si persiste",
                inline=False
            )
            error_embed.set_footer(text="💡 Este error ha sido registrado automáticamente")
            await interaction.followup.send(embed=error_embed, ephemeral=True)