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
from utils import setup_error_handlers
from chatgpt_chat import chat_manager

# Inicializar cliente y árbol de comandos
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Configurar los comandos y manejadores de errores
async def setup():
    setup_owner_commands(tree, client)
    setup_user_commands(tree, client)
    setup_general_commands(tree, client)
    await setup_error_handlers(tree)

# La configuración se ejecutará en la función main

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")
    activity = discord.Activity(type=discord.ActivityType.playing, name="ia")
    await client.change_presence(activity=activity)
    try:
        synced = await tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(e)

@client.event
async def on_message(message):
    # Ignorar mensajes del propio bot
    if message.author == client.user:
        return

    # Verificar si el bot fue mencionado
    if client.user.mentioned_in(message):
        # Eliminar la mención del bot del mensaje
        content = message.content.replace(f'<@{client.user.id}>', '').strip()
        if not content:
            await message.reply('¡Hola! ¿En qué puedo ayudarte?')
            return

        # Mostrar indicador de escritura
        async with message.channel.typing():
            try:
                # Obtener respuesta del ChatManager
                response = await chat_manager.get_response(
                    str(message.author.id),
                    content
                )
                
                # Enviar la respuesta
                await message.reply(response)
            except Exception as e:
                print(f'Error al procesar mensaje: {str(e)}')
                await message.reply(
                    'Lo siento, ha ocurrido un error al procesar tu mensaje. '
                    'Por favor, inténtalo de nuevo más tarde.'
                )
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