import discord
from discord import app_commands
import sys
import os

# Agregar el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import DISCORD_TOKEN, intents
from commands.owner_commands import setup as setup_owner_commands
from commands.user_commands import setup as setup_user_commands
from commands.general_commands import setup as setup_general_commands
from commands.category_commands import setup as setup_category_commands
from commands.economy_commands import setup as setup_economy_commands
from commands.virtual_shop_commands import setup as setup_virtual_shop_commands
from utils import setup_error_handlers
from chatgpt_chat import chat_manager
from reminder_system import initialize_reminder_system

# Inicializar cliente y árbol de comandos
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Configurar los comandos y manejadores de errores
async def setup():
    setup_owner_commands(tree, client)
    setup_user_commands(tree, client)
    setup_general_commands(tree, client)
    setup_category_commands(tree, client)
    setup_economy_commands(tree, client)
    setup_virtual_shop_commands(tree, client)
    await setup_error_handlers(tree)

# La configuración se ejecutará en la función main

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")
    activity = discord.Activity(type=discord.ActivityType.playing, name="Gestionando Tickets y Productos")
    await client.change_presence(activity=activity)
    try:
        synced = await tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(e)
    
    # Inicializar y arrancar el sistema de recordatorios
    try:
        reminder_system = initialize_reminder_system(client)
        await reminder_system.start_reminder_system()
        print("Sistema de recordatorios de Robux iniciado")
    except Exception as e:
        print(f"Error al iniciar sistema de recordatorios: {e}")

# Diccionario para almacenar el último mensaje procesado por usuario
last_processed_messages = {}

@client.event
async def on_message(message):
    print(f"[DEBUG] Mensaje recibido: {message.content}")
    
    # Ignorar mensajes del propio bot
    if message.author == client.user:
        print(f"[DEBUG] Ignorando mensaje del bot")
        return

    print(f"[DEBUG] Verificando menciones...")
    print(f"[DEBUG] Bot ID: {client.user.id}")
    print(f"[DEBUG] Menciones: {[user.id for user in message.mentions]}")
    
    # Verificar si el bot fue mencionado
    if client.user.mentioned_in(message):
        print(f"[DEBUG] ¡Bot mencionado!")
        
        # Limpiar el contenido del mensaje
        content = message.content.replace(f'<@{client.user.id}>', '').strip()
        print(f"[DEBUG] Contenido limpio: '{content}'")
        
        # Si no hay contenido, usar mensaje por defecto
        if not content:
            content = "Hola"
        
        try:
            print(f"[DEBUG] Llamando a chat_manager...")
            # Obtener respuesta de la IA
            user_id = str(message.author.id)
            response = await chat_manager.get_response(user_id, content)
            print(f"[DEBUG] Respuesta obtenida: {response[:50]}...")
            
            # Enviar respuesta
            await message.reply(response)
            print(f"[DEBUG] Respuesta enviada")
        except Exception as e:
            print(f'[ERROR] Error completo: {e}')
            import traceback
            print(f'[ERROR] Traceback: {traceback.format_exc()}')
            await message.reply('Lo siento, ha ocurrido un error.')
    else:
        print(f"[DEBUG] Bot NO fue mencionado")

# Verificar que el token no esté vacío
if not DISCORD_TOKEN:
    print("Error: DISCORD_TOKEN está vacío. Por favor, coloca tu token en la variable DISCORD_TOKEN.")
    exit(1)

async def main():
    await setup()
    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())