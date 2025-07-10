# 🛒 Tienda Virtual GameCoins

## Descripción
La Tienda Virtual es un sistema completo que permite a los usuarios comprar productos virtuales usando GameCoins (la moneda del servidor). Los owners pueden gestionar productos y los usuarios pueden navegar, comprar y gestionar su inventario.

## 🎯 Características Principales

### Para Usuarios
- **Navegación por categorías**: Explora productos organizados por tipo
- **Compra con GameCoins**: Usa la moneda del servidor para comprar
- **Inventario personal**: Ve todos tus productos comprados
- **Productos temporales**: Algunos productos tienen duración limitada
- **Confirmación de compra**: Sistema seguro de confirmación

### Para Owners
- **Gestión completa**: Añadir, editar y eliminar productos
- **Categorización**: Organizar productos en categorías específicas
- **Estadísticas**: Ver métricas de ventas y productos
- **Productos flexibles**: Roles, beneficios, cosméticos y potenciadores

## 📂 Categorías de Productos

### 🎭 Roles Especiales
- Roles únicos para destacar en el servidor
- Pueden ser permanentes o temporales
- Acceso a canales y funciones exclusivas

### ⭐ Beneficios
- Ventajas especiales en el servidor
- Multiplicadores de XP y GameCoins
- Acceso a funciones premium

### ✨ Cosméticos
- Items decorativos y personalizaciones
- Colores de nombre personalizados
- Insignias y efectos especiales

### 🚀 Potenciadores
- Multiplicadores y bonificaciones temporales
- Boost de ganancias por tiempo limitado
- Mejoras en probabilidades de juegos

## 🎮 Comandos para Usuarios

### `/tienda`
Abre la tienda virtual principal donde puedes:
- Ver todas las categorías disponibles
- Navegar por productos
- Realizar compras
- Acceder a tu inventario

**Uso:**
```
/tienda
```

## 👑 Comandos para Owners

### `/añadir_producto_virtual`
Añade un nuevo producto a la tienda virtual.

**Parámetros:**
- `nombre`: Nombre del producto
- `precio`: Precio en GameCoins
- `descripcion`: Descripción del producto
- `categoria`: Categoría (roles, perks, cosmetics, boosters)
- `rol_id`: ID del rol (opcional, para productos de rol)
- `duracion_dias`: Duración en días (opcional, para productos temporales)
- `multiplicador`: Multiplicador (opcional, para boosters)

**Ejemplo:**
```
/añadir_producto_virtual nombre:"VIP Dorado" precio:5000 descripcion:"Rol VIP exclusivo" categoria:roles rol_id:123456789
```

### `/editar_producto_virtual`
Edita un producto existente.

**Parámetros:**
- `product_id`: ID del producto a editar
- `nombre`: Nuevo nombre (opcional)
- `precio`: Nuevo precio (opcional)
- `descripcion`: Nueva descripción (opcional)
- `habilitado`: Habilitar/deshabilitar (opcional)

### `/eliminar_producto_virtual`
Elimina un producto de la tienda.

**Parámetros:**
- `product_id`: ID del producto a eliminar

### `/listar_productos_virtuales`
Muestra todos los productos con estadísticas.

## 🔧 Configuración Inicial

### 1. Ejecutar el Script de Configuración
```bash
python setup_virtual_shop.py
```

Este script añade productos de ejemplo en todas las categorías.

### 2. Configurar Roles (Opcional)
Para productos de roles, necesitas:
1. Crear los roles en Discord
2. Obtener sus IDs
3. Editar los productos para añadir los `rol_id` correctos

### 3. Personalizar Productos
Puedes editar o eliminar los productos de ejemplo y crear los tuyos propios.

## 💡 Ejemplos de Productos

### Rol VIP
```
Nombre: 🌟 VIP Dorado
Precio: 5000 GameCoins
Categoría: roles
Descripción: Rol VIP exclusivo con beneficios especiales
Rol ID: [ID del rol en Discord]
```

