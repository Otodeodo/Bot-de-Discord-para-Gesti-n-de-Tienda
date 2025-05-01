# Bot de Discord para Gestión de Tienda

Este bot de Discord está diseñado para gestionar una tienda virtual con sistema de tickets y productos.

## Características

- Sistema de productos con gestión completa (añadir, editar, eliminar)
- Sistema de tickets para compras
- Panel de tickets interactivo
- Gestión de métodos de pago
- Comandos específicos para owners y usuarios
- Integración con tienda de Fortnite

## Comandos Principales

### Usuarios
- `/products` - Muestra los productos disponibles
- `/ticket` - Abre un ticket para comprar un producto
- `/ver-tienda` - Muestra los regalos disponibles de la tienda de Fortnite
- `/pago` - Muestra la información de pago

### Owners
- `/add-product` - Añade un nuevo producto
- `/edit-product` - Edita un producto existente
- `/delete-product` - Elimina un producto
- `/close` - Cierra un ticket
- `/ticket-panel` - Crea un panel para tickets

## Configuración

1. Crea un archivo `config.py` con las siguientes variables:
   - `DISCORD_TOKEN`
   - `OWNER_ROLE_ID`
   - `TICKET_CHANNEL_ID`

2. Instala las dependencias:
```bash
pip install discord.py
```

3. Ejecuta el bot:
```bash
python main.py
```