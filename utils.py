import discord
from discord import app_commands
import requests
import uuid
from datetime import datetime
from typing import Optional, Callable, Any, Dict, List
import json
import aiohttp

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
        if isinstance(error, app_commands.errors.CheckFailure):
            # Ya manejado por el decorador is_owner()
            return
        elif isinstance(error, app_commands.CommandNotFound):
            await interaction.response.send_message(
                "El comando no existe. Usa /help para ver los comandos disponibles.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Ha ocurrido un error inesperado. Por favor, inténtalo de nuevo más tarde.",
                ephemeral=True
            )
            print(f"Error en comando {interaction.command}: {str(error)}")

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
                "source": "fortnite_api"
            }
        data["shop"]["last_updated"] = datetime.utcnow().isoformat()
        save_data(data)
        return True
    except requests.RequestException as e:
        print(f"Error al sincronizar tienda: {e}")
        return False