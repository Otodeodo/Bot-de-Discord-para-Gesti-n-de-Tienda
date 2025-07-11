# 🛒 Tienda Virtual de GameCoins

La tienda virtual permite a los usuarios comprar productos digitales usando sus GameCoins ganados en el servidor.

## 📋 Características

### Para Usuarios
- **Navegación por categorías**: Explora productos organizados por tipo
- **Compras seguras**: Sistema de verificación de fondos
- **Historial de compras**: Revisa todas tus compras anteriores
- **Productos temporales**: Algunos productos pueden tener duración limitada
- **Roles automáticos**: Recibe roles al comprar productos específicos

### Para Administradores
- **Gestión completa**: Añadir, editar y eliminar productos
- **Categorización**: Organizar productos en categorías
- **Estadísticas**: Ver métricas de ventas y productos
- **Control de disponibilidad**: Habilitar/deshabilitar productos
- **Precios flexibles**: Establecer cualquier precio en GameCoins

## 🎯 Categorías Disponibles

- 🎭 **Roles**: Roles especiales del servidor
- ⭐ **Beneficios**: Ventajas y privilegios
- 🎁 **Items**: Objetos virtuales
- ✨ **Cosméticos**: Elementos decorativos
- 📦 **Otros**: Productos diversos

## 👥 Comandos para Usuarios

### `/tienda_virtual`
Abre la tienda virtual interactiva donde puedes:
- Navegar por categorías
- Ver productos disponibles
- Realizar compras
- Ver precios y descripciones

### `/mis_compras`
Muestra tu historial de compras con:
- Lista de productos comprados
- Fechas de compra
- Precios pagados
- Estado de los productos

## 👑 Comandos para Administradores

### `/añadir_producto_virtual`
Añade un nuevo producto a la tienda:
- **nombre**: Nombre del producto
- **precio**: Precio en GameCoins
- **descripcion**: Descripción del producto
- **categoria**: Categoría del producto
- **imagen_url**: URL de imagen (opcional)
- **rol_id**: ID del rol a otorgar (opcional)
- **duracion_dias**: Duración en días (opcional)

### `/editar_producto_virtual`
Edita un producto existente:
- **product_id**: ID del producto a editar
- **nombre**: Nuevo nombre (opcional)
- **precio**: Nuevo precio (opcional)
- **descripcion**: Nueva descripción (opcional)
- **habilitado**: Habilitar/deshabilitar (opcional)

### `/eliminar_producto_virtual`
Elimina un producto de la tienda:
- **product_id**: ID del producto a eliminar

### `/listar_productos_virtuales`
Muestra todos los productos con detalles:
- Estado (habilitado/deshabilitado)
- Precios y categorías
- Número de compras
- IDs de productos

### `/gestionar_tienda_virtual`
Panel de gestión con estadísticas:
- Total de productos y ventas
- Ingresos generados
- Productos por categoría
- Comandos disponibles

## 💡 Consejos de Uso

### Para Usuarios
1. **Gana GameCoins** primero usando `/daily`, `/work`, y minijuegos
2. **Explora categorías** para encontrar productos de tu interés
3. **Revisa descripciones** antes de comprar
4. **Verifica tu saldo** en la tienda antes de comprar

### Para Administradores
1. **Organiza productos** en categorías apropiadas
2. **Establece precios justos** basados en la economía del servidor
3. **Usa descripciones claras** para explicar qué incluye cada producto
4. **Monitorea estadísticas** regularmente
5. **Actualiza productos** según las necesidades del servidor

## 🔧 Funcionalidades Técnicas

### Sistema de Compras
- Verificación automática de fondos
- Descuento automático de GameCoins
- Registro de todas las transacciones
- Otorgamiento automático de roles

### Gestión de Productos
- IDs únicos para cada producto
- Control de disponibilidad
- Contador de compras
- Soporte para productos temporales

### Seguridad
- Solo owners pueden gestionar productos
- Validación de datos en todas las operaciones
- Manejo de errores robusto
- Logs de todas las transacciones

## 📊 Estadísticas Disponibles

- **Total de productos**: Activos y deshabilitados
- **Total de compras**: Número de transacciones
- **Ingresos totales**: GameCoins generados
- **Productos por categoría**: Distribución
- **Historial individual**: Por usuario

## 🚀 Ejemplos de Uso

### Añadir un Rol VIP
```
/añadir_producto_virtual
nombre: VIP Premium
precio: 5000
descripcion: Acceso VIP con beneficios exclusivos
categoria: roles
rol_id: 123456789012345678
```

### Añadir un Beneficio Temporal
```
/añadir_producto_virtual
nombre: Boost de XP
precio: 1000
descripcion: Doble XP por una semana
categoria: perks
duracion_dias: 7
```

### Editar Precio de Producto
```
/editar_producto_virtual
product_id: abc123
precio: 3000
```

## 🎮 Integración con Economía

La tienda virtual está completamente integrada con el sistema de GameCoins:
- Los GameCoins se descuentan automáticamente
- Las compras se registran en el historial
- Compatible con todos los métodos de ganar GameCoins
- Estadísticas incluidas en el sistema económico

---

*La tienda virtual es una extensión del sistema de economía de GameCoins, diseñada para crear una experiencia de compra inmersiva y segura para todos los usuarios del servidor.*