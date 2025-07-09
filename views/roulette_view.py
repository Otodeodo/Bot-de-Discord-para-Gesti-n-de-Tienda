import discord
import random
from typing import Dict, List

class RouletteView(discord.ui.View):
    def __init__(self, user_id: str, economy_system):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.user_id = user_id
        self.economy = economy_system
        self.bet_amount = 0
        self.bet_type = None
        self.bet_value = None
        self.game_started = False
        self.game_over = False
        
        # Números rojos y negros de la ruleta europea
        self.red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        self.black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        
        self.update_buttons()
    
    def update_buttons(self):
        """Actualiza el estado de los botones"""
        self.clear_items()
        
        if self.game_over:
            # Botón para jugar de nuevo
            new_game_button = discord.ui.Button(
                label="🎯 Nueva Partida",
                style=discord.ButtonStyle.primary,
                custom_id="new_game"
            )
            new_game_button.callback = self.new_game
            self.add_item(new_game_button)
            return
        
        if not self.game_started:
            # Botones para seleccionar tipo de apuesta
            color_button = discord.ui.Button(
                label="🎨 Color (Rojo/Negro)",
                style=discord.ButtonStyle.secondary,
                custom_id="color_bet"
            )
            color_button.callback = self.color_bet
            self.add_item(color_button)
            
            even_odd_button = discord.ui.Button(
                label="🔢 Par/Impar",
                style=discord.ButtonStyle.secondary,
                custom_id="even_odd_bet"
            )
            even_odd_button.callback = self.even_odd_bet
            self.add_item(even_odd_button)
            
            high_low_button = discord.ui.Button(
                label="📊 Alto/Bajo",
                style=discord.ButtonStyle.secondary,
                custom_id="high_low_bet"
            )
            high_low_button.callback = self.high_low_bet
            self.add_item(high_low_button)
            
            number_button = discord.ui.Button(
                label="🎯 Número Específico",
                style=discord.ButtonStyle.secondary,
                custom_id="number_bet"
            )
            number_button.callback = self.number_bet
            self.add_item(number_button)
        
        elif self.bet_type and not self.bet_value:
            # Botones específicos según el tipo de apuesta
            if self.bet_type == "color":
                red_button = discord.ui.Button(
                    label="🔴 Rojo",
                    style=discord.ButtonStyle.danger,
                    custom_id="red"
                )
                red_button.callback = lambda i: self.set_bet_value(i, "red")
                self.add_item(red_button)
                
                black_button = discord.ui.Button(
                    label="⚫ Negro",
                    style=discord.ButtonStyle.secondary,
                    custom_id="black"
                )
                black_button.callback = lambda i: self.set_bet_value(i, "black")
                self.add_item(black_button)
            
            elif self.bet_type == "even_odd":
                even_button = discord.ui.Button(
                    label="🔢 Par",
                    style=discord.ButtonStyle.primary,
                    custom_id="even"
                )
                even_button.callback = lambda i: self.set_bet_value(i, "even")
                self.add_item(even_button)
                
                odd_button = discord.ui.Button(
                    label="🔢 Impar",
                    style=discord.ButtonStyle.secondary,
                    custom_id="odd"
                )
                odd_button.callback = lambda i: self.set_bet_value(i, "odd")
                self.add_item(odd_button)
            
            elif self.bet_type == "high_low":
                low_button = discord.ui.Button(
                    label="📉 Bajo (1-18)",
                    style=discord.ButtonStyle.secondary,
                    custom_id="low"
                )
                low_button.callback = lambda i: self.set_bet_value(i, "low")
                self.add_item(low_button)
                
                high_button = discord.ui.Button(
                    label="📈 Alto (19-36)",
                    style=discord.ButtonStyle.primary,
                    custom_id="high"
                )
                high_button.callback = lambda i: self.set_bet_value(i, "high")
                self.add_item(high_button)
        
        # Botón de cancelar (siempre disponible si no ha terminado)
        if not self.game_over:
            cancel_button = discord.ui.Button(
                label="❌ Cancelar",
                style=discord.ButtonStyle.danger,
                custom_id="cancel"
            )
            cancel_button.callback = self.cancel_game
            self.add_item(cancel_button)
    
    def create_embed(self) -> discord.Embed:
        """Crea el embed para mostrar el estado del juego"""
        if self.game_over:
            return self.create_result_embed()
        
        if not self.game_started:
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
            
        elif self.bet_type and not self.bet_value:
            embed = discord.Embed(
                title=f"🎯 Ruleta - {self.get_bet_type_name()}",
                description=f"Has elegido apostar a **{self.get_bet_type_name()}**\nAhora selecciona tu opción específica:",
                color=0x9b59b6
            )
            
        else:
            embed = discord.Embed(
                title="🎯 Ruleta - Configurando Apuesta",
                description="Configurando tu apuesta...",
                color=0x9b59b6
            )
        
        embed.set_footer(text="🎯 Ruleta Europea • GameMid Casino")
        return embed
    
    def create_result_embed(self) -> discord.Embed:
        """Crea el embed con el resultado del juego"""
        # Este método se llamará después de girar la ruleta
        pass
    
    def get_bet_type_name(self) -> str:
        """Obtiene el nombre legible del tipo de apuesta"""
        names = {
            "color": "Color (Rojo/Negro)",
            "even_odd": "Par/Impar",
            "high_low": "Alto/Bajo",
            "number": "Número Específico"
        }
        return names.get(self.bet_type, "Desconocido")
    
    async def color_bet(self, interaction: discord.Interaction):
        """Maneja la selección de apuesta por color"""
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        self.bet_type = "color"
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def even_odd_bet(self, interaction: discord.Interaction):
        """Maneja la selección de apuesta par/impar"""
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        self.bet_type = "even_odd"
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def high_low_bet(self, interaction: discord.Interaction):
        """Maneja la selección de apuesta alto/bajo"""
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        self.bet_type = "high_low"
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def number_bet(self, interaction: discord.Interaction):
        """Maneja la selección de apuesta por número específico"""
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        # Para números específicos, mostrar modal para ingresar el número
        modal = NumberBetModal(self)
        await interaction.response.send_modal(modal)
    
    async def set_bet_value(self, interaction: discord.Interaction, value: str):
        """Establece el valor específico de la apuesta"""
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        self.bet_value = value
        # Mostrar modal para ingresar la cantidad de apuesta
        modal = BetAmountModal(self)
        await interaction.response.send_modal(modal)
    
    async def cancel_game(self, interaction: discord.Interaction):
        """Cancela el juego"""
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="❌ Juego Cancelado",
            description="Has cancelado la partida de ruleta.",
            color=0xff0000
        )
        embed.set_footer(text="🎯 Ruleta Europea • GameMid Casino")
        
        self.game_over = True
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def new_game(self, interaction: discord.Interaction):
        """Inicia una nueva partida"""
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Esta no es tu partida.", ephemeral=True)
            return
        
        # Reiniciar el estado del juego
        self.bet_amount = 0
        self.bet_type = None
        self.bet_value = None
        self.game_started = False
        self.game_over = False
        
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def spin_roulette(self, bet_amount: int):
        """Gira la ruleta y determina el resultado"""
        self.bet_amount = bet_amount
        self.game_started = True
        
        # Usar la función del sistema de economía
        result = self.economy.play_roulette(self.user_id, bet_amount, self.bet_type, self.bet_value)
        
        # Crear embed con el resultado
        winning_number = result['winning_number']
        winning_color = result['winning_color']
        
        color_emoji = {
            "red": "🔴",
            "black": "⚫",
            "green": "🟢"
        }
        
        bet_descriptions = {
            "color": f"Color {self.bet_value}",
            "even_odd": f"{'Par' if self.bet_value == 'even' else 'Impar'}",
            "high_low": f"{'Alto (19-36)' if self.bet_value == 'high' else 'Bajo (1-18)'}",
            "number": f"Número {self.bet_value}"
        }
        
        if result["result"] == "win":
            embed = discord.Embed(
                title="🎯 ¡GANASTE EN LA RULETA!",
                description=f"🎊 La bola cayó en: **{winning_number}** {color_emoji[winning_color]}",
                color=0x00ff00
            )
            embed.add_field(
                name="💰 Ganancias",
                value=f"+{result['winnings']:,} GameCoins",
                inline=True
            )
        else:
            embed = discord.Embed(
                title="🎯 Perdiste en la Ruleta",
                description=f"😔 La bola cayó en: **{winning_number}** {color_emoji[winning_color]}",
                color=0xff0000
            )
            embed.add_field(
                name="💸 Pérdida",
                value=f"-{bet_amount:,} GameCoins",
                inline=True
            )
        
        embed.add_field(
            name="🎲 Tu Apuesta",
            value=f"{bet_descriptions[self.bet_type]}\n{bet_amount:,} GameCoins",
            inline=True
        )
        embed.add_field(
            name="💳 Nuevo Balance",
            value=f"{result['new_balance']:,} GameCoins",
            inline=True
        )
        
        embed.add_field(
            name="💡 Información de Pagos",
            value="🔢 Número específico: 35:1\n🎨 Color (rojo/negro): 1:1\n🔢 Par/Impar: 1:1\n📊 Alto/Bajo: 1:1",
            inline=False
        )
        
        embed.set_footer(text="🎯 Ruleta Europea • GameMid Casino")
        
        self.game_over = True
        self.update_buttons()
        
        return embed

