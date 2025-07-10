import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from economy_system import economy
from views.virtual_shop_view import VirtualShopView
from typing import Optional
import random

def setup(tree: app_commands.CommandTree, client: discord.Client):
    
    @tree.command(name="balance", description="🪙 Muestra tu balance de GameCoins")
    async def balance(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
        target_user = usuario or interaction.user
        # Forzar recarga de datos frescos
        from data_manager import load_data
        data = load_data()
        if "economy" in data and "users" in data["economy"] and str(target_user.id) in data["economy"]["users"]:
            user_economy = data["economy"]["users"][str(target_user.id)]
        else:
            user_economy = economy.get_user_economy(str(target_user.id))
        
        embed = discord.Embed(
            title=f"💰 Balance de {target_user.display_name}",
            color=0x00ff00
        )
        
        embed.add_field(
            name="🪙 GameCoins", 
            value=f"`{user_economy['coins']:,}`", 
            inline=True
        )
        embed.add_field(
            name="📊 Nivel", 
            value=f"`{user_economy['level']}`", 
            inline=True
        )
        embed.add_field(
            name="⭐ XP", 
            value=f"`{user_economy['xp']:,}`", 
            inline=True
        )
        
        embed.add_field(
            name="💎 Total Ganado", 
            value=f"`{user_economy['total_earned']:,}`", 
            inline=True
        )
        embed.add_field(
            name="💸 Total Gastado", 
            value=f"`{user_economy['total_spent']:,}`", 
            inline=True
        )
        embed.add_field(
            name="🎮 Juegos Ganados", 
            value=f"`{user_economy['games_won']}/{user_economy['games_played']}`", 
            inline=True
        )
        
        if user_economy.get('job'):
            job_info = economy.jobs.get(user_economy['job'])
            if job_info:
                embed.add_field(
                    name="💼 Trabajo Actual", 
                    value=job_info['name'], 
                    inline=False
                )
        
        # Obtener ranking
        rank = economy.get_user_rank(str(target_user.id), "coins")
        if rank:
            embed.add_field(
                name="🏆 Ranking Global", 
                value=f"#{rank}", 
                inline=True
            )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.set_footer(text="GameMid Economy System")
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="daily", description="📅 Muestra y reclama tus tareas diarias")
    async def daily(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        daily_tasks = economy.get_daily_tasks(user_id)
        
        embed = discord.Embed(
            title="📅 Tareas Diarias",
            description="Completa estas tareas para ganar GameCoins extra!",
            color=0x3498db
        )
        
        total_possible = 0
        total_claimed = 0
        
        for task_id, task_data in daily_tasks.items():
            if task_id in economy.daily_tasks:
                task_info = economy.daily_tasks[task_id]
                progress = task_data['progress']
                target = task_info['target']
                reward = task_info['reward']
                
                total_possible += reward
                
                # Determinar estado
                if task_data['claimed']:
                    status = "✅ Reclamada"
                    total_claimed += reward
                elif task_data['completed']:
                    status = "🎁 Lista para reclamar"
                else:
                    status = f"📊 {progress}/{target}"
                
                embed.add_field(
                    name=f"{task_info['name']} - {reward} 🪙",
                    value=status,
                    inline=False
                )
        
        embed.add_field(
            name="💰 Progreso Total",
            value=f"{total_claimed}/{total_possible} GameCoins reclamados",
            inline=False
        )
        
        embed.set_footer(text="Usa /claim_task para reclamar recompensas completadas")
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="claim_task", description="🎁 Reclama la recompensa de una tarea completada")
    async def claim_task(interaction: discord.Interaction, 
                        tarea: str):
        user_id = str(interaction.user.id)
        task_id = tarea
        
        reward = economy.claim_task_reward(user_id, task_id)
        
        if reward:
            embed = discord.Embed(
                title="🎉 ¡Recompensa Reclamada!",
                description=f"Has ganado **{reward} GameCoins** por completar: {economy.daily_tasks[task_id]['name']}",
                color=0x00ff00
            )
            
            user_economy = economy.get_user_economy(user_id)
            embed.add_field(
                name="💰 Nuevo Balance",
                value=f"{user_economy['coins']:,} GameCoins",
                inline=True
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No puedes reclamar esta tarea. Asegúrate de que esté completada y no reclamada.",
                color=0xff0000
            )
        
        await interaction.response.send_message(embed=embed)
    
    @claim_task.autocomplete('tarea')
    async def claim_task_autocomplete(interaction: discord.Interaction, current: str):
        user_id = str(interaction.user.id)
        daily_tasks = economy.get_daily_tasks(user_id)
        
        choices = []
        for task_id, task_data in daily_tasks.items():
            if task_data['completed'] and not task_data['claimed']:
                task_name = economy.daily_tasks[task_id]['name']
                choices.append(app_commands.Choice(name=task_name, value=task_id))
        
        return choices[:25]  # Discord limit
    
    @tree.command(name="jobs", description="💼 Muestra los trabajos disponibles")
    async def jobs(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        available_jobs = economy.get_available_jobs(user_id)
        user_economy = economy.get_user_economy(user_id)
        
        embed = discord.Embed(
            title="💼 Centro de Empleos GameMid",
            description="Trabajos disponibles para ganar GameCoins regulares",
            color=0x9b59b6
        )
        
        if user_economy.get('job'):
            current_job = economy.jobs.get(user_economy['job'])
            if current_job:
                embed.add_field(
                    name="🏢 Trabajo Actual",
                    value=f"{current_job['name']}\n💰 Salario: {current_job['salary']} GameCoins\n⏰ Cooldown: {current_job['cooldown']} horas",
                    inline=False
                )
        
        if available_jobs:
            for job in available_jobs:
                requirements = f"Nivel {job['requirements']['level']}"
                if job['requirements']['coins'] > 0:
                    requirements += f", {job['requirements']['coins']} GameCoins"
                
                embed.add_field(
                    name=job['name'],
                    value=f"{job['description']}\n💰 **{job['salary']} GameCoins**\n⏰ Cooldown: {job['cooldown']}h\n📋 Requisitos: {requirements}",
                    inline=True
                )
        else:
            embed.add_field(
                name="❌ Sin trabajos disponibles",
                value="Sube de nivel o gana más GameCoins para desbloquear trabajos",
                inline=False
            )
        
        embed.set_footer(text="Usa /apply_job para aplicar a un trabajo")
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="apply_job", description="📝 Aplica a un trabajo")
    async def apply_job(interaction: discord.Interaction, 
                       trabajo: str):
        user_id = str(interaction.user.id)
        job_id = trabajo
        
        if economy.assign_job(user_id, job_id):
            job_info = economy.jobs[job_id]
            embed = discord.Embed(
                title="🎉 ¡Trabajo Asignado!",
                description=f"Ahora trabajas como: **{job_info['name']}**",
                color=0x00ff00
            )
            embed.add_field(
                name="💰 Salario",
                value=f"{job_info['salary']} GameCoins",
                inline=True
            )
            embed.add_field(
                name="⏰ Cooldown",
                value=f"{job_info['cooldown']} horas",
                inline=True
            )
            embed.add_field(
                name="📋 Descripción",
                value=job_info['description'],
                inline=False
            )
            embed.set_footer(text="Usa /work para trabajar y ganar GameCoins")
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No puedes aplicar a este trabajo. Verifica los requisitos.",
                color=0xff0000
            )
        
        await interaction.response.send_message(embed=embed)
    
    @apply_job.autocomplete('trabajo')
    async def apply_job_autocomplete(interaction: discord.Interaction, current: str):
        user_id = str(interaction.user.id)
        available_jobs = economy.get_available_jobs(user_id)
        
        choices = []
        for job in available_jobs:
            choices.append(app_commands.Choice(name=job['name'], value=job['id']))
        
        return choices[:25]
    
    @tree.command(name="work", description="⚒️ Trabaja para ganar GameCoins")
    async def work(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        result = economy.work(user_id)
        
        if not result:
            embed = discord.Embed(
                title="❌ Sin Trabajo",
                description="No tienes un trabajo asignado. Usa `/jobs` para ver trabajos disponibles.",
                color=0xff0000
            )
        elif "error" in result:
            if result["error"] == "cooldown":
                time_left = result["time_left"]
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                
                embed = discord.Embed(
                    title="⏰ En Cooldown",
                    description=f"Debes esperar **{hours}h {minutes}m** antes de poder trabajar de nuevo.",
                    color=0xffa500
                )
        else:
            embed = discord.Embed(
                title="💼 ¡Trabajo Completado!",
                description=f"Has trabajado como **{result['job_name']}**",
                color=0x00ff00
            )
            
            embed.add_field(
                name="💰 Ganado",
                value=f"{result['earned']} GameCoins",
                inline=True
            )
            embed.add_field(
                name="📊 Desglose",
                value=f"Salario: {result['base_salary']}\nBonus Nivel: +{result['level_bonus']}",
                inline=True
            )
            
            user_economy = economy.get_user_economy(user_id)
            embed.add_field(
                name="💳 Nuevo Balance",
                value=f"{user_economy['coins']:,} GameCoins",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="games", description="🎮 Muestra los minijuegos disponibles")
    async def games(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 Casino GameMid",
            description="¡Juega y gana GameCoins! (O piérdelos... 😅)",
            color=0xe74c3c
        )
        
        for game_id, game_info in economy.minigames.items():
            embed.add_field(
                name=game_info['name'],
                value=f"💰 Apuesta: {game_info['min_bet']}-{game_info['max_bet']} GameCoins",
                inline=True
            )
        
        embed.add_field(
            name="🎯 Comandos Disponibles",
            value="`/coinflip` - Cara o cruz\n`/dice` - Adivina el número\n`/slots` - Tragamonedas\n`/blackjack` - Blackjack interactivo con botones\n`/ruleta` - Ruleta europea\n`/transfer` - Transferir GameCoins",
            inline=False
        )
        
        embed.set_footer(text="¡Juega responsablemente!")
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="coinflip", description="🪙 Juega cara o cruz")
    async def coinflip(interaction: discord.Interaction, 
                      apuesta: int, 
                      eleccion: str):
        user_id = str(interaction.user.id)
        choice = eleccion
        
        result = economy.play_coinflip(user_id, apuesta, choice)
        
        if "error" in result:
            if result["error"] == "invalid_bet":
                embed = discord.Embed(
                    title="❌ Apuesta Inválida",
                    description=f"La apuesta debe estar entre {economy.minigames['coinflip']['min_bet']} y {economy.minigames['coinflip']['max_bet']} GameCoins",
                    color=0xff0000
                )
            else:
                embed = discord.Embed(
                    title="❌ Fondos Insuficientes",
                    description="No tienes suficientes GameCoins para esta apuesta",
                    color=0xff0000
                )
        else:
            coin_emoji = "🟡" if result["result"] == "cara" else "⚪"
            
            if result["won"]:
                embed = discord.Embed(
                    title="🎉 ¡Ganaste!",
                    description=f"La moneda cayó en **{result['result']}** {coin_emoji}",
                    color=0x00ff00
                )
                embed.add_field(
                    name="💰 Ganancia",
                    value=f"+{result['winnings']} GameCoins",
                    inline=True
                )
            else:
                embed = discord.Embed(
                    title="😢 Perdiste",
                    description=f"La moneda cayó en **{result['result']}** {coin_emoji}",
                    color=0xff0000
                )
                embed.add_field(
                    name="💸 Pérdida",
                    value=f"-{result['lost']} GameCoins",
                    inline=True
                )
            
            user_economy = economy.get_user_economy(user_id)
            embed.add_field(
                name="💳 Balance",
                value=f"{user_economy['coins']:,} GameCoins",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
    
    @coinflip.autocomplete('eleccion')
    async def coinflip_autocomplete(interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name="Cara 🟡", value="cara"),
            app_commands.Choice(name="Cruz ⚪", value="cruz")
        ]
    
    @tree.command(name="dice", description="🎲 Adivina el número del dado")
    async def dice(interaction: discord.Interaction, apuesta: int, numero: int):
        if numero < 1 or numero > 6:
            embed = discord.Embed(
                title="❌ Número Inválido",
                description="El número debe estar entre 1 y 6",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        user_id = str(interaction.user.id)
        result = economy.play_dice(user_id, apuesta, numero)
        
        if "error" in result:
            if result["error"] == "invalid_bet":
                embed = discord.Embed(
                    title="❌ Apuesta Inválida",
                    description=f"La apuesta debe estar entre {economy.minigames['dice']['min_bet']} y {economy.minigames['dice']['max_bet']} GameCoins",
                    color=0xff0000
                )
            else:
                embed = discord.Embed(
                    title="❌ Fondos Insuficientes",
                    description="No tienes suficientes GameCoins para esta apuesta",
                    color=0xff0000
                )
        else:
            dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
            dice_emoji = dice_emojis[result["result"] - 1]
            
            if result["won"]:
                embed = discord.Embed(
                    title="🎉 ¡Acertaste!",
                    description=f"El dado mostró **{result['result']}** {dice_emoji}",
                    color=0x00ff00
                )
                embed.add_field(
                    name="💰 Ganancia",
                    value=f"+{result['winnings']} GameCoins (6x)",
                    inline=True
                )
            else:
                embed = discord.Embed(
                    title="😢 Fallaste",
                    description=f"El dado mostró **{result['result']}** {dice_emoji}\nTu predicción: **{numero}**",
                    color=0xff0000
                )
                embed.add_field(
                    name="💸 Pérdida",
                    value=f"-{result['lost']} GameCoins",
                    inline=True
                )
            
            user_economy = economy.get_user_economy(user_id)
            embed.add_field(
                name="💳 Balance",
                value=f"{user_economy['coins']:,} GameCoins",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="slots", description="🎰 Juega a las tragamonedas")
    async def slots(interaction: discord.Interaction, apuesta: int):
        user_id = str(interaction.user.id)
        result = economy.play_slots(user_id, apuesta)
        
        if "error" in result:
            if result["error"] == "invalid_bet":
                embed = discord.Embed(
                    title="❌ Apuesta Inválida",
                    description=f"La apuesta debe estar entre {economy.minigames['slots']['min_bet']} y {economy.minigames['slots']['max_bet']} GameCoins",
                    color=0xff0000
                )
            else:
                embed = discord.Embed(
                    title="❌ Fondos Insuficientes",
                    description="No tienes suficientes GameCoins para esta apuesta",
                    color=0xff0000
                )
        else:
            slots_result = " ".join(result["result"])
            
            embed = discord.Embed(
                title="🎰 Tragamonedas GameMid",
                description=f"**[ {slots_result} ]**",
                color=0x00ff00 if result["won"] else 0xff0000
            )
            
            if result["won"]:
                embed.add_field(
                    name="🎉 ¡Ganaste!",
                    value=f"+{result['winnings']} GameCoins\nMultiplicador: {result['multiplier']}x",
                    inline=True
                )
            else:
                embed.add_field(
                    name="😢 Perdiste",
                    value=f"-{result['lost']} GameCoins",
                    inline=True
                )
            
            user_economy = economy.get_user_economy(user_id)
            embed.add_field(
                name="💳 Balance",
                value=f"{user_economy['coins']:,} GameCoins",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Premios",
                value="💎💎💎 = 10x\n⭐⭐⭐ = 5x\n🍒🍒🍒 = 3x\nDos iguales = 1.5x",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="blackjack", description="🃏 Juega al Blackjack interactivo")
    async def blackjack(interaction: discord.Interaction, apuesta: int):
        from views.blackjack_view import BlackjackView
        
        try:
            user_id = str(interaction.user.id)
            
            # Validar apuesta
            if not economy._validate_bet("blackjack", apuesta):
                embed = discord.Embed(
                    title="❌ Apuesta Inválida",
                    description=f"La apuesta debe estar entre {economy.minigames['blackjack']['min_bet']} y {economy.minigames['blackjack']['max_bet']} GameCoins",
                    color=0xff0000
                )
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar fondos
            if not economy.remove_coins(user_id, apuesta, "Blackjack bet"):
                embed = discord.Embed(
                    title="❌ Fondos Insuficientes",
                    description="No tienes suficientes GameCoins para esta apuesta",
                    color=0xff0000
                )
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Crear vista interactiva
            view = BlackjackView(user_id, apuesta, economy)
            embed = view.create_embed()
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, view=view)
        except discord.NotFound:
            # Interacción expirada, no hacer nada
            print(f"Interacción de blackjack expirada para usuario {interaction.user.id}")
        except Exception as e:
            print(f"Error en comando blackjack: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.response.send_message(
                        "❌ Ha ocurrido un error. Inténtalo de nuevo.",
                        ephemeral=True
                    )
                except:
                    pass
    
    @tree.command(name="transfer", description="💸 Transfiere GameCoins a otro usuario")
    async def transfer(interaction: discord.Interaction, 
                      usuario: discord.Member, 
                      cantidad: int):
        if usuario.id == interaction.user.id:
            embed = discord.Embed(
                title="❌ Error",
                description="No puedes transferirte GameCoins a ti mismo",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        if cantidad <= 0:
            embed = discord.Embed(
                title="❌ Cantidad Inválida",
                description="La cantidad debe ser mayor a 0",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        user_id = str(interaction.user.id)
        target_id = str(usuario.id)
        
        if economy.transfer_coins(user_id, target_id, cantidad):
            embed = discord.Embed(
                title="✅ Transferencia Exitosa",
                description=f"Has transferido **{cantidad:,} GameCoins** a {usuario.mention}",
                color=0x00ff00
            )
            
            sender_economy = economy.get_user_economy(user_id)
            embed.add_field(
                name="💳 Tu Nuevo Balance",
                value=f"{sender_economy['coins']:,} GameCoins",
                inline=True
            )
        else:
            embed = discord.Embed(
                title="❌ Transferencia Fallida",
                description="No tienes suficientes GameCoins para esta transferencia",
                color=0xff0000
            )
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="leaderboard", description="🏆 Muestra el ranking de GameCoins")
    async def leaderboard(interaction: discord.Interaction, 
                         categoria: str = None):
        category = categoria if categoria else "coins"
        leaderboard = economy.get_leaderboard(category, limit=10)
        
        category_names = {
            "coins": "💰 GameCoins",
            "level": "📊 Nivel",
            "total_earned": "💎 Total Ganado",
            "games_won": "🎮 Juegos Ganados"
        }
        
        embed = discord.Embed(
            title=f"🏆 Leaderboard - {category_names.get(category, category)}",
            description="Los mejores usuarios de GameMid",
            color=0xffd700
        )
        
        if not leaderboard:
            embed.add_field(
                name="❌ Sin Datos",
                value="No hay datos disponibles para esta categoría",
                inline=False
            )
        else:
            rank_emojis = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
            
            leaderboard_text = ""
            for entry in leaderboard:
                try:
                    user = interaction.client.get_user(int(entry["user_id"]))
                    username = user.display_name if user else f"Usuario {entry['user_id'][:8]}"
                except:
                    username = f"Usuario {entry['user_id'][:8]}"
                
                emoji = rank_emojis[entry["rank"] - 1] if entry["rank"] <= 10 else "🏅"
                value = f"{entry['value']:,}" if category in ["coins", "total_earned"] else str(entry['value'])
                
                leaderboard_text += f"{emoji} **#{entry['rank']}** {username} - {value}\n"
            
            embed.add_field(
                name="🏆 Top 10",
                value=leaderboard_text,
                inline=False
            )
            
            # Mostrar posición del usuario actual
            user_rank = economy.get_user_rank(str(interaction.user.id), category)
            if user_rank:
                embed.add_field(
                    name="📍 Tu Posición",
                    value=f"#{user_rank}",
                    inline=True
                )
        
        embed.set_footer(text="GameMid Economy System")
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="ruleta", description="🎯 Juega a la ruleta europea (interactiva)")
    async def ruleta(interaction: discord.Interaction):
        from views.roulette_view import RouletteView
        
        try:
            user_id = str(interaction.user.id)
            
            # Verificar que el usuario tenga al menos la apuesta mínima
            user_economy = economy.get_user_economy(user_id)
            min_bet = economy.minigames['roulette']['min_bet']
            
            if user_economy['coins'] < min_bet:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"❌ Necesitas al menos {min_bet:,} GameCoins para jugar a la ruleta.",
                        ephemeral=True
                    )
                return
            
            # Crear la vista interactiva
            view = RouletteView(user_id, economy)
            embed = view.create_embed()
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, view=view)
        except discord.NotFound:
            # Interacción expirada, no hacer nada
            print(f"Interacción de ruleta expirada para usuario {interaction.user.id}")
        except Exception as e:
            print(f"Error en comando ruleta: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.response.send_message(
                        "❌ Ha ocurrido un error. Inténtalo de nuevo.",
                        ephemeral=True
                    )
                except:
                    pass
    
    @tree.command(name="tienda", description="🛒 Abre la tienda virtual de GameCoins")
    async def tienda_virtual(interaction: discord.Interaction):
        """Comando para abrir la tienda virtual de GameCoins"""
        try:
            await interaction.response.defer()
            
            view = VirtualShopView(str(interaction.user.id))
            embed = view.create_embed()
            
            await interaction.followup.send(embed=embed, view=view)
            
            print(f"Usuario {interaction.user.name} (ID: {interaction.user.id}) abrió la tienda virtual")
            
        except Exception as e:
            print(f"Error en comando tienda: {str(e)}")
            if not interaction.response.is_done():
                await interaction.followup.send("❌ Error al abrir la tienda virtual. Intenta de nuevo.", ephemeral=True)
            else:
                await interaction.edit_original_response(content="❌ Error al abrir la tienda virtual. Intenta de nuevo.")
    
    @leaderboard.autocomplete('categoria')
    async def leaderboard_autocomplete(interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name="💰 GameCoins", value="coins"),
            app_commands.Choice(name="📊 Nivel", value="level"),
            app_commands.Choice(name="💎 Total Ganado", value="total_earned"),
            app_commands.Choice(name="🎮 Juegos Ganados", value="games_won")
        ]

    # Event listeners para actualizar progreso de tareas

    async def handle_economy_message(message: discord.Message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        economy.update_task_progress(user_id, "send_messages")
        economy.update_task_progress(user_id, "send_many_messages")

    async def handle_economy_interaction(interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            user_id = str(interaction.user.id)
            economy.update_task_progress(user_id, "use_commands")

    async def handle_economy_reaction(reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        user_id = str(user.id)
        economy.update_task_progress(user_id, "react_messages")

    client.add_listener(handle_economy_message, "on_message")
    client.add_listener(handle_economy_interaction, "on_interaction")
    client.add_listener(handle_economy_reaction, "on_reaction_add")
