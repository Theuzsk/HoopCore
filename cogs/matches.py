import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio
from datetime import datetime
from database import Database
from utils import EmbedBuilder, ButtonBuilder, GameLogic
from config import COLORS, EMOJIS, ECONOMY, MATCH_SETTINGS

class MatchesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.active_matches = {}  # Armazena partidas ativas
    
    @app_commands.command(name="desafiar", description="Desafia outro jogador para uma partida")
    @app_commands.describe(jogador="Mencione o jogador que você quer desafiar")
    async def challenge_player(self, interaction: discord.Interaction, jogador: discord.Member):
        """Desafia outro jogador para uma partida"""
        await interaction.response.defer()
        
        challenger_id = interaction.user.id
        challenged_id = jogador.id
        
        # Verifica se não está desafiando a si mesmo
        if challenger_id == challenged_id:
            embed = EmbedBuilder.create_embed(
                "❌ Erro",
                "Você não pode desafiar a si mesmo!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Verifica se ambos têm times
        challenger_team = await self.db.get_team(challenger_id)
        challenged_team = await self.db.get_team(challenged_id)
        
        if not challenger_team:
            embed = EmbedBuilder.create_embed(
                "❌ Sem Time",
                "Você precisa criar um time primeiro!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        if not challenged_team:
            embed = EmbedBuilder.create_embed(
                "❌ Jogador Sem Time",
                f"{jogador.display_name} ainda não criou um time!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Verifica se ambos têm jogadores suficientes
        challenger_players = await self.db.get_user_players(challenger_id)
        challenged_players = await self.db.get_user_players(challenged_id)
        
        if len(challenger_players) < 5:
            embed = EmbedBuilder.create_embed(
                "❌ Time Incompleto",
                "Você precisa de pelo menos 5 jogadores para desafiar!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        if len(challenged_players) < 5:
            embed = EmbedBuilder.create_embed(
                "❌ Time Incompleto",
                f"{jogador.display_name} precisa de pelo menos 5 jogadores!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Cria embed de desafio
        embed = EmbedBuilder.match_embed(
            interaction.user.display_name,
            jogador.display_name,
            0  # Match ID será gerado
        )
        
        # Adiciona informações dos times
        embed.add_field(
            name="🏀 Times",
            value=f"**{challenger_team['team_name']}** vs **{challenged_team['team_name']}**",
            inline=False
        )
        
        # Adiciona botões de aceitar/recusar
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.green,
            label="Aceitar Desafio",
            emoji=EMOJIS['check'],
            custom_id=f"accept_challenge_{challenger_id}"
        ))
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.red,
            label="Recusar Desafio",
            emoji=EMOJIS['cross'],
            custom_id=f"decline_challenge_{challenger_id}"
        ))
        
        await interaction.followup.send(
            f"{jogador.mention} você foi desafiado!",
            embed=embed,
            view=view
        )
    
    @app_commands.command(name="partida", description="Inicia uma partida simulada")
    @app_commands.describe(jogador="Mencione o jogador para jogar contra")
    async def start_match(self, interaction: discord.Interaction, jogador: discord.Member):
        """Inicia uma partida simulada"""
        await interaction.response.defer()
        
        player1_id = interaction.user.id
        player2_id = jogador.id
        
        # Verifica se ambos têm times
        team1 = await self.db.get_team(player1_id)
        team2 = await self.db.get_team(player2_id)
        
        if not team1 or not team2:
            embed = EmbedBuilder.create_embed(
                "❌ Times Necessários",
                "Ambos os jogadores precisam ter times criados!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obtém jogadores titulares
        players1 = await self.db.get_user_players(player1_id)
        players2 = await self.db.get_user_players(player2_id)
        
        starters1 = [p for p in players1 if p['is_starter']][:5]
        starters2 = [p for p in players2 if p['is_starter']][:5]
        
        if len(starters1) < 5 or len(starters2) < 5:
            embed = EmbedBuilder.create_embed(
                "❌ Times Incompletos",
                "Ambos os times precisam ter 5 titulares!",
                COLORS['error']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Simula a partida
        score1, score2 = GameLogic.simulate_match(starters1, starters2)
        
        # Determina o vencedor
        if score1 > score2:
            winner_id = player1_id
            winner_name = interaction.user.display_name
            loser_id = player2_id
            loser_name = jogador.display_name
        else:
            winner_id = player2_id
            winner_name = jogador.display_name
            loser_id = player1_id
            loser_name = interaction.user.display_name
        
        # Cria embed do resultado
        embed = EmbedBuilder.create_embed(
            f"{EMOJIS['game']} Resultado da Partida",
            f"**{team1['team_name']}** {score1} - {score2} **{team2['team_name']}**",
            COLORS['primary']
        )
        
        embed.add_field(
            name="🏆 Vencedor",
            value=f"**{winner_name}** ({team1['team_name'] if winner_id == player1_id else team2['team_name']})",
            inline=True
        )
        
        embed.add_field(
            name="💰 Prêmios",
            value=f"Ganhador: +${ECONOMY['match_win_reward']}\nPerdedor: -${ECONOMY['match_lose_penalty']}",
            inline=True
        )
        
        # Adiciona estatísticas dos times
        overall1 = GameLogic.calculate_team_overall(starters1)
        overall2 = GameLogic.calculate_team_overall(starters2)
        
        embed.add_field(
            name="📊 Estatísticas",
            value=f"**{team1['team_name']}:** Overall {overall1:.1f}\n**{team2['team_name']}:** Overall {overall2:.1f}",
            inline=False
        )
        
        # Atualiza estatísticas no banco de dados
        # (implementar no database)
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="ranking", description="Mostra os rankings")
    @app_commands.describe(
        categoria="Tipo de ranking (overall, dinheiro, vitorias)"
    )
    @app_commands.choices(categoria=[
        app_commands.Choice(name="Overall", value="overall"),
        app_commands.Choice(name="Dinheiro", value="money"),
        app_commands.Choice(name="Vitórias", value="wins")
    ])
    async def show_rankings(self, interaction: discord.Interaction, categoria: str = "overall"):
        """Mostra os rankings"""
        await interaction.response.defer()
        
        # Obtém rankings
        rankings = await self.db.get_rankings()
        
        if not rankings or not rankings.get(categoria):
            embed = EmbedBuilder.create_embed(
                "📊 Ranking",
                "Nenhum dado disponível para este ranking.",
                COLORS['info']
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = EmbedBuilder.ranking_embed(rankings, categoria)
        
        # Adiciona botões para outros rankings
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Overall",
            custom_id="ranking_overall"
        ))
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Dinheiro",
            custom_id="ranking_money"
        ))
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Vitórias",
            custom_id="ranking_wins"
        ))
        
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(name="estatisticas", description="Mostra suas estatísticas")
    async def show_stats(self, interaction: discord.Interaction):
        """Mostra estatísticas do usuário"""
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
        
        # Obtém dados do usuário
        user = await self.db.get_user(user_id)
        players = await self.db.get_user_players(user_id)
        
        # Calcula estatísticas
        total_players = len(players)
        starters = [p for p in players if p['is_starter']]
        avg_overall = GameLogic.calculate_team_overall(starters) if starters else 0
        
        # Conta jogadores por raridade
        rarity_counts = {}
        for player in players:
            rarity = player['rarity']
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        # Cria embed
        embed = EmbedBuilder.create_embed(
            f"{EMOJIS['stats']} Estatísticas - {team['team_name']}",
            f"Estatísticas detalhadas do seu time",
            COLORS['primary']
        )
        
        embed.add_field(
            name="📊 Record",
            value=f"**Vitórias:** {team['wins']}\n**Derrotas:** {team['losses']}\n**Win Rate:** {(team['wins']/(team['wins']+team['losses'])*100):.1f}%" if (team['wins']+team['losses']) > 0 else "0%",
            inline=True
        )
        
        embed.add_field(
            name="💰 Economia",
            value=f"**Dinheiro:** ${user['money']:,}\n**Jogadores:** {total_players}\n**Titulares:** {len(starters)}/5",
            inline=True
        )
        
        embed.add_field(
            name="🏀 Time",
            value=f"**Overall Médio:** {avg_overall:.1f}\n**Melhor Jogador:** {max(players, key=lambda x: x['overall'])['name'] if players else 'N/A'}",
            inline=True
        )
        
        # Adiciona distribuição por raridade
        if rarity_counts:
            rarity_text = ""
            for rarity, count in rarity_counts.items():
                rarity_emoji = {'comum': '⚪', 'raro': '🔵', 'épico': '🟣', 'lendário': '🟡'}
                rarity_text += f"{rarity_emoji.get(rarity, '⚪')} {rarity}: {count}\n"
            
            embed.add_field(
                name="⭐ Raridades",
                value=rarity_text,
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="historico", description="Mostra histórico de partidas")
    async def show_match_history(self, interaction: discord.Interaction):
        """Mostra histórico de partidas"""
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
        
        # Por enquanto, mostra estatísticas básicas
        # (implementar histórico completo no database)
        
        embed = EmbedBuilder.create_embed(
            f"{EMOJIS['game']} Histórico de Partidas",
            f"Histórico de partidas do {team['team_name']}",
            COLORS['info']
        )
        
        embed.add_field(
            name="📊 Resumo",
            value=f"**Total de Partidas:** {team['wins'] + team['losses']}\n"
                  f"**Vitórias:** {team['wins']}\n"
                  f"**Derrotas:** {team['losses']}\n"
                  f"**Win Rate:** {(team['wins']/(team['wins']+team['losses'])*100):.1f}%" if (team['wins']+team['losses']) > 0 else "0%",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Informação",
            value="Histórico detalhado de partidas será implementado em breve!",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MatchesCog(bot))