class BetAmountModal(discord.ui.Modal):
    def __init__(self, roulette_view):
        super().__init__(title="💰 Cantidad de Apuesta")
        self.roulette_view = roulette_view
        
        self.bet_input = discord.ui.TextInput(
            label="Cantidad de GameCoins",
            placeholder=f"Entre {roulette_view.economy.minigames['roulette']['min_bet']} y {roulette_view.economy.minigames['roulette']['max_bet']}",
            min_length=1,
            max_length=10
        )
        self.add_item(self.bet_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet_amount = int(self.bet_input.value)
            
            # Validar apuesta
            min_bet = self.roulette_view.economy.minigames['roulette']['min_bet']
            max_bet = self.roulette_view.economy.minigames['roulette']['max_bet']
            
            if bet_amount < min_bet or bet_amount > max_bet:
                await interaction.response.send_message(
                    f"❌ La apuesta debe estar entre {min_bet} y {max_bet} GameCoins.",
                    ephemeral=True
                )
                return
            
            # Verificar fondos
            user_economy = self.roulette_view.economy.get_user_economy(self.roulette_view.user_id)
            if user_economy['coins'] < bet_amount:
                await interaction.response.send_message(
                    "❌ No tienes suficientes GameCoins para esta apuesta.",
                    ephemeral=True
                )
                return
            
            # Girar la ruleta
            result_embed = await self.roulette_view.spin_roulette(bet_amount)
            await interaction.response.edit_message(embed=result_embed, view=self.roulette_view)
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Por favor ingresa un número válido.",
                ephemeral=True
            )

class NumberBetModal(discord.ui.Modal):
    def __init__(self, roulette_view):
        super().__init__(title="🎯 Apuesta por Número")
        self.roulette_view = roulette_view
        
        self.number_input = discord.ui.TextInput(
            label="Número (0-36)",
            placeholder="Ingresa un número entre 0 y 36",
            min_length=1,
            max_length=2
        )
        self.add_item(self.number_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            number = int(self.number_input.value)
            
            if number < 0 or number > 36:
                await interaction.response.send_message(
                    "❌ El número debe estar entre 0 y 36.",
                    ephemeral=True
                )
                return
            
            self.roulette_view.bet_type = "number"
            self.roulette_view.bet_value = str(number)
            
            # Mostrar modal para la cantidad de apuesta
            bet_modal = BetAmountModal(self.roulette_view)
            await interaction.response.send_modal(bet_modal)
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Por favor ingresa un número válido.",
                ephemeral=True
            )