# 🪙 Sistema de Economía Virtual - GameMid

## 📋 Descripción General

El Sistema de Economía Virtual de GameMid permite a los usuarios ganar, gastar y gestionar **GameCoins**, la moneda virtual del servidor. Incluye tareas diarias, trabajos, minijuegos y un sistema de ranking competitivo.

## 💰 GameCoins

**GameCoins** es la moneda principal del sistema. Los usuarios pueden:
- Ganar GameCoins a través de tareas diarias, trabajos y minijuegos
- Transferir GameCoins a otros usuarios
- Competir en el ranking global
- Subir de nivel basado en su experiencia (XP)

## 📊 Sistema de Niveles

- **Nivel 1-10**: 100 XP por nivel
- **Nivel 11-25**: 200 XP por nivel
- **Nivel 26-50**: 300 XP por nivel
- **Nivel 51+**: 500 XP por nivel

Cada acción en el sistema otorga XP, y subir de nivel desbloquea nuevos trabajos y beneficios.

## 📅 Tareas Diarias

Las tareas se reinician cada día y ofrecen recompensas por actividades comunes:

| Tarea | Objetivo | Recompensa |
|-------|----------|------------|
| 💬 Enviar Mensajes | 10 mensajes | 50 GameCoins |
| ⚡ Usar Comandos | 5 comandos | 30 GameCoins |
| 😀 Reaccionar Mensajes | 5 reacciones | 25 GameCoins |
| 🎮 Jugar Minijuegos | 3 juegos | 75 GameCoins |
| 💼 Trabajar | 2 trabajos | 100 GameCoins |

### Comandos de Tareas
- `/daily` - Ver progreso de tareas diarias
- `/claim_task` - Reclamar recompensas completadas

## 💼 Sistema de Trabajos

Los trabajos proporcionan ingresos regulares con diferentes requisitos:

### Trabajos Disponibles

| Trabajo | Nivel Req. | Costo | Salario | Cooldown |
|---------|------------|-------|---------|----------|
| 🍕 Repartidor de Pizza | 1 | 0 | 50 | 2h |
| 🛒 Cajero de Tienda | 3 | 100 | 75 | 3h |
| 👨‍💻 Programador Junior | 5 | 500 | 120 | 4h |
| 🏢 Gerente de Oficina | 10 | 1000 | 200 | 6h |
| 💎 CEO de Empresa | 20 | 5000 | 500 | 12h |

### Comandos de Trabajo
- `/jobs` - Ver trabajos disponibles
- `/apply_job` - Aplicar a un trabajo
- `/work` - Trabajar para ganar GameCoins

## 🎮 Minijuegos

Tres emocionantes juegos de azar para ganar (o perder) GameCoins:

### 🪙 Coinflip
- **Apuesta**: 10-1000 GameCoins
- **Mecánica**: Elige cara o cruz
- **Payout**: 2x la apuesta si aciertas

### 🎲 Dice
- **Apuesta**: 10-500 GameCoins
- **Mecánica**: Adivina el número del dado (1-6)
- **Payout**: 6x la apuesta si aciertas

### 🎰 Slots
- **Apuesta**: 25-2000 GameCoins
- **Mecánica**: Tragamonedas con símbolos
- **Payouts**:
  - 💎💎💎 = 10x
  - ⭐⭐⭐ = 5x
  - 🍒🍒🍒 = 3x
  - Dos iguales = 1.5x

### Comandos de Juegos
- `/games` - Ver juegos disponibles
- `/coinflip <apuesta> <elección>` - Jugar cara o cruz
- `/dice <apuesta> <número>` - Jugar dados
- `/slots <apuesta>` - Jugar tragamonedas

## 🏆 Sistema de Ranking

Compite con otros usuarios en diferentes categorías:

- **💰 GameCoins**: Total de monedas actuales
- **📊 Nivel**: Nivel más alto alcanzado
- **💎 Total Ganado**: GameCoins ganados históricamente
- **🎮 Juegos Ganados**: Victorias en minijuegos

### Comandos de Ranking
- `/leaderboard [categoría]` - Ver el top 10 global

## 💸 Transferencias

Los usuarios pueden transferir GameCoins entre sí:

- `/transfer <usuario> <cantidad>` - Transferir GameCoins
- Sin comisiones ni límites (excepto el balance disponible)
- Perfecto para regalos, pagos o intercambios

## 📊 Comandos Principales

### Información Personal
- `/balance [usuario]` - Ver balance y estadísticas
- `/daily` - Ver tareas diarias
- `/jobs` - Ver trabajos disponibles

### Acciones
- `/work` - Trabajar en tu empleo actual
- `/apply_job <trabajo>` - Aplicar a un trabajo
- `/claim_task <tarea>` - Reclamar recompensa de tarea

### Juegos
- `/games` - Ver minijuegos disponibles
- `/coinflip <apuesta> <cara/cruz>` - Cara o cruz
- `/dice <apuesta> <número>` - Adivinar dado
- `/slots <apuesta>` - Tragamonedas

### Social
- `/transfer <usuario> <cantidad>` - Transferir GameCoins
- `/leaderboard [categoría]` - Ver rankings

## 🔧 Características Técnicas

### Persistencia de Datos
- Todos los datos se guardan automáticamente
- Respaldo en `data.json`
- Sincronización en tiempo real

### Sistema de Cooldowns
- Trabajos tienen cooldowns individuales
- Tareas diarias se reinician a medianoche
- Prevención de spam y explotación

### Balanceado Económico
- Límites de apuesta en minijuegos
- Requisitos progresivos para trabajos
- Recompensas escaladas por nivel

### Integración con Discord
- Comandos slash nativos
- Embeds ricos y coloridos
- Autocompletado inteligente
- Menciones y notificaciones

## 🎯 Estrategias Recomendadas

1. **Principiantes**: Completa tareas diarias y trabaja como repartidor
2. **Nivel Medio**: Ahorra para trabajos mejor pagados, juega conservadoramente
3. **Avanzados**: Optimiza trabajos de alto nivel, domina los minijuegos
4. **Expertos**: Lidera rankings, ayuda a nuevos usuarios con transferencias

## 🚀 Futuras Expansiones

- 🏪 **Tienda Virtual**: Comprar roles, beneficios y items especiales
- 🏆 **Torneos**: Competencias programadas con grandes premios
- 🎁 **Eventos Especiales**: Bonificaciones temporales y eventos únicos
- 📈 **Inversiones**: Sistema de acciones y mercado virtual
- 🏘️ **Propiedades**: Comprar y gestionar propiedades virtuales

---

**¡Disfruta del Sistema de Economía Virtual de GameMid!** 🎮💰

*Para soporte o sugerencias, contacta a los administradores del servidor.*