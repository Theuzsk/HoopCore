import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio
from datetime import datetime
from database import Database
from utils import EmbedBuilder, ButtonBuilder, GameLogic
from config import COLORS, EMOJIS, ECONOMY, MATCH_SETTINGS
import random

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
    async def start_match(self, interaction: discord.Interaction):
        """Inicia uma partida simulada"""
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
        
        # Verifica se tem 5 titulares
        players = await self.db.get_user_players(user_id)
        starters = [p for p in players if p['is_starter']]
        
        if len(starters) < 5:
            embed = EmbedBuilder.create_embed(
                "⚠️ Time Incompleto",
                f"Você precisa de 5 titulares para jogar. Atualmente tem {len(starters)}.",
                COLORS['warning']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Inicia a partida
        await self.start_interactive_match(interaction, team, starters)
    
    async def start_interactive_match(self, interaction, team, starters):
        """Inicia partida interativa"""
        # Calcula overall do time
        team_overall = sum(p['overall'] for p in starters) / len(starters)
        
        # Cria embed inicial da partida
        embed = discord.Embed(
            title="🏀 Partida Iniciada!",
            description=f"**{team['team_name']}** vs **CPU**\n\n"
                       f"Overall do Time: **{team_overall:.1f}**\n"
                       f"Quartos: 4 x 12 minutos\n\n"
                       f"Clique em **Iniciar** para começar!",
            color=0x00ff00
        )
        
        # Botão para iniciar
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.green,
            label="🚀 Iniciar Partida",
            emoji="🏀",
            custom_id="start_match"
        ))
        
        await interaction.followup.send(embed=embed, view=view)
    
    async def handle_match_situation(self, interaction, quarter, time, score_player, score_cpu):
        """Lida com situação da partida"""
        # Situações variadas baseadas no momento da partida
        situations = [
            {
                "name": "🏀 Ataque Rápido",
                "description": "Seu time tem uma chance de contra-ataque!",
                "options": [
                    {"label": "⚡ Correr para a cesta", "custom_id": "fast_break_run", "success_rate": 0.7},
                    {"label": "🎯 Passar para o ala", "custom_id": "fast_break_pass", "success_rate": 0.8},
                    {"label": "🏃‍♂️ Drible e finalização", "custom_id": "fast_break_dribble", "success_rate": 0.6}
                ]
            },
            {
                "name": "🎯 Arremesso de 3 Pontos",
                "description": "Chance de arremesso de longa distância!",
                "options": [
                    {"label": "🎯 Arremesso limpo", "custom_id": "three_clean", "success_rate": 0.4},
                    {"label": "🏃‍♂️ Drible e arremesso", "custom_id": "three_dribble", "success_rate": 0.3},
                    {"label": "🤝 Passar para melhor posição", "custom_id": "three_pass", "success_rate": 0.9}
                ]
            },
            {
                "name": "💪 Jogo Interior",
                "description": "Chance de jogada próxima à cesta!",
                "options": [
                    {"label": "🏀 Hook shot", "custom_id": "inside_hook", "success_rate": 0.6},
                    {"label": "💪 Post-up", "custom_id": "inside_post", "success_rate": 0.7},
                    {"label": "🔄 Girar e finalizar", "custom_id": "inside_spin", "success_rate": 0.5}
                ]
            },
            {
                "name": "🛡️ Defesa",
                "description": "O adversário está atacando!",
                "options": [
                    {"label": "🛡️ Bloqueio", "custom_id": "defense_block", "success_rate": 0.3},
                    {"label": "🏃‍♂️ Roubar a bola", "custom_id": "defense_steal", "success_rate": 0.4},
                    {"label": "📏 Forçar arremesso ruim", "custom_id": "defense_contest", "success_rate": 0.7}
                ]
            },
            {
                "name": "🎭 Jogada Especial",
                "description": "Chance de uma jogada espetacular!",
                "options": [
                    {"label": "🔥 Alley-oop", "custom_id": "special_alley", "success_rate": 0.2},
                    {"label": "💫 Crossover", "custom_id": "special_crossover", "success_rate": 0.4},
                    {"label": "🚀 Tomahawk dunk", "custom_id": "special_tomahawk", "success_rate": 0.3}
                ]
            },
            {
                "name": "⏰ Final de Quarto",
                "description": "Última chance do quarto!",
                "options": [
                    {"label": "🎯 Arremesso de 3", "custom_id": "quarter_three", "success_rate": 0.3},
                    {"label": "🏃‍♂️ Penetração", "custom_id": "quarter_drive", "success_rate": 0.6},
                    {"label": "🤝 Passar para finalização", "custom_id": "quarter_pass", "success_rate": 0.8}
                ]
            }
        ]
        
        # Escolhe situação baseada no momento
        if quarter == 4 and time <= 60:  # Final do jogo
            situation = situations[5]  # Final de quarto
        elif time <= 30:  # Final do quarto
            situation = situations[5]  # Final de quarto
        elif score_player > score_cpu + 10:  # Time na frente
            situation = random.choice(situations[0:3])  # Ataque
        elif score_cpu > score_player + 10:  # Time atrás
            situation = random.choice(situations[0:3])  # Ataque agressivo
        else:  # Jogo equilibrado
            situation = random.choice(situations)
        
        # Cria embed da situação
        embed = discord.Embed(
            title=situation["name"],
            description=f"{situation['description']}\n\n"
                       f"**Quarto {quarter}** | **{time}s** restantes\n"
                       f"**Placar:** {score_player} x {score_cpu}",
            color=0x1e90ff
        )
        
        # Cria botões para as opções
        view = discord.ui.View()
        for option in situation["options"]:
            button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label=option["label"],
                custom_id=f"match_{option['custom_id']}_{quarter}_{time}_{score_player}_{score_cpu}",
                emoji="🎯"
            )
            view.add_item(button)
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def resolve_match_action(self, interaction, action, quarter, time, score_player, score_cpu):
        """Resolve a ação escolhida na partida"""
        # Mapeia ações para resultados
        action_results = {
            "fast_break_run": {"success": "🏃‍♂️ **Contra-ataque perfeito!** +2 pontos", "fail": "❌ Defesa interceptou o passe"},
            "fast_break_pass": {"success": "🤝 **Passe perfeito!** +2 pontos", "fail": "❌ Passe interceptado"},
            "fast_break_dribble": {"success": "🏀 **Drible e finalização!** +2 pontos", "fail": "❌ Bola roubada"},
            
            "three_clean": {"success": "🎯 **Três pontos!** +3 pontos", "fail": "❌ Arremesso errou"},
            "three_dribble": {"success": "🏃‍♂️ **Três pontos com drible!** +3 pontos", "fail": "❌ Arremesso errou"},
            "three_pass": {"success": "🤝 **Passe para posição melhor!** +2 pontos", "fail": "❌ Passe interceptado"},
            
            "inside_hook": {"success": "🏀 **Hook shot perfeito!** +2 pontos", "fail": "❌ Hook shot errou"},
            "inside_post": {"success": "💪 **Post-up dominante!** +2 pontos", "fail": "❌ Defesa forçou erro"},
            "inside_spin": {"success": "🔄 **Giro e finalização!** +2 pontos", "fail": "❌ Giro perdeu o equilíbrio"},
            
            "defense_block": {"success": "🛡️ **Bloqueio espetacular!** Bola recuperada", "fail": "❌ Bloqueio falhou, +2 pontos CPU"},
            "defense_steal": {"success": "🏃‍♂️ **Roubo de bola!** Contra-ataque", "fail": "❌ Roubo falhou, +2 pontos CPU"},
            "defense_contest": {"success": "📏 **Arremesso contestado!** CPU errou", "fail": "❌ Contestação falhou, +2 pontos CPU"},
            
            "special_alley": {"success": "🔥 **ALLEY-OOP ESPETACULAR!** +3 pontos", "fail": "❌ Alley-oop falhou"},
            "special_crossover": {"success": "💫 **CROSSOVER PERFEITO!** +2 pontos", "fail": "❌ Crossover falhou"},
            "special_tomahawk": {"success": "🚀 **TOMAHAWK DUNK!** +3 pontos", "fail": "❌ Dunk falhou"},
            
            "quarter_three": {"success": "🎯 **TRÊS PONTOS NO FINAL!** +3 pontos", "fail": "❌ Arremesso final errou"},
            "quarter_drive": {"success": "🏃‍♂️ **Penetração perfeita!** +2 pontos", "fail": "❌ Penetração falhou"},
            "quarter_pass": {"success": "🤝 **Passe para finalização!** +2 pontos", "fail": "❌ Passe final falhou"}
        }
        
        # Obtém resultado da ação
        action_key = action.split("_", 1)[1]  # Remove "match_" do início
        result = action_results.get(action_key, {"success": "✅ Ação bem-sucedida!", "fail": "❌ Ação falhou"})
        
        # Simula dados de RPG (1-100)
        roll = random.randint(1, 100)
        
        # Determina sucesso baseado na taxa de sucesso da ação
        success_rate = 0.5  # Taxa padrão
        for situation in self.get_match_situations():
            for option in situation["options"]:
                if option["custom_id"] == action_key:
                    success_rate = option["success_rate"]
                    break
        
        # Calcula sucesso (roll <= success_rate * 100)
        is_success = roll <= (success_rate * 100)
        
        # Atualiza placar
        if is_success:
            if "pontos" in result["success"]:
                if "+3 pontos" in result["success"]:
                    score_player += 3
                elif "+2 pontos" in result["success"]:
                    score_player += 2
        else:
            if "pontos" in result["fail"]:
                if "+2 pontos" in result["fail"]:
                    score_cpu += 2
                elif "+3 pontos" in result["fail"]:
                    score_cpu += 3
        
        # Cria embed do resultado
        embed = discord.Embed(
            title="🎯 Resultado da Jogada",
            description=f"**Dados:** {roll}/100\n"
                       f"**Taxa de Sucesso:** {success_rate*100:.0f}%\n\n"
                       f"**Resultado:** {result['success'] if is_success else result['fail']}\n\n"
                       f"**Placar Atual:** {score_player} x {score_cpu}",
            color=0x00ff00 if is_success else 0xff0000
        )
        
        # Adiciona informações do jogo
        embed.add_field(
            name="⏰ Tempo",
            value=f"Quarto {quarter} | {time}s restantes",
            inline=True
        )
        
        # Botão para continuar
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.green,
            label="▶️ Continuar",
            emoji="🏀",
            custom_id=f"continue_match_{quarter}_{time}_{score_player}_{score_cpu}"
        ))
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    def get_match_situations(self):
        """Retorna todas as situações possíveis"""
        return [
            {
                "name": "🏀 Ataque Rápido",
                "description": "Seu time tem uma chance de contra-ataque!",
                "options": [
                    {"label": "⚡ Correr para a cesta", "custom_id": "fast_break_run", "success_rate": 0.7},
                    {"label": "🎯 Passar para o ala", "custom_id": "fast_break_pass", "success_rate": 0.8},
                    {"label": "🏃‍♂️ Drible e finalização", "custom_id": "fast_break_dribble", "success_rate": 0.6}
                ]
            },
            {
                "name": "🎯 Arremesso de 3 Pontos",
                "description": "Chance de arremesso de longa distância!",
                "options": [
                    {"label": "🎯 Arremesso limpo", "custom_id": "three_clean", "success_rate": 0.4},
                    {"label": "🏃‍♂️ Drible e arremesso", "custom_id": "three_dribble", "success_rate": 0.3},
                    {"label": "🤝 Passar para melhor posição", "custom_id": "three_pass", "success_rate": 0.9}
                ]
            },
            {
                "name": "💪 Jogo Interior",
                "description": "Chance de jogada próxima à cesta!",
                "options": [
                    {"label": "🏀 Hook shot", "custom_id": "inside_hook", "success_rate": 0.6},
                    {"label": "💪 Post-up", "custom_id": "inside_post", "success_rate": 0.7},
                    {"label": "🔄 Girar e finalizar", "custom_id": "inside_spin", "success_rate": 0.5}
                ]
            },
            {
                "name": "🛡️ Defesa",
                "description": "O adversário está atacando!",
                "options": [
                    {"label": "🛡️ Bloqueio", "custom_id": "defense_block", "success_rate": 0.3},
                    {"label": "🏃‍♂️ Roubar a bola", "custom_id": "defense_steal", "success_rate": 0.4},
                    {"label": "📏 Forçar arremesso ruim", "custom_id": "defense_contest", "success_rate": 0.7}
                ]
            },
            {
                "name": "🎭 Jogada Especial",
                "description": "Chance de uma jogada espetacular!",
                "options": [
                    {"label": "🔥 Alley-oop", "custom_id": "special_alley", "success_rate": 0.2},
                    {"label": "💫 Crossover", "custom_id": "special_crossover", "success_rate": 0.4},
                    {"label": "🚀 Tomahawk dunk", "custom_id": "special_tomahawk", "success_rate": 0.3}
                ]
            },
            {
                "name": "⏰ Final de Quarto",
                "description": "Última chance do quarto!",
                "options": [
                    {"label": "🎯 Arremesso de 3", "custom_id": "quarter_three", "success_rate": 0.3},
                    {"label": "🏃‍♂️ Penetração", "custom_id": "quarter_drive", "success_rate": 0.6},
                    {"label": "🤝 Passar para finalização", "custom_id": "quarter_pass", "success_rate": 0.8}
                ]
            }
        ]
    
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
        
        if not rankings:
            embed = EmbedBuilder.create_embed(
                "📊 Ranking",
                "Nenhum dado disponível para rankings ainda.",
                COLORS['info']
            )
            await interaction.followup.send(embed=embed)
            return
        
        if not rankings.get(categoria) or len(rankings[categoria]) == 0:
            if categoria == "overall":
                message = "Nenhum time com 5 titulares ainda para calcular overall."
            elif categoria == "money":
                message = "Nenhum time criado ainda."
            else:
                message = "Nenhuma partida jogada ainda."
            
            embed = EmbedBuilder.create_embed(
                "📊 Ranking",
                message,
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
