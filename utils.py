import discord
from discord import app_commands
import requests
import uuid
from datetime import datetime
from typing import Optional, Callable, Any, Dict, List
import json
import aiohttp
import logging
from functools import wraps
import asyncio

# Configuración del sistema de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Decorador para reintentos en operaciones críticas
def retry_operation(max_retries: int = 3, delay: float = 1.0):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f'Error en {func.__name__} después de {max_retries} intentos: {str(e)}')
                        raise
                    logger.warning(f'Intento {attempt + 1} fallido para {func.__name__}: {str(e)}')
                    await asyncio.sleep(delay)
            return None
        return wrapper
    return decorator

# Función para enviar notificaciones por DM
async def send_dm_notification(user: discord.User, message: str) -> bool:
    try:
        await user.send(message)
        logger.info(f'Notificación enviada a {user.name} (ID: {user.id})')
        return True
    except Exception as e:
        logger.error(f'Error al enviar DM a {user.name} (ID: {user.id}): {str(e)}')
        return False

# Validador de permisos de usuario
def check_user_permissions(user_id: str, required_id: str) -> bool:
    try:
        return str(user_id) == str(required_id)
    except Exception as e:
        logger.error(f'Error en validación de permisos: {str(e)}')
        return False

# Manejador de respuestas de interacción
async def handle_interaction_response(interaction: discord.Interaction, message: str, ephemeral: bool = True):
    try:
        await interaction.response.send_message(message, ephemeral=ephemeral)
        logger.debug(f'Respuesta enviada a {interaction.user.name}: {message}')
    except Exception as e:
        logger.error(f'Error al enviar respuesta de interacción: {str(e)}')
        try:
            await interaction.response.send_message(
                "Ha ocurrido un error al procesar tu solicitud.",
                ephemeral=True
            )
        except:
            pass

from config import OWNER_ROLE_ID, FORTNITE_API_URL, FORTNITE_HEADERS
from data_manager import load_data, save_data  # Esto está bien porque utils.py está en el directorio raíz

def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        role = discord.utils.get(interaction.user.roles, id=OWNER_ROLE_ID)
        if role is None:
            await interaction.response.send_message("No tienes permisos para ejecutar este comando. Este comando está reservado para Owners.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

async def setup_error_handlers(tree: app_commands.CommandTree):
    @tree.error
    async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Maneja errores de comandos de aplicación"""
        try:
            if isinstance(error, app_commands.MissingPermissions):
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ No tienes permisos para usar este comando.",
                        ephemeral=True
                    )
            elif isinstance(error, app_commands.CheckFailure):
                if "owner" in str(error).lower():
                    # Ya manejado por el decorador is_owner()
                    return
                elif isinstance(error, app_commands.CommandNotFound):
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            "El comando no existe. Usa /help para ver los comandos disponibles.",
                            ephemeral=True
                        )
                else:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            f"Ha ocurrido un error inesperado. Por favor, inténtalo de nuevo más tarde.",
                            ephemeral=True
                        )
                    print(f"Error en comando {interaction.command}: {str(error)}")
        except discord.NotFound:
            # Interacción expirada, solo registrar el error
            print(f"Error en comando {getattr(interaction, 'command', 'unknown')}: {str(error)} (interacción expirada)")
        except Exception as e:
            # Error adicional al manejar el error original
            print(f"Error al manejar error de comando: {e}")
            print(f"Error original: {error}")

def sync_fortnite_shop():
    data = load_data()
    try:
        response = requests.get(f"{FORTNITE_API_URL}/shop?lang=es", headers=FORTNITE_HEADERS)
        response.raise_for_status()
        shop_data = response.json().get("shop", [])
        
        # Clear previously synced gifts, keep manual ones
        data["gifts"] = {k: v for k, v in data["gifts"].items() if v.get("source") == "manual"}
        
        # Add shop items
        for item in shop_data:
            gift_id = item.get("id", str(uuid.uuid4()))
            data["gifts"][gift_id] = {
                "name": item.get("displayName", "Desconocido"),
                "price": item.get("price", {}).get("finalPrice", 0),
                "image_url": item.get("displayAssets", [{}])[0].get("url", ""),
                "source": "fortnite_api",
                "last_updated": datetime.utcnow().isoformat()
            }
        data["shop"]["last_updated"] = datetime.utcnow().isoformat()
        
        # Guardar en caché
        with open('fortnite_shop_cache.json', 'w', encoding='utf-8') as f:
            json.dump(data["gifts"], f)
            
        save_data(data)
        return True
    except requests.RequestException as e:
        logger.error(f"Error al sincronizar tienda: {e}")
        return False

def cache_fortnite_shop():
    """Obtiene los datos de la tienda desde el caché si están disponibles y son recientes."""
    try:
        with open('fortnite_shop_cache.json', 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            
        # Verificar si los datos en caché son recientes (menos de 1 hora)
        for item in cached_data.values():
            last_updated = datetime.fromisoformat(item.get('last_updated', '2000-01-01'))
            if (datetime.utcnow() - last_updated).total_seconds() > 3600:
                logger.info("Caché de la tienda expirado")
                return None
                
        logger.info("Usando datos en caché de la tienda")
        return cached_data
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Error al leer caché de la tienda: {e}")
        return None