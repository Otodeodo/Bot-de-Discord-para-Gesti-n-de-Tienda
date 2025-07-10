import discord
import random
from typing import Dict, List

class RouletteView(discord.ui.View):
    def __init__(self, user_id: str, economy_system):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.user_id = str(user_id)
        self.economy = economy_system
        self.bet_amount = 0
        self.bet_type = None
        self.bet_value = None
        self.game_started = False
        self.game_over = False
        
        # Números rojos y negros de la ruleta europea
        self.red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        self.black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        
        self.create_initial_buttons()
    
    def create_initial_buttons(self):
        """Crea los botones iniciales para seleccionar tipo de apuesta"""
        self.clear_items()
        
        # Botón Color
        color_btn = discord.ui.Button(
            label="🎨 Color (Rojo/Negro)",
            style=discord.ButtonStyle.secondary,
            custom_id="color"
        )
        color_btn.callback = self.handle_color_selection
        self.add_item(color_btn)
        
        # Botón Par/Impar
        even_odd_btn = discord.ui.Button(
            label="🔢 Par/Impar",
            style=discord.ButtonStyle.secondary,
            custom_id="even_odd"
        )
        even_odd_btn.callback = self.handle_even_odd_selection
        self.add_item(even_odd_btn)
        
        # Botón Alto/Bajo
        high_low_btn = discord.ui.Button(
            label="📊 Alto/Bajo",
            style=discord.ButtonStyle.secondary,
            custom_id="high_low"
        )
        high_low_btn.callback = self.handle_high_low_selection
        self.add_item(high_low_btn)
        
        # Botón Número Específico
        number_btn = discord.ui.Button(
            label="🎯 Número Específico",
            style=discord.ButtonStyle.secondary,
            custom_id="number"
        )
        number_btn.callback = self.handle_number_selection
        self.add_item(number_btn)
        
        # Botón Cancelar
        cancel_btn = discord.ui.Button(
            label="❌ Cancelar",
            style=discord.ButtonStyle.danger,
            custom_id="cancel"
        )
        cancel_btn.callback = self.handle_cancel
        self.add_item(cancel_btn)
    
    async def handle_color_selection(self, interaction: discord.Interaction):
        """Maneja la selección de apuesta por color"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        self.bet_type = "color"
        self.create_color_buttons()
        embed = self.create_selection_embed("Color (Rojo/Negro)", "Selecciona rojo o negro:")
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def handle_even_odd_selection(self, interaction: discord.Interaction):
        """Maneja la selección de apuesta par/impar"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        self.bet_type = "even_odd"
        self.create_even_odd_buttons()
        embed = self.create_selection_embed("Par/Impar", "Selecciona par o impar:")
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def handle_high_low_selection(self, interaction: discord.Interaction):
        """Maneja la selección de apuesta alto/bajo"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        self.bet_type = "high_low"
        self.create_high_low_buttons()
        embed = self.create_selection_embed("Alto/Bajo", "Selecciona alto (19-36) o bajo (1-18):")
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def handle_number_selection(self, interaction: discord.Interaction):
        """Maneja la selección de número específico"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        modal = NumberBetModal(self)
        await interaction.response.send_modal(modal)
    
    def create_color_buttons(self):
        """Crea botones para selección de color"""
        self.clear_items()
        
        red_btn = discord.ui.Button(
            label="🔴 Rojo",
            style=discord.ButtonStyle.danger,
            custom_id="red"
        )
        red_btn.callback = lambda i: self.handle_bet_value_selection(i, "red")
        self.add_item(red_btn)
        
        black_btn = discord.ui.Button(
            label="⚫ Negro",
            style=discord.ButtonStyle.secondary,
            custom_id="black"
        )
        black_btn.callback = lambda i: self.handle_bet_value_selection(i, "black")
        self.add_item(black_btn)
        
        self.add_back_button()
    
    def create_even_odd_buttons(self):
        """Crea botones para selección par/impar"""
        self.clear_items()
        
        even_btn = discord.ui.Button(
            label="🔢 Par",
            style=discord.ButtonStyle.primary,
            custom_id="even"
        )
        even_btn.callback = lambda i: self.handle_bet_value_selection(i, "even")
        self.add_item(even_btn)
        
        odd_btn = discord.ui.Button(
            label="🔢 Impar",
            style=discord.ButtonStyle.secondary,
            custom_id="odd"
        )
        odd_btn.callback = lambda i: self.handle_bet_value_selection(i, "odd")
        self.add_item(odd_btn)
        
        self.add_back_button()
    
    def create_high_low_buttons(self):
        """Crea botones para selección alto/bajo"""
        self.clear_items()
        
        low_btn = discord.ui.Button(
            label="📉 Bajo (1-18)",
            style=discord.ButtonStyle.secondary,
            custom_id="low"
        )
        low_btn.callback = lambda i: self.handle_bet_value_selection(i, "low")
        self.add_item(low_btn)
        
        high_btn = discord.ui.Button(
            label="📈 Alto (19-36)",
            style=discord.ButtonStyle.primary,
            custom_id="high"
        )
        high_btn.callback = lambda i: self.handle_bet_value_selection(i, "high")
        self.add_item(high_btn)
        
        self.add_back_button()
    
    def add_back_button(self):
        """Agrega botón para volver atrás"""
        back_btn = discord.ui.Button(
            label="⬅️ Volver",
            style=discord.ButtonStyle.secondary,
            custom_id="back"
        )
        back_btn.callback = self.handle_back
        self.add_item(back_btn)
        
        cancel_btn = discord.ui.Button(
            label="❌ Cancelar",
            style=discord.ButtonStyle.danger,
            custom_id="cancel"
        )
        cancel_btn.callback = self.handle_cancel
        self.add_item(cancel_btn)
    
    async def handle_bet_value_selection(self, interaction: discord.Interaction, value: str):
        """Maneja la selección del valor específico de apuesta"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        self.bet_value = value
        modal = BetAmountModal(self)
        await interaction.response.send_modal(modal)
    
    async def handle_back(self, interaction: discord.Interaction):
        """Maneja el botón de volver atrás"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        self.bet_type = None
        self.bet_value = None
        self.create_initial_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def handle_cancel(self, interaction: discord.Interaction):
        """Maneja la cancelación del juego"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎯 Ruleta Cancelada",
            description="Has cancelado la partida de ruleta.",
            color=0xe74c3c
        )
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)
    
    def create_embed(self) -> discord.Embed:
        """Crea el embed principal del juego"""
        if self.game_over:
            return self.create_result_embed()
        
        embed = discord.Embed(
            title="🎯 Ruleta Europea - Selecciona tu Apuesta",
            description="Elige el tipo de apuesta que quieres hacer:",
            color=0x9b59b6
        )
        
        user_economy = self.economy.get_user_economy(self.user_id)
        embed.add_field(
            name="💰 Tu Balance",
            value=f"{user_economy['coins']:,} GameCoins",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Rango de Apuestas",
            value=f"{self.economy.minigames['roulette']['min_bet']}-{self.economy.minigames['roulette']['max_bet']} GameCoins",
            inline=True
        )
        
        embed.add_field(
            name="💡 Tipos de Apuesta",
            value="🎨 **Color**: Rojo/Negro (1:1)\n🔢 **Par/Impar**: Even/Odd (1:1)\n📊 **Alto/Bajo**: 1-18/19-36 (1:1)\n🎯 **Número**: 0-36 (35:1)",
            inline=False
        )
        
        embed.set_footer(text="🎯 Ruleta Europea • GameMid Casino")
        return embed
    
    def create_selection_embed(self, bet_type: str, description: str) -> discord.Embed:
        """Crea embed para selección específica"""
        embed = discord.Embed(
            title=f"🎯 Ruleta - {bet_type}",
            description=description,
            color=0x9b59b6
        )
        embed.set_footer(text="🎯 Ruleta Europea • GameMid Casino")
        return embed
    
    def create_result_embed(self) -> discord.Embed:
        """Crea el embed con el resultado del juego"""
        # Este método se implementará cuando se complete el juego
        pass
    
    async def spin_roulette(self, bet_amount: int):
        """Ejecuta el giro de la ruleta"""
        try:
            result = self.economy.play_roulette(self.user_id, bet_amount, self.bet_type, self.bet_value)
            
            # Crear embed de resultado
            if result['result'] == 'win':
                color = 0x2ecc71  # Verde
                title = "🎉 ¡Ganaste!"
            else:
                color = 0xe74c3c  # Rojo
                title = "😔 Perdiste"
            
            embed = discord.Embed(
                title=title,
                color=color
            )
            
            embed.add_field(
                name="🎯 Número Ganador",
                value=f"**{result['winning_number']}**",
                inline=True
            )
            
            embed.add_field(
                name="🎨 Color",
                value="🔴 Rojo" if result['winning_number'] in self.red_numbers else "⚫ Negro" if result['winning_number'] != 0 else "🟢 Verde",
                inline=True
            )
            
            embed.add_field(
                name="💰 Resultado",
                value=f"{result['winnings']:+,} GameCoins",
                inline=True
            )
            
            embed.add_field(
                name="🏦 Balance Final",
                value=f"{result['new_balance']:,} GameCoins",
                inline=True
            )
            
            self.game_over = True
            self.create_new_game_button()
            
            return embed
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=0xe74c3c
            )
            return embed
    
    def create_new_game_button(self):
        """Crea botón para nueva partida"""
        self.clear_items()
        
        new_game_btn = discord.ui.Button(
            label="🎯 Nueva Partida",
            style=discord.ButtonStyle.primary,
            custom_id="new_game"
        )
        new_game_btn.callback = self.handle_new_game
        self.add_item(new_game_btn)
    
    async def handle_new_game(self, interaction: discord.Interaction):
        """Maneja el inicio de una nueva partida"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        # Reiniciar estado del juego
        self.bet_amount = 0
        self.bet_type = None
        self.bet_value = None
        self.game_started = False
        self.game_over = False
        
        self.create_initial_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

