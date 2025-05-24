import discord
from typing import List, Dict, Tuple

class EnhancedProductView(discord.ui.View):
    def __init__(self, products: List[Tuple[str, Dict]], pages: List[List], current_page: int = 0):
        super().__init__(timeout=180)  # 3 minutos de timeout
        self.products = products
        self.pages = pages
        self.current_page = current_page
        self.selected_product = None
        self.selected_category = None
        self.categories = self._get_categories()
        self.update_buttons()
        self._setup_category_select()

    def _get_categories(self) -> List[str]:
        # Obtener todas las categorías del sistema
        from data_manager import get_all_categories
        categories_data = get_all_categories()
        categories = ['Sin categoría']  # Asegurar que siempre exista la categoría por defecto
        
        # Añadir todas las categorías existentes
        for category_id, category in categories_data.items():
            categories.append(category['name'])
        
        return sorted(categories)

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🛍️ Catálogo de Productos",
            description="Explora nuestros productos por categoría\n\n**Comprar:** Usa '🛒 Seleccionar' para elegir un producto",
            color=0xA100F2
        )

        if not self.products:
            embed.description = "❌ No hay productos disponibles en este momento."
            return embed

        current_page_products = self.pages[self.current_page]
        
        # Obtener el mapeo de categorías
        from data_manager import get_all_categories
        categories_data = get_all_categories()
        category_name_map = {cat_id: cat_info['name'] for cat_id, cat_info in categories_data.items()}

        # Filtrar productos por categoría seleccionada
        filtered_products = []
        for pid, prod in current_page_products:
            category_id = prod.get('category_id')
            category_name = category_name_map.get(category_id, 'Sin categoría') if category_id else 'Sin categoría'
            
            if self.selected_category and self.selected_category != "all":
                if category_name == self.selected_category:
                    filtered_products.append((pid, prod, category_name))
            else:
                filtered_products.append((pid, prod, category_name))

        if not filtered_products:
            embed.description += "\n\n❌ No hay productos en esta categoría."
            return embed

        # Agrupar productos por categoría
        products_by_category = {}
        for product_id, product, category_name in filtered_products:
            if category_name not in products_by_category:
                products_by_category[category_name] = []
            products_by_category[category_name].append((product_id, product))

        # Mostrar productos agrupados por categoría
        for category, products in products_by_category.items():
            embed.add_field(
                name=f"📁 {category}",
                value="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
                inline=False
            )

            for product_id, product in products:
                price = product.get('price', 0)
                name = product.get('name', 'Producto sin nombre')
                description = product.get('description', 'Sin descripción')

                embed.add_field(
                    name=name,
                    value=f"💰 ${price:.2f} MXN\n"
                          f"📝 {description[:100]}{'...' if len(description) > 100 else ''}",
                    inline=True
                )

        embed.set_footer(text=f"Página {self.current_page + 1}/{len(self.pages)} • "
                             f"Categoría: {self.selected_category or 'Todas'}")
        return embed

    def update_buttons(self):
        # Actualizar estado de los botones de navegación
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.gray, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.gray, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    def _setup_category_select(self):
        select = discord.ui.Select(
            placeholder="Selecciona una categoría",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label="Todas", value="all")] +
                    [discord.SelectOption(label=cat, value=cat) for cat in self.categories],
            row=1
        )
        select.callback = self.select_category_callback
        self.add_item(select)

    async def select_category_callback(self, interaction: discord.Interaction):
        selected = interaction.data['values'][0]
        self.selected_category = None if selected == "all" else selected
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="🛒 Seleccionar", style=discord.ButtonStyle.success, row=2)
    async def select_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Obtener productos de la página actual
        current_page_products = self.pages[self.current_page]
        if self.selected_category and self.selected_category != "all":
            filtered_products = [(pid, prod) for pid, prod in current_page_products 
                               if prod.get('category', 'Sin categoría') == self.selected_category]
        else:
            filtered_products = current_page_products

        # Crear menú de selección
        select = discord.ui.Select(
            placeholder="Selecciona un producto",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=f"{prod['name']} - ${prod['price']:.2f} MXN",
                    value=pid,
                    description=prod.get('description', 'Sin descripción')[:100]
                ) for pid, prod in filtered_products
            ]
        )

        async def select_callback(interaction: discord.Interaction):
            selected_id = interaction.data['values'][0]
            selected_product = next((prod for pid, prod in filtered_products if pid == selected_id), None)
            if selected_product:
                self.selected_product = (selected_id, selected_product)
                # Crear vista de ticket con el producto seleccionado
                from views.enhanced_ticket_view import EnhancedTicketView
                ticket_view = EnhancedTicketView(str(interaction.user.id), selected_id, selected_product['name'])
                await interaction.response.edit_message(
                    embed=ticket_view.create_confirmation_embed(),
                    view=ticket_view
                )

        select.callback = select_callback
        self.clear_items()
        self.add_item(select)
        await interaction.response.edit_message(view=self)