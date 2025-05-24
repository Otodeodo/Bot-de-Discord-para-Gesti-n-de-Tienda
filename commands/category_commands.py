import discord
from discord import app_commands
from typing import Optional
import logging
from data_manager import (
    add_category,
    update_category,
    delete_category,
    get_all_categories,
    assign_product_to_category,
    load_data
)
from utils import is_owner

# Configuración del logging
logger = logging.getLogger(__name__)

def setup(tree: app_commands.CommandTree, client: discord.Client):
    @tree.command(name="add_category", description="Añade una nueva categoría de productos")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def add_category_command(interaction: discord.Interaction, name: str, description: str, icon: Optional[str] = ""):
        try:
            category_id = add_category(name, description, icon)
            if category_id:
                embed = discord.Embed(
                    title="✅ Categoría Creada",
                    description=f"Se ha creado la categoría '{name}' exitosamente.",
                    color=0xA100F2
                )
                embed.add_field(name="ID", value=category_id, inline=True)
                embed.add_field(name="Nombre", value=name, inline=True)
                embed.add_field(name="Descripción", value=description, inline=False)
                if icon:
                    embed.set_thumbnail(url=icon)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Error al crear la categoría.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error al crear categoría: {str(e)}")
            await interaction.response.send_message("❌ Ha ocurrido un error al crear la categoría.", ephemeral=True)

    @tree.command(name="edit_category", description="Edita una categoría existente")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def edit_category_command(
        interaction: discord.Interaction,
        category_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None
    ):
        try:
            success = update_category(category_id, name, description, icon)
            if success:
                embed = discord.Embed(
                    title="✅ Categoría Actualizada",
                    description=f"Se ha actualizado la categoría {category_id} exitosamente.",
                    color=0xA100F2
                )
                if name:
                    embed.add_field(name="Nuevo Nombre", value=name, inline=True)
                if description:
                    embed.add_field(name="Nueva Descripción", value=description, inline=True)
                if icon:
                    embed.set_thumbnail(url=icon)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ No se encontró la categoría especificada.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error al editar categoría: {str(e)}")
            await interaction.response.send_message("❌ Ha ocurrido un error al editar la categoría.", ephemeral=True)

    @tree.command(name="delete_category", description="Elimina una categoría")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def delete_category_command(interaction: discord.Interaction, category_id: str):
        try:
            success = delete_category(category_id)
            if success:
                await interaction.response.send_message("✅ Categoría eliminada exitosamente.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ No se encontró la categoría especificada.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error al eliminar categoría: {str(e)}")
            await interaction.response.send_message("❌ Ha ocurrido un error al eliminar la categoría.", ephemeral=True)

    @tree.command(name="assign_product_category", description="Asigna un producto a una categoría")
    @app_commands.default_permissions(administrator=True)
    @is_owner()
    async def assign_product_category_command(interaction: discord.Interaction, product_id: str, category_id: str):
        try:
            success = assign_product_to_category(product_id, category_id)
            if success:
                data = load_data()
                product_name = data['products'][product_id]['name']
                category_name = data['categories'][category_id]['name']
                
                embed = discord.Embed(
                    title="✅ Producto Asignado",
                    description=f"Se ha asignado el producto a la categoría exitosamente.",
                    color=0xA100F2
                )
                embed.add_field(name="Producto", value=f"{product_name} (ID: {product_id})", inline=True)
                embed.add_field(name="Categoría", value=f"{category_name} (ID: {category_id})", inline=True)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ No se encontró el producto o la categoría especificada.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error al asignar producto a categoría: {str(e)}")
            await interaction.response.send_message("❌ Ha ocurrido un error al asignar el producto a la categoría.", ephemeral=True)

    @tree.command(name="list_categories", description="Muestra todas las categorías disponibles")
    async def list_categories_command(interaction: discord.Interaction):
        try:
            categories = get_all_categories()
            if not categories:
                await interaction.response.send_message("No hay categorías disponibles.", ephemeral=True)
                return

            embed = discord.Embed(
                title="📑 Categorías Disponibles",
                color=0xA100F2
            )

            for category_id, category in categories.items():
                product_count = len(category['products'])
                value = f"Descripción: {category['description']}\nProductos: {product_count}"
                embed.add_field(
                    name=f"📁 {category['name']} (ID: {category_id})",
                    value=value,
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error al listar categorías: {str(e)}")
            await interaction.response.send_message("❌ Ha ocurrido un error al listar las categorías.", ephemeral=True)