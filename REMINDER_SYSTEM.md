# 🔔 Sistema de Recordatorios Automáticos de Robux

## 📋 Descripción

El Sistema de Recordatorios Automáticos es una funcionalidad que notifica automáticamente a los usuarios cuando sus cuentas de Roblox cumplen 15 días y se vuelven elegibles para recibir Robux.

## ⚙️ Funcionamiento

### 🔄 Proceso Automático

1. **Verificación Diaria**: El sistema se ejecuta cada 24 horas
2. **Análisis de Cuentas**: Revisa todas las cuentas de Roblox vinculadas
3. **Cálculo de Elegibilidad**: Determina qué usuarios cumplen exactamente 15 días
4. **Envío de Recordatorios**: Envía mensajes directos a usuarios elegibles
5. **Registro de Notificaciones**: Marca a los usuarios como "recordados" para evitar duplicados

### 📊 Criterios de Elegibilidad

- ✅ Cuenta de Roblox vinculada al Discord
- ✅ Cuenta creada hace 15+ días
- ✅ Usuario no ha recibido recordatorio previamente
- ✅ Mensajes directos habilitados

## 🎯 Características

### 🤖 Automatización Completa
- **Inicio Automático**: Se inicia cuando el bot se conecta
- **Ejecución Continua**: Funciona 24/7 sin intervención manual
- **Recuperación de Errores**: Se reinicia automáticamente en caso de fallos

### 📱 Notificaciones Inteligentes
- **Mensajes Personalizados**: Incluye información específica del usuario
- **Diseño Atractivo**: Embeds con colores y formato profesional
- **Información Completa**: Muestra días transcurridos y estado de elegibilidad

### 🛡️ Prevención de Spam
- **Una Sola Notificación**: Cada usuario recibe máximo un recordatorio
- **Base de Datos Persistente**: Registra usuarios notificados permanentemente
- **Validación de Fechas**: Verifica precisión en cálculos de tiempo

## 🎮 Comandos de Administración

### `/reminder_stats`
**Descripción**: Muestra estadísticas completas del sistema
**Permisos**: Solo propietarios
**Información mostrada**:
- Estado del sistema (activo/inactivo)
- Total de cuentas vinculadas
- Usuarios ya recordados
- Usuarios elegibles pendientes

### `/reminder_control`
**Descripción**: Controla el estado del sistema
**Permisos**: Solo propietarios
**Opciones disponibles**:
- `Iniciar`: Activa el sistema de recordatorios
- `Detener`: Pausa el sistema temporalmente
- `Reiniciar`: Reinicia completamente el sistema

### `/send_manual_reminder`
**Descripción**: Envía recordatorio manual a usuario específico
**Permisos**: Solo propietarios
**Parámetros**:
- `user`: Usuario de Discord al que enviar el recordatorio
**Validaciones**:
- Verifica que el usuario tenga cuenta vinculada
- Confirma elegibilidad (15+ días)
- Marca como recordado tras envío exitoso

## 📁 Estructura de Archivos

### `reminder_system.py`
**Clase Principal**: `RobuxReminderSystem`
**Funciones Clave**:
- `start_reminder_system()`: Inicia el sistema
- `stop_reminder_system()`: Detiene el sistema
- `_reminder_loop()`: Loop principal de verificación
- `_check_and_send_reminders()`: Lógica de verificación y envío
- `send_manual_reminder()`: Recordatorios manuales
- `get_reminder_stats()`: Estadísticas del sistema

### Integración en `main.py`
```python
# Importación del sistema
from reminder_system import initialize_reminder_system

# Inicialización automática en on_ready
reminder_system = initialize_reminder_system(client)
await reminder_system.start_reminder_system()
```

### Comandos en `owner_commands.py`
- Comandos de administración integrados
- Validaciones de permisos
- Manejo de errores robusto

## 💾 Almacenamiento de Datos

### Estructura en `data.json`
```json
{
  "roblox_accounts": {
    "discord_user_id": {
      "id": "roblox_user_id",
      "display_name": "username",
      "created": "2024-01-01T00:00:00Z",
      "avatar_url": "https://..."
    }
  },
  "reminded_users": [
    "discord_user_id_1",
    "discord_user_id_2"
  ]
}
```

### Funciones de Data Manager
- `get_all_roblox_accounts()`: Obtiene todas las cuentas vinculadas
- `load_data()` / `save_data()`: Gestión de persistencia
- Campo `reminded_users`: Lista de usuarios ya notificados

## 🔧 Configuración y Mantenimiento

### Configuración Inicial
1. El sistema se inicializa automáticamente al arrancar el bot
2. No requiere configuración adicional
3. Utiliza la base de datos existente del bot

### Monitoreo
- **Logs Detallados**: Registra todas las operaciones importantes
- **Estadísticas en Tiempo Real**: Comando `/reminder_stats`
- **Control Manual**: Comandos de administración disponibles

### Mantenimiento
- **Limpieza Automática**: Elimina verificaciones expiradas
- **Recuperación de Errores**: Reintentos automáticos
- **Backup de Datos**: Integrado con el sistema de datos del bot

## 🚀 Beneficios del Sistema

### Para los Usuarios
- ✅ **Notificación Oportuna**: Saben exactamente cuándo son elegibles
- ✅ **Información Clara**: Detalles completos sobre su estado
- ✅ **Sin Spam**: Una sola notificación por usuario
- ✅ **Acceso Inmediato**: Pueden usar `/micuenta` para verificar

### Para los Administradores
- ✅ **Automatización Total**: Sin intervención manual requerida
- ✅ **Control Completo**: Comandos de gestión disponibles
- ✅ **Estadísticas Detalladas**: Monitoreo en tiempo real
- ✅ **Escalabilidad**: Maneja cualquier cantidad de usuarios

### Para el Servidor
- ✅ **Engagement Mejorado**: Usuarios más activos y comprometidos
- ✅ **Experiencia Premium**: Funcionalidad profesional y pulida
- ✅ **Retención de Usuarios**: Recordatorios mantienen interés
- ✅ **Diferenciación**: Característica única vs otros bots

## 🔍 Solución de Problemas

### Problemas Comunes

**Sistema no envía recordatorios**
- Verificar estado con `/reminder_stats`
- Reiniciar con `/reminder_control restart`
- Revisar logs del bot

**Usuario no recibe mensaje**
- Verificar que tenga DMs habilitados
- Confirmar cuenta vinculada con `/micuenta`
- Usar `/send_manual_reminder` para prueba

**Estadísticas incorrectas**
- Verificar integridad de `data.json`
- Reiniciar sistema completamente
- Revisar logs de errores

### Logs Importantes
```
[INFO] Sistema de recordatorios iniciado
[INFO] Recordatorios enviados a X usuarios
[WARNING] No se pudo enviar DM al usuario X (DMs cerrados)
[ERROR] Error en el loop de recordatorios: ...
```

## 📈 Métricas y Análisis

El sistema proporciona métricas detalladas para análisis:

- **Tasa de Entrega**: Porcentaje de recordatorios enviados exitosamente
- **Usuarios Activos**: Cantidad de cuentas vinculadas activas
- **Crecimiento**: Nuevos usuarios elegibles por período
- **Engagement**: Respuesta a recordatorios enviados

---

**Desarrollado para GameMid Bot** 🎮
*Sistema de Recordatorios Automáticos v1.0*