### Boost Temporal
```
Nombre: 🚀 Boost de XP (7 días)
Precio: 1500 GameCoins
Categoría: perks
Descripción: Duplica la ganancia de XP por 7 días
Duración: 7 días
Multiplicador: 2.0
```

### Cosmético
```
Nombre: 🎨 Color de Nombre Personalizado
Precio: 2500 GameCoins
Categoría: cosmetics
Descripción: Cambia el color de tu nombre (permanente)
```

## 🛡️ Sistema de Seguridad

### Verificaciones de Compra
- **Balance suficiente**: Verifica que el usuario tenga GameCoins
- **Producto disponible**: Solo productos habilitados son comprables
- **Duplicados**: Previene comprar roles que ya se poseen
- **Confirmación**: Requiere escribir "COMPRAR" para confirmar

### Gestión de Permisos
- Solo owners pueden gestionar productos
- Usuarios solo pueden comprar y ver su inventario
- Verificación de roles automática

## 📊 Estadísticas y Métricas

La tienda virtual rastrea:
- **Total de productos**: Cantidad de productos creados
- **Productos activos**: Productos disponibles para compra
- **Compras realizadas**: Número total de transacciones
- **Ingresos totales**: GameCoins generados por ventas
- **Compras por producto**: Popularidad de cada item

## 🔄 Gestión de Inventario

### Productos Permanentes
- Se mantienen en el inventario indefinidamente
- Ideales para roles y cosméticos

### Productos Temporales
- Expiran automáticamente después del tiempo especificado
- Perfectos para boosts y beneficios temporales
- El sistema verifica automáticamente las expiraciones

## 🎨 Interfaz de Usuario

### Navegación
- **Botones de categoría**: Filtra productos por tipo
- **Paginación**: Navega entre páginas de productos
- **Selección de productos**: Dropdown para elegir qué comprar
- **Inventario**: Botón para ver productos comprados

### Embeds Informativos
- **Balance actual**: Muestra GameCoins disponibles
- **Información del producto**: Precio, descripción, beneficios
- **Confirmación de compra**: Detalles de la transacción
- **Estado del inventario**: Productos activos y expirados

## 🚀 Integración con Economía

La tienda virtual está completamente integrada con el sistema de economía:
- **Transacciones automáticas**: Descuenta GameCoins automáticamente
- **Historial de gastos**: Rastrea el total gastado por usuario
- **Estadísticas de usuario**: Actualiza métricas económicas
- **Validación de balance**: Verifica fondos antes de comprar

## 🔧 Mantenimiento

### Limpieza Automática
- Los productos expirados se marcan automáticamente
- El sistema verifica expiraciones al acceder al inventario
- No se requiere mantenimiento manual

### Respaldos
- Todos los datos se guardan en `data.json`
- Las compras se registran con timestamps
- Historial completo de transacciones

## 📝 Notas Importantes

1. **IDs de Roles**: Para productos de roles, asegúrate de usar IDs válidos de Discord
2. **Precios Balanceados**: Considera la economía del servidor al fijar precios
3. **Productos Temporales**: Comunica claramente la duración a los usuarios
4. **Categorización**: Mantén los productos organizados en las categorías correctas
5. **Descripciones Claras**: Explica exactamente qué incluye cada producto

## 🆘 Solución de Problemas

### Error: "Producto no encontrado"
- Verifica que el ID del producto sea correcto
- Asegúrate de que el producto no haya sido eliminado

### Error: "GameCoins insuficientes"
- El usuario necesita más GameCoins
- Puede ganar más jugando minijuegos o completando tareas

### Error: "Ya posees este producto"
- Para roles permanentes, no se puede comprar duplicados
- Verifica en el inventario si ya lo tienes

### Productos no aparecen
- Verifica que estén habilitados (`enabled: true`)
- Revisa la categoría correcta
- Asegúrate de que el bot tenga permisos

---

¡La Tienda Virtual GameCoins está lista para mejorar la experiencia de tu servidor Discord! 🎉