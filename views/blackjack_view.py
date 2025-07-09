import discord
import random
from typing import Dict, List, Tuple

class BlackjackView(discord.ui.View):
    def __init__(self, user_id: str, bet: int, economy_system):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.user_id = user_id
        self.bet = bet
        self.economy = economy_system
        self.game_over = False
        self.can_split = False
        self.has_split = False
        
        # Crear baraja
        self.suits = ["♠️", "♥️", "♦️", "♣️"]
        self.ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.deck = [(rank, suit) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)
        
        # Repartir cartas iniciales
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        
        # Verificar si se puede dividir (par)
        if self.player_hand[0][0] == self.player_hand[1][0]:
            self.can_split = True
        
        self.update_buttons()
    
    def calculate_hand_value(self, hand: List[Tuple[str, str]]) -> int:
        """Calcula el valor de una mano"""
        value = 0
        aces = 0
        for card, _ in hand:
            if card in ["J", "Q", "K"]:
                value += 10
            elif card == "A":
                aces += 1
                value += 11
            else:
                value += int(card)
        
        # Ajustar ases
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def format_hand(self, hand: List[Tuple[str, str]], hide_first: bool = False) -> str:
        """Formatea una mano para mostrar"""
        if hide_first:
            return f"🂠 {hand[1][0]}{hand[1][1]}"
        return " ".join([f"{card}{suit}" for card, suit in hand])
    
    def create_embed(self) -> discord.Embed:
        """Crea el embed del juego"""
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        if self.game_over:
            # Mostrar todas las cartas del dealer
            dealer_cards = self.format_hand(self.dealer_hand)
            
            # Determinar resultado
            if player_value > 21:
                color = 0xff0000
                title = "🃏 Te pasaste - Perdiste"
                result = f"😢 Tu mano se pasó de 21\n-{self.bet} GameCoins"
            elif dealer_value > 21:
                color = 0x00ff00
                title = "🃏 ¡Ganaste! - Dealer se pasó"
                winnings = self.bet * 2
                result = f"🎉 ¡El dealer se pasó de 21!\n+{winnings} GameCoins"
            elif player_value == 21 and len(self.player_hand) == 2:
                color = 0xffd700
                title = "🃏 ¡BLACKJACK! 🎉"
                winnings = int(self.bet * 2.5)
                result = f"🎉 ¡Blackjack natural!\n+{winnings} GameCoins"
            elif player_value > dealer_value:
                color = 0x00ff00
                title = "🃏 ¡Ganaste!"
                winnings = self.bet * 2
                result = f"🎉 ¡Tu mano es mejor!\n+{winnings} GameCoins"
            elif player_value == dealer_value:
                color = 0xffff00
                title = "🃏 Empate"
                result = f"🤝 Empate - Apuesta devuelta\n+{self.bet} GameCoins"
            else:
                color = 0xff0000
                title = "🃏 Perdiste"
                result = f"😢 El dealer tiene mejor mano\n-{self.bet} GameCoins"
        else:
            # Juego en progreso
            color = 0x0099ff
            title = "🃏 Blackjack - Tu turno"
            dealer_cards = self.format_hand(self.dealer_hand, hide_first=True)
            result = "Elige tu próxima acción:"
        
        embed = discord.Embed(title=title, color=color)
        
        embed.add_field(
            name=f"🎴 Tu mano ({player_value})",
            value=self.format_hand(self.player_hand),
            inline=True
        )
        
        embed.add_field(
            name=f"🎴 Dealer ({dealer_value if self.game_over else '?'})",
            value=dealer_cards,
            inline=True
        )
        
        embed.add_field(
            name="📊 Estado",
            value=result,
            inline=False
        )
        
        if not self.game_over:
            embed.add_field(
                name="🎯 Reglas",
                value="• **Hit**: Tomar otra carta\n• **Stand**: Plantarse\n• **Split**: Dividir par (si tienes par)\n• Objetivo: Llegar a 21 sin pasarse",
                inline=False
            )
        
        return embed
    
    def update_buttons(self):
        """Actualiza el estado de los botones"""
        player_value = self.calculate_hand_value(self.player_hand)
        
        # Deshabilitar botones si el juego terminó o el jugador se pasó
        if self.game_over or player_value >= 21:
            for child in self.children:
                child.disabled = True
        else:
            # Hit siempre disponible si no te pasaste
            self.children[0].disabled = False  # Hit
            self.children[1].disabled = False  # Stand
            
            # Split solo disponible si tienes par y no has dividido
            if hasattr(self, 'children') and len(self.children) > 2:
                self.children[2].disabled = not (self.can_split and not self.has_split and len(self.player_hand) == 2)
    
    async def end_game(self, interaction: discord.Interaction):
        """Termina el juego y procesa el resultado"""
        self.game_over = True
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        # El dealer toma cartas hasta 17 (solo si el jugador no se pasó)
        if player_value <= 21:
            while dealer_value < 17:
                self.dealer_hand.append(self.deck.pop())
                dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        # Procesar resultado económico
        if player_value > 21:
            # Jugador se pasó - ya perdió la apuesta al inicio
            self.economy._update_game_stats(self.user_id, False)
        elif dealer_value > 21:
            # Dealer se pasó - jugador gana
            winnings = self.bet * 2
            self.economy.add_coins(self.user_id, winnings, "Blackjack win")
            self.economy._update_game_stats(self.user_id, True)
        elif player_value == 21 and len(self.player_hand) == 2:
            # Blackjack natural
            winnings = int(self.bet * 2.5)
            self.economy.add_coins(self.user_id, winnings, "Blackjack win")
            self.economy._update_game_stats(self.user_id, True)
        elif player_value > dealer_value:
            # Jugador gana
            winnings = self.bet * 2
            self.economy.add_coins(self.user_id, winnings, "Blackjack win")
            self.economy._update_game_stats(self.user_id, True)
        elif player_value == dealer_value:
            # Empate - devolver apuesta
            self.economy.add_coins(self.user_id, self.bet, "Blackjack tie")
            self.economy._update_game_stats(self.user_id, False)
        else:
            # Dealer gana - ya perdió la apuesta al inicio
            self.economy._update_game_stats(self.user_id, False)
        
        self.update_buttons()
        
        # Mostrar balance actualizado
        user_economy = self.economy.get_user_economy(self.user_id)
        embed = self.create_embed()
        embed.add_field(
            name="💳 Balance",
            value=f"{user_economy['coins']:,} GameCoins",
            inline=True
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🃏 Hit", style=discord.ButtonStyle.primary, emoji="➕")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Este no es tu juego.", ephemeral=True)
            return
        
        # Tomar una carta
        self.player_hand.append(self.deck.pop())
        player_value = self.calculate_hand_value(self.player_hand)
        
        # Verificar si se pasó
        if player_value > 21:
            await self.end_game(interaction)
        else:
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label="✋ Stand", style=discord.ButtonStyle.secondary, emoji="🛑")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Este no es tu juego.", ephemeral=True)
            return
        
        await self.end_game(interaction)
    
    @discord.ui.button(label="✂️ Split", style=discord.ButtonStyle.success, emoji="🔀")
    async def split_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Este no es tu juego.", ephemeral=True)
            return
        
        if not self.can_split or self.has_split or len(self.player_hand) != 2:
            await interaction.response.send_message("❌ No puedes dividir en este momento.", ephemeral=True)
            return
        
        # Verificar si tiene fondos para la segunda apuesta
        user_economy = self.economy.get_user_economy(self.user_id)
        if user_economy['coins'] < self.bet:
            await interaction.response.send_message("❌ No tienes suficientes GameCoins para dividir.", ephemeral=True)
            return
        
        # Cobrar la segunda apuesta
        if not self.economy.remove_coins(self.user_id, self.bet, "Blackjack split bet"):
            await interaction.response.send_message("❌ Error al procesar la segunda apuesta.", ephemeral=True)
            return
        
        # Por simplicidad, en esta implementación el split solo duplica la apuesta
        # y continúa con una sola mano (implementación completa requeriría más lógica)
        self.has_split = True
        self.bet *= 2  # Duplicar apuesta
        
        # Dar una carta adicional
        self.player_hand.append(self.deck.pop())
        
        self.update_buttons()
        
        embed = self.create_embed()
        embed.add_field(
            name="✂️ Split Realizado",
            value=f"Apuesta duplicada a {self.bet} GameCoins\nCarta adicional repartida",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=self)