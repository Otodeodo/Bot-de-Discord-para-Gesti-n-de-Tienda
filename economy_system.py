import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from data_manager import load_data, save_data
import discord
from discord import app_commands

class EconomySystem:
    def __init__(self):
        self.daily_tasks = {
            "send_messages": {"name": "Enviar 10 mensajes", "reward": 50, "target": 10, "type": "counter"},
            "use_commands": {"name": "Usar 5 comandos", "reward": 30, "target": 5, "type": "counter"},
            "react_messages": {"name": "Reaccionar a 15 mensajes", "reward": 40, "target": 15, "type": "counter"},
            "play_minigames": {"name": "Jugar 5 minijuegos", "reward": 75, "target": 5, "type": "counter"},
            "send_many_messages": {"name": "Mandar 50 mensajes", "reward": 120, "target": 50, "type": "counter"}
        }
        
        self.jobs = {
            "moderator_helper": {
                "name": "🛡️ Ayudante de Moderador",
                "description": "Reporta infracciones y ayuda a mantener el orden",
                "salary": 200,
                "cooldown": 4,  # horas
                "requirements": {"level": 5, "coins": 0}
            },
            "event_organizer": {
                "name": "🎉 Organizador de Eventos",
                "description": "Organiza y gestiona eventos del servidor",
                "salary": 300,
                "cooldown": 6,
                "requirements": {"level": 10, "coins": 500}
            },
            "content_creator": {
                "name": "📹 Creador de Contenido",
                "description": "Crea contenido gaming para la comunidad",
                "salary": 400,
                "cooldown": 8,
                "requirements": {"level": 15, "coins": 1000}
            },
            "beta_tester": {
                "name": "🧪 Beta Tester",
                "description": "Prueba nuevas funciones del bot",
                "salary": 250,
                "cooldown": 5,
                "requirements": {"level": 8, "coins": 300}
            }
        }
        
        self.minigames = {
            "coinflip": {"name": "🪙 Cara o Cruz", "min_bet": 10, "max_bet": 500},
            "dice": {"name": "🎲 Dados", "min_bet": 20, "max_bet": 300},
            "slots": {"name": "🎰 Tragamonedas", "min_bet": 50, "max_bet": 1000},
            "blackjack": {"name": "🃏 Blackjack", "min_bet": 30, "max_bet": 800},
            "roulette": {"name": "🎯 Ruleta", "min_bet": 25, "max_bet": 600}
        }

    def get_user_economy(self, user_id: str) -> Dict:
        """Obtiene los datos económicos de un usuario"""
        data = load_data()
        if "economy" not in data:
            data["economy"] = {
                "users": {},
                "global_stats": {
                    "total_coins_in_circulation": 0,
                    "total_games_played": 0,
                    "total_jobs_completed": 0
                }
            }
        
        # Asegurar que existe la estructura de usuarios
        if "users" not in data["economy"]:
            data["economy"]["users"] = {}
        
        if user_id not in data["economy"]["users"]:
            data["economy"]["users"][user_id] = {
                "coins": 100,  # GameCoins iniciales
                "level": 1,
                "xp": 0,
                "daily_tasks": {},
                "last_daily": None,
                "job": None,
                "last_work": None,
                "total_earned": 100,
                "total_spent": 0,
                "games_played": 0,
                "games_won": 0,
                "streak": 0,
                "achievements": [],
                "created_at": datetime.now().isoformat()
            }
            save_data(data)
        
        return data["economy"]["users"][user_id]

    def add_coins(self, user_id: str, amount: int, reason: str = "Unknown") -> int:
        """Añade GameCoins a un usuario"""
        data = load_data()
        user_economy = self.get_user_economy(user_id)
        user_economy["coins"] += amount
        user_economy["total_earned"] += amount
        
        # Añadir XP (1 XP por cada 10 coins ganados)
        xp_gained = amount // 10
        user_economy["xp"] += xp_gained
        
        # Verificar subida de nivel
        old_level = user_economy["level"]
        new_level = self._calculate_level(user_economy["xp"])
        if new_level > old_level:
            user_economy["level"] = new_level
            # Bonus por subir de nivel
            bonus = new_level * 50
            user_economy["coins"] += bonus
            user_economy["total_earned"] += bonus
        
        data["economy"]["users"][user_id] = user_economy
        save_data(data)
        return user_economy["coins"]

    def remove_coins(self, user_id: str, amount: int, reason: str = "Unknown") -> bool:
        """Remueve GameCoins de un usuario"""
        user_economy = self.get_user_economy(user_id)
        if user_economy["coins"] >= amount:
            data = load_data()
            user_economy["coins"] -= amount
            user_economy["total_spent"] += amount
            data["economy"]["users"][user_id] = user_economy
            save_data(data)
            return True
        return False

    def _calculate_level(self, xp: int) -> int:
        """Calcula el nivel basado en XP"""
        return int((xp / 100) ** 0.5) + 1

    def get_daily_tasks(self, user_id: str) -> Dict:
        """Obtiene las tareas diarias del usuario"""
        user_economy = self.get_user_economy(user_id)
        today = datetime.now().date().isoformat()
        
        # Resetear tareas si es un nuevo día
        if user_economy.get("last_daily") != today:
            user_economy["daily_tasks"] = {}
            for task_id, task_info in self.daily_tasks.items():
                user_economy["daily_tasks"][task_id] = {
                    "progress": 0,
                    "completed": False,
                    "claimed": False
                }
            user_economy["last_daily"] = today
            
            data = load_data()
            data["economy"]["users"][user_id] = user_economy
            save_data(data)
        else:
            # Verificar si hay nuevas tareas que agregar
            if "daily_tasks" not in user_economy:
                user_economy["daily_tasks"] = {}
            
            updated = False
            for task_id, task_info in self.daily_tasks.items():
                if task_id not in user_economy["daily_tasks"]:
                    user_economy["daily_tasks"][task_id] = {
                        "progress": 0,
                        "completed": False,
                        "claimed": False
                    }
                    updated = True
            
            if updated:
                data = load_data()
                data["economy"]["users"][user_id] = user_economy
                save_data(data)
        
        return user_economy["daily_tasks"]

    def update_task_progress(self, user_id: str, task_id: str, amount: int = 1) -> bool:
        """Actualiza el progreso de una tarea"""
        if task_id not in self.daily_tasks:
            return False
        
        daily_tasks = self.get_daily_tasks(user_id)
        task = daily_tasks.get(task_id)
        
        if task and not task["completed"]:
            task["progress"] += amount
            target = self.daily_tasks[task_id]["target"]
            
            if task["progress"] >= target:
                task["progress"] = target
                task["completed"] = True
            
            data = load_data()
            data["economy"]["users"][user_id]["daily_tasks"] = daily_tasks
            save_data(data)
            return True
        
        return False

    def claim_task_reward(self, user_id: str, task_id: str) -> Optional[int]:
        """Reclama la recompensa de una tarea completada"""
        daily_tasks = self.get_daily_tasks(user_id)
        task = daily_tasks.get(task_id)
        
        if task and task["completed"] and not task["claimed"]:
            reward = self.daily_tasks[task_id]["reward"]
            self.add_coins(user_id, reward, f"Tarea diaria: {self.daily_tasks[task_id]['name']}")
            
            task["claimed"] = True
            data = load_data()
            data["economy"]["users"][user_id]["daily_tasks"] = daily_tasks
            save_data(data)
            
            return reward
        
        return None

    def get_available_jobs(self, user_id: str) -> List[Dict]:
        """Obtiene los trabajos disponibles para un usuario"""
        user_economy = self.get_user_economy(user_id)
        available = []
        
        for job_id, job_info in self.jobs.items():
            requirements = job_info["requirements"]
            if (user_economy["level"] >= requirements["level"] and 
                user_economy["coins"] >= requirements["coins"]):
                available.append({"id": job_id, **job_info})
        
        return available

    def assign_job(self, user_id: str, job_id: str) -> bool:
        """Asigna un trabajo a un usuario"""
        if job_id not in self.jobs:
            return False
        
        available_jobs = self.get_available_jobs(user_id)
        if not any(job["id"] == job_id for job in available_jobs):
            return False
        
        data = load_data()
        user_economy = self.get_user_economy(user_id)
        user_economy["job"] = job_id
        data["economy"]["users"][user_id] = user_economy
        save_data(data)
        return True

    def work(self, user_id: str) -> Optional[Dict]:
        """Permite al usuario trabajar y ganar dinero"""
        user_economy = self.get_user_economy(user_id)
        job_id = user_economy.get("job")
        
        if not job_id or job_id not in self.jobs:
            return None
        
        # Verificar cooldown
        last_work = user_economy.get("last_work")
        if last_work:
            last_work_time = datetime.fromisoformat(last_work)
            cooldown_hours = self.jobs[job_id]["cooldown"]
            if datetime.now() < last_work_time + timedelta(hours=cooldown_hours):
                time_left = (last_work_time + timedelta(hours=cooldown_hours)) - datetime.now()
                return {"error": "cooldown", "time_left": time_left}
        
        # Calcular salario con variación aleatoria (±20%)
        base_salary = self.jobs[job_id]["salary"]
        variation = random.uniform(0.8, 1.2)
        salary = int(base_salary * variation)
        
        # Bonus por nivel
        level_bonus = user_economy["level"] * 5
        total_earned = salary + level_bonus
        
        self.add_coins(user_id, total_earned, f"Trabajo: {self.jobs[job_id]['name']}")
        
        data = load_data()
        user_economy["last_work"] = datetime.now().isoformat()
        data["economy"]["users"][user_id] = user_economy
        save_data(data)
        
        return {
            "success": True,
            "earned": total_earned,
            "base_salary": salary,
            "level_bonus": level_bonus,
            "job_name": self.jobs[job_id]["name"]
        }

    def play_coinflip(self, user_id: str, bet: int, choice: str) -> Dict:
        """Juego de cara o cruz"""
        if not self._validate_bet("coinflip", bet):
            return {"error": "invalid_bet"}
        
        if not self.remove_coins(user_id, bet, "Coinflip bet"):
            return {"error": "insufficient_funds"}
        
        result = random.choice(["cara", "cruz"])
        won = choice.lower() == result
        
        if won:
            winnings = bet * 2
            self.add_coins(user_id, winnings, "Coinflip win")
            self._update_game_stats(user_id, True)
            self.update_task_progress(user_id, "play_minigames")
            return {"success": True, "result": result, "won": True, "winnings": winnings}
        else:
            self._update_game_stats(user_id, False)
            self.update_task_progress(user_id, "play_minigames")
            return {"success": True, "result": result, "won": False, "lost": bet}

    def play_dice(self, user_id: str, bet: int, guess: int) -> Dict:
        """Juego de dados"""
        if not self._validate_bet("dice", bet) or guess < 1 or guess > 6:
            return {"error": "invalid_bet"}
        
        if not self.remove_coins(user_id, bet, "Dice bet"):
            return {"error": "insufficient_funds"}
        
        result = random.randint(1, 6)
        won = guess == result
        
        if won:
            winnings = bet * 6  # 6x multiplier for exact guess
            self.add_coins(user_id, winnings, "Dice win")
            self._update_game_stats(user_id, True)
            self.update_task_progress(user_id, "play_minigames")
            return {"success": True, "result": result, "won": True, "winnings": winnings}
        else:
            self._update_game_stats(user_id, False)
            self.update_task_progress(user_id, "play_minigames")
            return {"success": True, "result": result, "won": False, "lost": bet}

    def play_slots(self, user_id: str, bet: int) -> Dict:
        """Juego de tragamonedas"""
        if not self._validate_bet("slots", bet):
            return {"error": "invalid_bet"}
        
        if not self.remove_coins(user_id, bet, "Slots bet"):
            return {"error": "insufficient_funds"}
        
        symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎"]
        result = [random.choice(symbols) for _ in range(3)]
        
        # Calcular multiplicador
        if result[0] == result[1] == result[2]:  # Tres iguales
            if result[0] == "💎":
                multiplier = 10
            elif result[0] == "⭐":
                multiplier = 5
            else:
                multiplier = 3
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:  # Dos iguales
            multiplier = 1.5
        else:
            multiplier = 0
        
        if multiplier > 0:
            winnings = int(bet * multiplier)
            self.add_coins(user_id, winnings, "Slots win")
            self._update_game_stats(user_id, True)
            self.update_task_progress(user_id, "play_minigames")
            return {"success": True, "result": result, "won": True, "winnings": winnings, "multiplier": multiplier}
        else:
            self._update_game_stats(user_id, False)
            self.update_task_progress(user_id, "play_minigames")
            return {"success": True, "result": result, "won": False, "lost": bet}

    def play_blackjack(self, user_id: str, bet: int) -> Dict:
        """Juego de Blackjack"""
        if not self._validate_bet("blackjack", bet):
            return {"error": "invalid_bet"}
        
        if not self.remove_coins(user_id, bet, "Blackjack bet"):
            return {"error": "insufficient_funds"}
        
        # Crear baraja
        suits = ["♠️", "♥️", "♦️", "♣️"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        deck = [(rank, suit) for suit in suits for rank in ranks]
        random.shuffle(deck)
        
        # Repartir cartas iniciales
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        # Calcular valores
        def calculate_hand_value(hand):
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
        
        player_value = calculate_hand_value(player_hand)
        dealer_value = calculate_hand_value(dealer_hand)
        
        # Verificar blackjack natural
        player_blackjack = player_value == 21
        dealer_blackjack = dealer_value == 21
        
        if player_blackjack and dealer_blackjack:
            # Empate
            self.add_coins(user_id, bet, "Blackjack tie")
            self._update_game_stats(user_id, False)
            return {
                "success": True, "result": "tie", "won": False, "tied": True,
                "player_hand": player_hand, "dealer_hand": dealer_hand,
                "player_value": player_value, "dealer_value": dealer_value,
                "returned": bet
            }
        elif player_blackjack:
            # Blackjack del jugador
            winnings = int(bet * 2.5)  # Blackjack paga 3:2
            self.add_coins(user_id, winnings, "Blackjack win")
            self._update_game_stats(user_id, True)
            return {
                "success": True, "result": "blackjack", "won": True,
                "player_hand": player_hand, "dealer_hand": dealer_hand,
                "player_value": player_value, "dealer_value": dealer_value,
                "winnings": winnings
            }
        elif dealer_blackjack:
            # Blackjack del dealer
            self._update_game_stats(user_id, False)
            return {
                "success": True, "result": "dealer_blackjack", "won": False,
                "player_hand": player_hand, "dealer_hand": dealer_hand,
                "player_value": player_value, "dealer_value": dealer_value,
                "lost": bet
            }
        
        # Juego normal - el dealer toma cartas hasta 17
        while dealer_value < 17:
            dealer_hand.append(deck.pop())
            dealer_value = calculate_hand_value(dealer_hand)
        
        # Determinar ganador
        if dealer_value > 21:
            # Dealer se pasa
            winnings = bet * 2
            self.add_coins(user_id, winnings, "Blackjack win")
            self._update_game_stats(user_id, True)
            return {
                "success": True, "result": "dealer_bust", "won": True,
                "player_hand": player_hand, "dealer_hand": dealer_hand,
                "player_value": player_value, "dealer_value": dealer_value,
                "winnings": winnings
            }
        elif player_value > dealer_value:
            # Jugador gana
            winnings = bet * 2
            self.add_coins(user_id, winnings, "Blackjack win")
            self._update_game_stats(user_id, True)
            return {
                "success": True, "result": "player_wins", "won": True,
                "player_hand": player_hand, "dealer_hand": dealer_hand,
                "player_value": player_value, "dealer_value": dealer_value,
                "winnings": winnings
            }
        elif player_value == dealer_value:
            # Empate
            self.add_coins(user_id, bet, "Blackjack tie")
            self._update_game_stats(user_id, False)
            return {
                "success": True, "result": "tie", "won": False, "tied": True,
                "player_hand": player_hand, "dealer_hand": dealer_hand,
                "player_value": player_value, "dealer_value": dealer_value,
                "returned": bet
            }
        else:
            # Dealer gana
            self._update_game_stats(user_id, False)
            return {
                "success": True, "result": "dealer_wins", "won": False,
                "player_hand": player_hand, "dealer_hand": dealer_hand,
                "player_value": player_value, "dealer_value": dealer_value,
                "lost": bet
            }

    def _validate_bet(self, game: str, bet: int) -> bool:
        """Valida si la apuesta es válida para el juego"""
        if game not in self.minigames:
            return False
        
        game_info = self.minigames[game]
        return game_info["min_bet"] <= bet <= game_info["max_bet"]

    def play_roulette(self, user_id: str, bet_amount: int, bet_type: str, bet_value: str = None) -> Dict:
        """Juega a la ruleta"""
        import random
        
        # Validar apuesta
        if bet_amount < self.minigames["roulette"]["min_bet"] or bet_amount > self.minigames["roulette"]["max_bet"]:
            return {"error": "invalid_bet"}
        
        user_economy = self.get_user_economy(user_id)
        if user_economy["coins"] < bet_amount:
            return {"error": "insufficient_funds"}
        
        # Quitar la apuesta
        self.remove_coins(user_id, bet_amount, "Roulette bet")
        
        # Generar número ganador (0-36)
        winning_number = random.randint(0, 36)
        
        # Determinar color del número ganador
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        
        if winning_number == 0:
            winning_color = "green"
        elif winning_number in red_numbers:
            winning_color = "red"
        else:
            winning_color = "black"
        
        # Calcular ganancia según el tipo de apuesta
        winnings = 0
        win = False
        
        if bet_type == "number" and bet_value:
            # Apuesta a número específico (paga 35:1)
            if int(bet_value) == winning_number:
                winnings = bet_amount * 36  # 35:1 + apuesta original
                win = True
        elif bet_type == "color":
            # Apuesta a color (paga 1:1)
            if bet_value == winning_color and winning_number != 0:
                winnings = bet_amount * 2  # 1:1 + apuesta original
                win = True
        elif bet_type == "even_odd":
            # Apuesta a par/impar (paga 1:1)
            if winning_number != 0:
                is_even = winning_number % 2 == 0
                if (bet_value == "even" and is_even) or (bet_value == "odd" and not is_even):
                    winnings = bet_amount * 2
                    win = True
        elif bet_type == "high_low":
            # Apuesta a alto/bajo (paga 1:1)
            if winning_number != 0:
                if (bet_value == "low" and 1 <= winning_number <= 18) or (bet_value == "high" and 19 <= winning_number <= 36):
                    winnings = bet_amount * 2
                    win = True
        
        # Añadir ganancias si ganó
        if win:
            self.add_coins(user_id, winnings, "Roulette win")
        
        # Actualizar estadísticas
        user_economy = self.get_user_economy(user_id)
        user_economy["games_played"] += 1
        if win:
            user_economy["games_won"] += 1
        
        # Actualizar progreso de tarea de minijuegos
        self.update_task_progress(user_id, "play_minigames")
        
        data = load_data()
        data["economy"]["users"][user_id] = user_economy
        save_data(data)
        
        return {
            "result": "win" if win else "lose",
            "winning_number": winning_number,
            "winning_color": winning_color,
            "bet_type": bet_type,
            "bet_value": bet_value,
            "winnings": winnings if win else 0,
            "new_balance": user_economy["coins"]
        }

    def _update_game_stats(self, user_id: str, won: bool):
        """Actualiza las estadísticas de juegos del usuario"""
        data = load_data()
        user_economy = self.get_user_economy(user_id)
        
        user_economy["games_played"] += 1
        if won:
            user_economy["games_won"] += 1
            user_economy["streak"] += 1
        else:
            user_economy["streak"] = 0
        
        data["economy"]["users"][user_id] = user_economy
        save_data(data)

    def get_leaderboard(self, category: str = "coins", limit: int = 10) -> List[Dict]:
        """Obtiene el leaderboard de la economía"""
        data = load_data()
        economy_data = data.get("economy", {}).get("users", {})
        
        # Ordenar usuarios según la categoría
        if category == "coins":
            sorted_users = sorted(economy_data.items(), key=lambda x: x[1]["coins"], reverse=True)
        elif category == "level":
            sorted_users = sorted(economy_data.items(), key=lambda x: x[1]["level"], reverse=True)
        elif category == "total_earned":
            sorted_users = sorted(economy_data.items(), key=lambda x: x[1]["total_earned"], reverse=True)
        elif category == "games_won":
            sorted_users = sorted(economy_data.items(), key=lambda x: x[1]["games_won"], reverse=True)
        else:
            return []
        
        leaderboard = []
        for i, (user_id, user_data) in enumerate(sorted_users[:limit]):
            leaderboard.append({
                "rank": i + 1,
                "user_id": user_id,
                "value": user_data[category],
                "level": user_data["level"],
                "coins": user_data["coins"]
            })
        
        return leaderboard

    def transfer_coins(self, from_user: str, to_user: str, amount: int) -> bool:
        """Transfiere GameCoins entre usuarios"""
        if amount <= 0:
            return False
        
        # Verificar que el usuario tenga suficientes coins
        from_economy = self.get_user_economy(from_user)
        if from_economy["coins"] < amount:
            return False
        
        # Realizar la transferencia
        if self.remove_coins(from_user, amount, f"Transfer to {to_user}"):
            self.add_coins(to_user, amount, f"Transfer from {from_user}")
            return True
        
        return False

    def get_user_rank(self, user_id: str, category: str = "coins") -> Optional[int]:
        """Obtiene el ranking de un usuario en una categoría específica"""
        leaderboard = self.get_leaderboard(category, limit=1000)  # Obtener más usuarios para encontrar el rank
        
        for entry in leaderboard:
            if entry["user_id"] == user_id:
                return entry["rank"]
        
        return None

# Instancia global del sistema de economía
economy = EconomySystem()