class NumberBetModal(discord.ui.Modal):
    def __init__(self, roulette_view):
        super().__init__(title="🎯 Número Específico")
        self.roulette_view = roulette_view
        
        self.number_input = discord.ui.TextInput(
            label="Número (0-36)",
            placeholder="Ingresa un número del 0 al 36",
            min_length=1,
            max_length=2,
            required=True
        )
        self.add_item(self.number_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            number = int(self.number_input.value)
            if not (0 <= number <= 36):
                await interaction.response.send_message(
                    "❌ El número debe estar entre 0 y 36.",
                    ephemeral=True
                )
                return
            
            self.roulette_view.bet_type = "number"
            self.roulette_view.bet_value = str(number)
            
            embed = discord.Embed(
                title="🎯 Número Seleccionado",
                description=f"Has seleccionado el número **{number}**\n\nAhora ingresa tu apuesta:",
                color=0x9b59b6
            )
            
            # Crear botón para abrir modal de apuesta
            view = discord.ui.View()
            bet_btn = discord.ui.Button(
                label="💰 Ingresar Apuesta",
                style=discord.ButtonStyle.primary
            )
            bet_btn.callback = lambda i: self.open_bet_modal(i)
            view.add_item(bet_btn)
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Por favor ingresa un número válido.",
                ephemeral=True
            )
    
    async def open_bet_modal(self, interaction: discord.Interaction):
        modal = BetAmountModal(self.roulette_view)
        await interaction.response.send_modal(modal)

