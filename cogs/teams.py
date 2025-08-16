import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio
from database import Database
from utils import EmbedBuilder, ButtonBuilder, GameLogic
from config import COLORS, EMOJIS, MATCH_SETTINGS

class TeamsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    @app_commands.command(name="criartime", description="Cria um novo time de basquete")
    @app_commands.describe(
        nome="Nome do seu time",
        logo="URL do logo do time (opcional)"
    )
    async def create_team(self, interaction: discord.Interaction, nome: str, logo: Optional[str] = None):
        """Cria um novo time para o usuário"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        username = interaction.user.display_name
        
        # Verifica se usuário existe
        user = await self.db.get_user(user_id)
        if not user:
            await self.db.create_user(user_id, username)
        
        # Verifica se já tem time
        existing_team = await self.db.get_team(user_id)
        if existing_team:
            embed = EmbedBuilder.create_embed(
                "❌ Erro",
                "Você já possui um time!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Cria o time
        success = await self.db.create_team(user_id, nome, logo)
        if success:
            embed = EmbedBuilder.create_embed(
                f"✅ Time Criado!",
                f"Seu time **{nome}** foi criado com sucesso!\n\n"
                f"Use `/time` para ver informações do seu time\n"
                f"Use `/loja` para comprar jogadores\n"
                f"Use `/pack` para abrir um pack gratuito",
                COLORS['success']
            )
            if logo:
                embed.set_thumbnail(url=logo)
        else:
            embed = EmbedBuilder.create_embed(
                "❌ Erro",
                "Erro ao criar o time. Tente novamente.",
                COLORS['error']
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="time", description="Mostra informações do seu time")
    async def team_info(self, interaction: discord.Interaction):
        """Mostra informações do time do usuário"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você ainda não criou um time!\nUse `/criartime` para criar seu time.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obtém jogadores
        players = await self.db.get_user_players(user_id)
        user = await self.db.get_user(user_id)
        
        embed = EmbedBuilder.team_overview(team, players, user['money'])
        
        # Adiciona botões
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Ver Jogadores",
            emoji=EMOJIS['team'],
            custom_id="view_players"
        ))
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Gerenciar Time",
            emoji="⚙️",
            custom_id="manage_team"
        ))
        
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(name="jogadores", description="Mostra todos os seus jogadores")
    async def show_players(self, interaction: discord.Interaction):
        """Mostra todos os jogadores do usuário"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você ainda não criou um time!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obtém jogadores
        players = await self.db.get_user_players(user_id)
        
        if not players:
            embed = EmbedBuilder.create_embed(
                "📭 Sem Jogadores",
                "Você ainda não tem jogadores!\nUse `/loja` para comprar jogadores ou `/pack` para abrir um pack.",
                COLORS['warning']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Separa titulares e reservas
        starters = [p for p in players if p['is_starter']]
        bench = [p for p in players if not p['is_starter']]
        
        embed = EmbedBuilder.create_embed(
            f"👥 Jogadores - {team['team_name']}",
            f"**Titulares:** {len(starters)}/5 | **Reservas:** {len(bench)}",
            COLORS['primary']
        )
        
        # Lista titulares
        if starters:
            starters_text = ""
            for i, player in enumerate(starters[:5], 1):
                rarity_emoji = {'comum': '⚪', 'raro': '🔵', 'épico': '🟣', 'lendário': '🟡'}
                starters_text += f"{i}. {player['name']} ({player['overall']}) {rarity_emoji.get(player['rarity'], '⚪')}\n"
            
            embed.add_field(
                name="⭐ Titulares",
                value=starters_text,
                inline=False
            )
        
        # Lista reservas
        if bench:
            bench_text = ""
            for i, player in enumerate(bench[:10], 1):  # Máximo 10 reservas
                rarity_emoji = {'comum': '⚪', 'raro': '🔵', 'épico': '🟣', 'lendário': '🟡'}
                bench_text += f"{i}. {player['name']} ({player['overall']}) {rarity_emoji.get(player['rarity'], '⚪')}\n"
            
            embed.add_field(
                name="🪑 Reservas",
                value=bench_text,
                inline=False
            )
        
        # Adiciona estatísticas
        if players:
            avg_overall = sum(p['overall'] for p in players) / len(players)
            highest_rarity = max(players, key=lambda x: {'comum': 1, 'raro': 2, 'épico': 3, 'lendário': 4}[x['rarity']])
            
            embed.add_field(
                name="📊 Estatísticas",
                value=f"**Overall Médio:** {avg_overall:.1f}\n"
                      f"**Melhor Jogador:** {highest_rarity['name']} ({highest_rarity['overall']})\n"
                      f"**Total de Jogadores:** {len(players)}",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="titular", description="Define um jogador como titular")
    @app_commands.describe(jogador="Nome do jogador para definir como titular")
    async def set_starter(self, interaction: discord.Interaction, jogador: str):
        """Define um jogador como titular"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você ainda não criou um time!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Busca o jogador
        players = await self.db.get_user_players(user_id)
        target_player = None
        
        for player in players:
            if jogador.lower() in player['name'].lower():
                target_player = player
                break
        
        if not target_player:
            embed = EmbedBuilder.create_embed(
                "❌ Jogador Não Encontrado",
                f"Jogador '{jogador}' não encontrado no seu time.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Verifica se já é titular
        if target_player['is_starter']:
            embed = EmbedBuilder.create_embed(
                "ℹ️ Já é Titular",
                f"{target_player['name']} já é titular do seu time.",
                COLORS['info']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Verifica se já tem 5 titulares
        starters = [p for p in players if p['is_starter']]
        if len(starters) >= 5:
            embed = EmbedBuilder.create_embed(
                "❌ Time Completo",
                "Você já tem 5 titulares. Remova um titular primeiro.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Define como titular (implementar no database)
        # Por enquanto, apenas confirma
        embed = EmbedBuilder.create_embed(
            "✅ Titular Definido",
            f"{target_player['name']} agora é titular do seu time!",
            COLORS['success']
        )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="reserva", description="Define um jogador como reserva")
    @app_commands.describe(jogador="Nome do jogador para definir como reserva")
    async def set_bench(self, interaction: discord.Interaction, jogador: str):
        """Define um jogador como reserva"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você ainda não criou um time!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Busca o jogador
        players = await self.db.get_user_players(user_id)
        target_player = None
        
        for player in players:
            if jogador.lower() in player['name'].lower():
                target_player = player
                break
        
        if not target_player:
            embed = EmbedBuilder.create_embed(
                "❌ Jogador Não Encontrado",
                f"Jogador '{jogador}' não encontrado no seu time.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Verifica se já é reserva
        if not target_player['is_starter']:
            embed = EmbedBuilder.create_embed(
                "ℹ️ Já é Reserva",
                f"{target_player['name']} já é reserva do seu time.",
                COLORS['info']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Define como reserva (implementar no database)
        # Por enquanto, apenas confirma
        embed = EmbedBuilder.create_embed(
            "✅ Reserva Definido",
            f"{target_player['name']} agora é reserva do seu time!",
            COLORS['success']
        )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="vender", description="Vende um jogador")
    @app_commands.describe(jogador="Nome do jogador para vender")
    async def sell_player(self, interaction: discord.Interaction, jogador: str):
        """Vende um jogador"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se tem time
        team = await self.db.get_team(user_id)
        if not team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você ainda não criou um time!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Busca o jogador
        players = await self.db.get_user_players(user_id)
        target_player = None
        
        for player in players:
            if jogador.lower() in player['name'].lower():
                target_player = player
                break
        
        if not target_player:
            embed = EmbedBuilder.create_embed(
                "❌ Jogador Não Encontrado",
                f"Jogador '{jogador}' não encontrado no seu time.",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Calcula valor de venda (80% do valor de mercado)
        sell_value = int(target_player['market_value'] * 0.8)
        
        # Confirma venda
        embed = EmbedBuilder.create_embed(
            "💰 Confirmar Venda",
            f"Você está vendendo **{target_player['name']}** por **${sell_value:,}**\n\n"
            f"Overall: {target_player['overall']} | Time: {target_player['team']}\n"
            f"Raridade: {target_player['rarity']} | Posição: {target_player['position']}",
            COLORS['warning']
        )
        
        # Adiciona botões de confirmação
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.green,
            label="Confirmar Venda",
            emoji=EMOJIS['money'],
            custom_id=f"sell_confirm_{target_player['id']}"
        ))
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.red,
            label="Cancelar",
            emoji=EMOJIS['cross'],
            custom_id="sell_cancel"
        ))
        
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(TeamsCog(bot))
