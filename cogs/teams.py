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
    async def set_starter(self, interaction: discord.Interaction):
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
        
        # Obtém jogadores
        players = await self.db.get_user_players(user_id)
        
        if not players:
            embed = EmbedBuilder.create_embed(
                "📭 Sem Jogadores",
                "Você não tem jogadores para definir como titular!",
                COLORS['warning']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Filtra apenas reservas (não titulares)
        bench_players = [p for p in players if not p['is_starter']]
        
        if not bench_players:
            embed = EmbedBuilder.create_embed(
                "ℹ️ Todos Titulares",
                "Todos os seus jogadores já são titulares!",
                COLORS['info']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Cria embed com lista de jogadores
        embed = EmbedBuilder.create_embed(
            "⭐ Definir Titular",
            "Selecione um jogador para definir como titular:",
            COLORS['primary']
        )
        
        # Cria menu suspenso com jogadores
        options = []
        for player in bench_players[:25]:  # Discord limita a 25 opções
            rarity_emoji = {'comum': '⚪', 'raro': '🔵', 'épico': '🟣', 'lendário': '🟡'}
            emoji = rarity_emoji.get(player['rarity'], '⚪')
            options.append(discord.SelectOption(
                label=f"{player['name']} ({player['overall']})",
                value=str(player['id']),
                description=f"{player['position']} - {player['team']}",
                emoji=emoji
            ))
        
        # Cria o menu suspenso
        select = discord.ui.Select(
            placeholder="Escolha um jogador...",
            options=options,
            custom_id="select_starter"
        )
        
        # Cria a view
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(name="reserva", description="Define um jogador como reserva")
    async def set_bench(self, interaction: discord.Interaction):
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
        
        # Obtém jogadores
        players = await self.db.get_user_players(user_id)
        
        if not players:
            embed = EmbedBuilder.create_embed(
                "📭 Sem Jogadores",
                "Você não tem jogadores para definir como reserva!",
                COLORS['warning']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Filtra apenas titulares
        starter_players = [p for p in players if p['is_starter']]
        
        if not starter_players:
            embed = EmbedBuilder.create_embed(
                "ℹ️ Sem Titulares",
                "Você não tem jogadores titulares para definir como reserva!",
                COLORS['info']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Cria embed com lista de jogadores
        embed = EmbedBuilder.create_embed(
            "🪑 Definir Reserva",
            "Selecione um jogador para definir como reserva:",
            COLORS['primary']
        )
        
        # Cria menu suspenso com jogadores
        options = []
        for player in starter_players[:25]:  # Discord limita a 25 opções
            rarity_emoji = {'comum': '⚪', 'raro': '🔵', 'épico': '🟣', 'lendário': '🟡'}
            emoji = rarity_emoji.get(player['rarity'], '⚪')
            options.append(discord.SelectOption(
                label=f"{player['name']} ({player['overall']})",
                value=str(player['id']),
                description=f"{player['position']} - {player['team']}",
                emoji=emoji
            ))
        
        # Cria o menu suspenso
        select = discord.ui.Select(
            placeholder="Escolha um jogador...",
            options=options,
            custom_id="select_bench"
        )
        
        # Cria a view
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(name="vender", description="Vende um jogador")
    async def sell_player(self, interaction: discord.Interaction):
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
        
        # Obtém jogadores
        players = await self.db.get_user_players(user_id)
        
        if not players:
            embed = EmbedBuilder.create_embed(
                "📭 Sem Jogadores",
                "Você não tem jogadores para vender!",
                COLORS['warning']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Cria embed com lista de jogadores
        embed = EmbedBuilder.create_embed(
            "💰 Vender Jogador",
            "Selecione um jogador para vender:",
            COLORS['warning']
        )
        
        # Cria menu suspenso com jogadores
        options = []
        for player in players[:25]:  # Discord limita a 25 opções
            rarity_emoji = {'comum': '⚪', 'raro': '🔵', 'épico': '🟣', 'lendário': '🟡'}
            sell_value = int(player['market_value'] * 0.8)
            emoji = rarity_emoji.get(player['rarity'], '⚪')
            
            options.append(discord.SelectOption(
                label=f"{player['name']} (${sell_value:,})",
                value=str(player['id']),
                description=f"Overall: {player['overall']} | {player['position']} - {player['team']}",
                emoji=emoji
            ))
        
        # Cria o menu suspenso
        select = discord.ui.Select(
            placeholder="Escolha um jogador para vender...",
            options=options,
            custom_id="select_sell"
        )
        
        # Cria a view
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="posicao", description="Define a posição de um jogador no time")
    async def set_position(self, interaction: discord.Interaction):
        """Define a posição de um jogador no time"""
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
        
        # Obtém jogadores titulares
        players = await self.db.get_user_players(user_id)
        starter_players = [p for p in players if p['is_starter']]
        
        if len(starter_players) < 5:
            embed = EmbedBuilder.create_embed(
                "⚠️ Time Incompleto",
                f"Você precisa de 5 titulares para definir posições. Atualmente tem {len(starter_players)}.",
                COLORS['warning']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Cria embed com posições
        embed = EmbedBuilder.create_embed(
            "🏀 Definir Posições",
            "Selecione a posição para cada jogador:",
            COLORS['primary']
        )
        
        # Posições do basquete
        positions = {
            'PG': 'Point Guard (Armador)',
            'SG': 'Shooting Guard (Ala-armador)', 
            'SF': 'Small Forward (Ala)',
            'PF': 'Power Forward (Ala-pivô)',
            'C': 'Center (Pivô)'
        }
        
        # Cria menus suspensos para cada posição
        view = discord.ui.View()
        
        for pos, desc in positions.items():
            # Filtra jogadores recomendados para cada posição
            recommended_players = []
            for player in starter_players:
                if player['position'] == pos:
                    recommended_players.append(player)
            
            # Cria opções para o menu
            options = []
            for player in starter_players:
                is_recommended = player['position'] == pos
                emoji = "⭐" if is_recommended else "⚪"
                label = f"{player['name']} ({player['overall']})"
                description = f"{player['position']} - {player['team']}"
                
                options.append(discord.SelectOption(
                    label=label,
                    value=f"{pos}_{player['id']}",
                    description=description,
                    emoji=emoji
                ))
            
            # Cria o menu para esta posição
            select = discord.ui.Select(
                placeholder=f"Selecione {pos} ({desc})",
                options=options,
                custom_id=f"position_{pos}"
            )
            view.add_item(select)
        
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(TeamsCog(bot))