class BetAmountModal(discord.ui.Modal):
    def __init__(self, roulette_view):
        super().__init__(title="💰 Cantidad de Apuesta")
        self.roulette_view = roulette_view
        
        min_bet = roulette_view.economy.minigames['roulette']['min_bet']
        max_bet = roulette_view.economy.minigames['roulette']['max_bet']
        
        self.amount_input = discord.ui.TextInput(
            label=f"Cantidad ({min_bet:,} - {max_bet:,} GameCoins)",
            placeholder=f"Ingresa tu apuesta (mín: {min_bet:,})",
            min_length=1,
            max_length=10,
            required=True
        )
        self.add_item(self.amount_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value.replace(',', '').replace('.', ''))
            min_bet = self.roulette_view.economy.minigames['roulette']['min_bet']
            max_bet = self.roulette_view.economy.minigames['roulette']['max_bet']
            
            if amount < min_bet or amount > max_bet:
                await interaction.response.send_message(
                    f"❌ La apuesta debe estar entre {min_bet:,} y {max_bet:,} GameCoins.",
                    ephemeral=True
                )
                return
            
            user_economy = self.roulette_view.economy.get_user_economy(self.roulette_view.user_id)
            if amount > user_economy['coins']:
                await interaction.response.send_message(
                    "❌ No tienes suficientes GameCoins para esta apuesta.",
                    ephemeral=True
                )
                return
            
            # Ejecutar el giro de la ruleta
            result_embed = await self.roulette_view.spin_roulette(amount)
            await interaction.response.edit_message(embed=result_embed, view=self.roulette_view)
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Por favor ingresa una cantidad válida.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )