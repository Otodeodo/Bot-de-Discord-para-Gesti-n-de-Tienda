import discord
import random
from typing import Dict, List, Tuple

class BlackjackView(discord.ui.View):
    def __init__(self, user_id: str, bet: int, economy_system):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.user_id = user_id
        self.bet = bet
        self.original_bet = bet  # Guardar apuesta original para double
        self.economy = economy_system
        self.game_over = False
        self.can_split = False
        self.has_split = False
        self.can_double = True  # Permitir double en las primeras dos cartas
        self.insurance_offered = False
        self.has_insurance = False
        
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
                value="• **Hit**: Tomar otra carta\n• **Stand**: Plantarse\n• **Split**: Dividir par (si tienes par)\n• **Double**: Doblar apuesta y tomar 1 carta\n• **Insurance**: Seguro si dealer muestra As\n• Objetivo: Llegar a 21 sin pasarse",
                inline=False
            )
        
        return embed
    
    def update_buttons(self):
        """Actualiza el estado de los botones"""
        player_value = self.calculate_hand_value(self.player_hand)
        
        # Deshabilitar botones si el juego terminó o el jugador se pasó de 21
        if self.game_over or player_value > 21:
            for child in self.children:
                child.disabled = True
        else:
            # Hit disponible si no te pasaste y no tienes 21
            self.children[0].disabled = player_value == 21  # Hit
            self.children[1].disabled = False  # Stand - siempre disponible
            
            # Double solo disponible con 2 cartas y fondos suficientes
            if len(self.children) > 2:
                user_economy = self.economy.get_user_economy(self.user_id)
                self.children[2].disabled = not (self.can_double and len(self.player_hand) == 2 and user_economy['coins'] >= self.bet)
            
            # Insurance solo disponible si dealer muestra As y no se ha ofrecido
            if len(self.children) > 3:
                dealer_showing_ace = self.dealer_hand[1][0] == "A"
                self.children[3].disabled = not (dealer_showing_ace and not self.insurance_offered and len(self.player_hand) == 2)
            
            # Split solo disponible si tienes par y no has dividido
            if len(self.children) > 4:
                self.children[4].disabled = not (self.can_split and not self.has_split and len(self.player_hand) == 2)
    
    async def end_game(self, interaction: discord.Interaction):
        """Termina el juego y procesa el resultado"""
        self.game_over = True
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        # Verificar blackjack del dealer primero (para insurance)
        dealer_blackjack = dealer_value == 21 and len(self.dealer_hand) == 2
        
        # Procesar insurance si aplica
        if dealer_blackjack and self.has_insurance:
            # Insurance paga 2:1
            insurance_payout = (self.original_bet // 2) * 3
            self.economy.add_coins(self.user_id, insurance_payout, "Blackjack insurance win")
        
        # El dealer toma cartas hasta 17 (solo si el jugador no se pasó y no tiene blackjack)
        if player_value <= 21 and not dealer_blackjack:
            while dealer_value < 17:
                self.dealer_hand.append(self.deck.pop())
                dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        # Procesar resultado económico
        if player_value > 21:
            # Jugador se pasó - ya perdió la apuesta al inicio
            self.economy._update_game_stats(self.user_id, False)
        elif dealer_blackjack and player_value != 21:
            # Dealer tiene blackjack y jugador no
            self.economy._update_game_stats(self.user_id, False)
        elif dealer_value > 21:
            # Dealer se pasó - jugador gana
            winnings = self.bet * 2
            self.economy.add_coins(self.user_id, winnings, "Blackjack win")
            self.economy._update_game_stats(self.user_id, True)
        elif player_value == 21 and len(self.player_hand) == 2 and not dealer_blackjack:
            # Blackjack natural del jugador
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
        
        # Actualizar progreso de tarea de minijuegos
        self.economy.update_task_progress(self.user_id, "play_minigames")
        
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
        
        # Ya no se puede hacer double después de hit
        self.can_double = False
        
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
    
    @discord.ui.button(label="💰 Double", style=discord.ButtonStyle.success, emoji="⬆️")
    async def double_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Este no es tu juego.", ephemeral=True)
            return
        
        if not self.can_double or len(self.player_hand) != 2:
            await interaction.response.send_message("❌ No puedes doblar en este momento.", ephemeral=True)
            return
        
        # Verificar si tiene fondos para doblar
        user_economy = self.economy.get_user_economy(self.user_id)
        if user_economy['coins'] < self.bet:
            await interaction.response.send_message("❌ No tienes suficientes GameCoins para doblar.", ephemeral=True)
            return
        
        # Cobrar la apuesta adicional
        if not self.economy.remove_coins(self.user_id, self.bet, "Blackjack double bet"):
            await interaction.response.send_message("❌ Error al procesar la apuesta adicional.", ephemeral=True)
            return
        
        # Duplicar apuesta y tomar exactamente una carta
        self.bet *= 2
        self.can_double = False
        self.player_hand.append(self.deck.pop())
        
        # Después de double, automáticamente se hace stand
        await self.end_game(interaction)
    
    @discord.ui.button(label="🛡️ Insurance", style=discord.ButtonStyle.secondary, emoji="🔒")
    async def insurance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("❌ Este no es tu juego.", ephemeral=True)
            return
        
        if self.insurance_offered or self.dealer_hand[1][0] != "A" or len(self.player_hand) != 2:
            await interaction.response.send_message("❌ No puedes tomar seguro en este momento.", ephemeral=True)
            return
        
        # El seguro cuesta la mitad de la apuesta original
        insurance_cost = self.original_bet // 2
        
        # Verificar si tiene fondos para el seguro
        user_economy = self.economy.get_user_economy(self.user_id)
        if user_economy['coins'] < insurance_cost:
            await interaction.response.send_message("❌ No tienes suficientes GameCoins para el seguro.", ephemeral=True)
            return
        
        # Cobrar el seguro
        if not self.economy.remove_coins(self.user_id, insurance_cost, "Blackjack insurance bet"):
            await interaction.response.send_message("❌ Error al procesar el seguro.", ephemeral=True)
            return
        
        self.has_insurance = True
        self.insurance_offered = True
        
        self.update_buttons()
        
        embed = self.create_embed()
        embed.add_field(
            name="🛡️ Seguro Tomado",
            value=f"Seguro de {insurance_cost} GameCoins\nSi el dealer tiene Blackjack, ganarás {insurance_cost * 2} GameCoins",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
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