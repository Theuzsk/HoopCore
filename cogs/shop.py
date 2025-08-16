import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio
from datetime import datetime, timedelta
from database import Database
from utils import EmbedBuilder, ButtonBuilder, GameLogic
from config import COLORS, EMOJIS, ECONOMY, TIMERS

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    @app_commands.command(name="loja", description="Mostra a loja de jogadores")
    async def show_shop(self, interaction: discord.Interaction):
        """Mostra a loja de jogadores"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você precisa criar um time primeiro!\nUse `/criartime` para criar seu time.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obtém itens da loja
        shop_items = await self.db.get_shop_items()
        
        if not shop_items:
            embed = EmbedBuilder.create_embed(
                "🛒 Loja Vazia",
                "A loja está vazia no momento.\nTente novamente em alguns minutos!",
                COLORS['warning']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obtém dinheiro do usuário
        user = await self.db.get_user(user_id)
        
        embed = EmbedBuilder.shop_embed(shop_items)
        embed.add_field(
            name="💰 Seu Dinheiro",
            value=f"**${user['money']:,}**",
            inline=False
        )
        
        # Adiciona botões
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Atualizar Loja",
            emoji=EMOJIS['reload'],
            custom_id="refresh_shop"
        ))
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Comprar Pack",
            emoji=EMOJIS['shop'],
            custom_id="buy_pack"
        ))
        
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(name="comprar", description="Compra um jogador da loja")
    @app_commands.describe(numero="Número do jogador na loja")
    async def buy_player(self, interaction: discord.Interaction, numero: int):
        """Compra um jogador da loja"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você precisa criar um time primeiro!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obtém itens da loja
        shop_items = await self.db.get_shop_items()
        
        if not shop_items:
            embed = EmbedBuilder.create_embed(
                "❌ Loja Vazia",
                "A loja está vazia no momento.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Verifica se o número é válido
        if numero < 1 or numero > len(shop_items):
            embed = EmbedBuilder.create_embed(
                "❌ Número Inválido",
                f"Digite um número entre 1 e {len(shop_items)}.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obtém o item selecionado
        selected_item = shop_items[numero - 1]
        
        # Obtém dinheiro do usuário
        user = await self.db.get_user(user_id)
        
        # Verifica se tem dinheiro suficiente
        if user['money'] < selected_item['price']:
            embed = EmbedBuilder.create_embed(
                "❌ Dinheiro Insuficiente",
                f"Você precisa de **${selected_item['price']:,}** mas tem apenas **${user['money']:,}**.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Tenta comprar o jogador
        success = await self.db.buy_player(user_id, selected_item['id'])
        
        if success:
            embed = EmbedBuilder.create_embed(
                "✅ Compra Realizada!",
                f"Você comprou **{selected_item['name']}** por **${selected_item['price']:,}**!\n\n"
                f"Overall: {selected_item['overall']} | Time: {selected_item['team']}\n"
                f"Raridade: {selected_item['rarity']} | Posição: {selected_item['position']}",
                COLORS['success']
            )
            
            # Atualiza dinheiro restante
            remaining_money = user['money'] - selected_item['price']
            embed.add_field(
                name="💰 Dinheiro Restante",
                value=f"**${remaining_money:,}**",
                inline=False
            )
        else:
            embed = EmbedBuilder.create_embed(
                "❌ Erro na Compra",
                "Erro ao realizar a compra. Tente novamente.",
                COLORS['error']
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="pack", description="Abre um pack gratuito de jogadores")
    async def open_free_pack(self, interaction: discord.Interaction):
        """Abre um pack gratuito"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você precisa criar um time primeiro!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Verifica se pode abrir pack (cooldown de 25 minutos)
        user = await self.db.get_user(user_id)
        if user['last_free_pack']:
            try:
                # Converte string para datetime
                if 'Z' in user['last_free_pack']:
                    last_pack = datetime.fromisoformat(user['last_free_pack'].replace('Z', '+00:00'))
                else:
                    last_pack = datetime.fromisoformat(user['last_free_pack'])
                
                time_diff = datetime.now() - last_pack.replace(tzinfo=None)
                
                if time_diff.total_seconds() < TIMERS['free_pack']:
                    remaining_time = TIMERS['free_pack'] - time_diff.total_seconds()
                    minutes = int(remaining_time // 60)
                    seconds = int(remaining_time % 60)
                    
                    embed = EmbedBuilder.create_embed(
                        "⏰ Cooldown",
                        f"Você pode abrir outro pack em **{minutes}m {seconds}s**.",
                        COLORS['warning']
                    )
                    await interaction.followup.send(embed=embed)
                    return
            except Exception as e:
                print(f"Erro ao verificar cooldown: {e}")
                # Se houver erro, continua normalmente
        
        # Obtém jogador aleatório
        player = await self.db.get_random_player()
        
        if not player:
            embed = EmbedBuilder.create_embed(
                "❌ Erro",
                "Erro ao gerar jogador. Tente novamente.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Adiciona jogador ao usuário
        success = await self.db.add_player_to_user(user_id, player['player_id'])
        
        if success:
            # Atualiza timestamp do último pack
            await self.db.update_last_free_pack(user_id)
            
            # Cria embed do jogador obtido
            embed = EmbedBuilder.player_card(player)
            embed.title = "🎁 Pack Aberto!"
            embed.description = f"🎉 Parabéns! Você obteve:\n\n{embed.description}"
            
            # Adiciona informações extras
            embed.add_field(
                name="📦 Tipo de Pack",
                value="Pack Gratuito",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Próximo Pack",
                value="Em 25 minutos",
                inline=True
            )
            
            # Adiciona emoji de raridade
            rarity_emoji = {
                'comum': '⚪',
                'raro': '🔵',
                'épico': '🟣',
                'lendário': '🟡'
            }
            
            embed.add_field(
                name="⭐ Raridade",
                value=f"{rarity_emoji.get(player['rarity'], '⚪')} {player['rarity'].title()}",
                inline=True
            )
            
        else:
            embed = EmbedBuilder.create_embed(
                "❌ Erro",
                "Erro ao adicionar jogador. Tente novamente.",
                COLORS['error']
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="packpremium", description="Compra e abre um pack premium")
    async def buy_premium_pack(self, interaction: discord.Interaction):
        """Compra um pack premium"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você precisa criar um time primeiro!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obtém dinheiro do usuário
        user = await self.db.get_user(user_id)
        
        # Verifica se tem dinheiro suficiente
        if user['money'] < ECONOMY['pack_cost']:
            embed = EmbedBuilder.create_embed(
                "❌ Dinheiro Insuficiente",
                f"Pack Premium custa **${ECONOMY['pack_cost']:,}** mas você tem apenas **${user['money']:,}**.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Remove dinheiro
        await self.db.update_money(user_id, -ECONOMY['pack_cost'])
        
        # Gera 3 jogadores (melhor chance de raridade)
        players = []
        for _ in range(3):
            player = await self.db.get_random_player()
            if player:
                success = await self.db.add_player_to_user(user_id, player['player_id'])
                if success:
                    players.append(player)
        
        if players:
            embed = EmbedBuilder.create_embed(
                "🎁 Pack Premium Aberto!",
                f"Você obteve **{len(players)} jogadores** por **${ECONOMY['pack_cost']:,}**!",
                COLORS['purple']
            )
            
            # Mostra os jogadores obtidos
            for i, player in enumerate(players, 1):
                rarity_emoji = {'comum': '⚪', 'raro': '🔵', 'épico': '🟣', 'lendário': '🟡'}
                embed.add_field(
                    name=f"{i}. {player['name']} {rarity_emoji.get(player['rarity'], '⚪')}",
                    value=f"Overall: **{player['overall']}** | Time: {player['team']}\n"
                          f"Raridade: {player['rarity']} | Posição: {player['position']}",
                    inline=False
                )
            
            # Atualiza dinheiro restante
            remaining_money = user['money'] - ECONOMY['pack_cost']
            embed.add_field(
                name="💰 Dinheiro Restante",
                value=f"**${remaining_money:,}**",
                inline=False
            )
        else:
            embed = EmbedBuilder.create_embed(
                "❌ Erro",
                "Erro ao abrir pack. Seu dinheiro foi devolvido.",
                COLORS['error']
            )
            # Devolve o dinheiro
            await self.db.update_money(user_id, ECONOMY['pack_cost'])
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="diario", description="Coleta recompensa diária")
    async def daily_reward(self, interaction: discord.Interaction):
        """Coleta recompensa diária"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você precisa criar um time primeiro!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Verifica se pode coletar (cooldown de 24 horas)
        user = await self.db.get_user(user_id)
        if user['last_daily']:
            try:
                # Converte string para datetime
                if 'Z' in user['last_daily']:
                    last_daily = datetime.fromisoformat(user['last_daily'].replace('Z', '+00:00'))
                else:
                    last_daily = datetime.fromisoformat(user['last_daily'])
                
                time_diff = datetime.now() - last_daily.replace(tzinfo=None)
                
                if time_diff.total_seconds() < TIMERS['daily_reset']:
                    remaining_time = TIMERS['daily_reset'] - time_diff.total_seconds()
                    hours = int(remaining_time // 3600)
                    minutes = int((remaining_time % 3600) // 60)
                    
                    embed = EmbedBuilder.create_embed(
                        "⏰ Cooldown",
                        f"Você pode coletar a recompensa diária em **{hours}h {minutes}m**.",
                        COLORS['warning']
                    )
                    await interaction.followup.send(embed=embed)
                    return
            except Exception as e:
                print(f"Erro ao verificar cooldown diário: {e}")
                # Se houver erro, continua normalmente
        
        # Adiciona dinheiro
        await self.db.update_money(user_id, ECONOMY['daily_reward'])
        
        # Atualiza timestamp da última recompensa diária
        await self.db.update_last_daily(user_id)
        
        embed = EmbedBuilder.create_embed(
            "💰 Recompensa Diária!",
            f"Você recebeu **${ECONOMY['daily_reward']:,}** como recompensa diária!\n\n"
            f"Use o dinheiro para comprar jogadores na loja ou abrir packs premium.",
            COLORS['success']
        )
        
        # Atualiza dinheiro total
        new_money = user['money'] + ECONOMY['daily_reward']
        embed.add_field(
            name="💰 Dinheiro Total",
            value=f"**${new_money:,}**",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="dinheiro", description="Mostra seu dinheiro atual")
    async def show_money(self, interaction: discord.Interaction):
        """Mostra o dinheiro do usuário"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você precisa criar um time primeiro!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obtém dinheiro do usuário
        user = await self.db.get_user(user_id)
        
        embed = EmbedBuilder.create_embed(
            f"{EMOJIS['money']} Seu Dinheiro",
            f"Você possui **${user['money']:,}**",
            COLORS['gold']
        )
        
        # Adiciona informações sobre como ganhar dinheiro
        embed.add_field(
            name="💡 Como Ganhar Dinheiro",
            value="• **Recompensa Diária:** `/diario` (+$1,000)\n"
                  "• **Vitórias em Partidas:** +$500\n"
                  "• **Vender Jogadores:** 80% do valor de mercado",
            inline=False
        )
        
        # Adiciona informações sobre gastos
        embed.add_field(
            name="💸 Como Gastar Dinheiro",
            value="• **Loja:** Comprar jogadores\n"
                  "• **Pack Premium:** $5,000 (3 jogadores)\n"
                  "• **Derrotas em Partidas:** -$200",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ShopCog(bot))
