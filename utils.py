import discord
from discord import app_commands
from discord.ext import commands
from typing import Dict, List, Optional, Tuple
import math
from config import COLORS, RARITIES, EMOJIS
import random

class EmbedBuilder:
    """Classe para criar embeds profissionais e consistentes"""
    
    @staticmethod
    def create_embed(title: str, description: str = "", color: int = COLORS['primary'], 
                    thumbnail: str = None, footer: str = None) -> discord.Embed:
        """Cria um embed básico"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        
        if footer:
            embed.set_footer(text=footer)
        
        return embed
    
    @staticmethod
    def player_card(player: Dict, show_details: bool = True) -> discord.Embed:
        """Cria um card de jogador"""
        rarity_info = RARITIES.get(player['rarity'], {})
        color = rarity_info.get('color', COLORS['primary'])
        
        embed = discord.Embed(
            title=f"{player['name']} {EMOJIS['basketball']}",
            color=color
        )
        
        embed.add_field(
            name="📊 Overall",
            value=f"**{player['overall']}**",
            inline=True
        )
        
        embed.add_field(
            name="🏀 Posição",
            value=f"**{player['position']}**",
            inline=True
        )
        
        embed.add_field(
            name="📏 Altura",
            value=f"**{player['height']}**",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Time",
            value=f"**{player['team']}**",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Raridade",
            value=f"**{rarity_info.get('name', player['rarity'])}**",
            inline=True
        )
        
        if show_details:
            embed.add_field(
                name="💰 Valor",
                value=f"**${player['market_value']:,}**",
                inline=True
            )
        
        # Adiciona emoji baseado na raridade
        rarity_emoji = {
            'comum': '⚪',
            'raro': '🔵',
            'épico': '🟣',
            'lendário': '🟡'
        }
        
        embed.description = f"{rarity_emoji.get(player['rarity'], '⚪')} **{rarity_info.get('name', player['rarity'])}**"
        
        return embed
    
    @staticmethod
    def team_overview(team: Dict, players: List[Dict], user_money: int) -> discord.Embed:
        """Cria overview do time"""
        starters = [p for p in players if p['is_starter']]
        bench = [p for p in players if not p['is_starter']]
        
        avg_overall = sum(p['overall'] for p in starters) / len(starters) if starters else 0
        
        embed = discord.Embed(
            title=f"🏀 {team['team_name']}",
            color=COLORS['primary']
        )
        
        embed.add_field(
            name="📊 Estatísticas",
            value=f"**Vitórias:** {team['wins']}\n**Derrotas:** {team['losses']}\n**Overall:** {avg_overall:.1f}",
            inline=True
        )
        
        embed.add_field(
            name="💰 Economia",
            value=f"**Dinheiro:** ${user_money:,}",
            inline=True
        )
        
        embed.add_field(
            name="👥 Jogadores",
            value=f"**Titulares:** {len(starters)}/5\n**Reservas:** {len(bench)}",
            inline=True
        )
        
        # Lista titulares
        if starters:
            starters_text = "\n".join([f"• {p['name']} ({p['overall']})" for p in starters[:5]])
            embed.add_field(
                name="⭐ Titulares",
                value=starters_text,
                inline=False
            )
        
        return embed
    
    @staticmethod
    def shop_embed(items: List[Dict]) -> discord.Embed:
        """Cria embed da loja"""
        embed = discord.Embed(
            title=f"{EMOJIS['shop']} Loja da NBA",
            description="Jogadores disponíveis para compra!",
            color=COLORS['info']
        )
        
        for i, item in enumerate(items[:10], 1):  # Máximo 10 itens
            rarity_info = RARITIES.get(item['rarity'], {})
            rarity_emoji = {
                'comum': '⚪',
                'raro': '🔵',
                'épico': '🟣',
                'lendário': '🟡'
            }
            
            embed.add_field(
                name=f"{i}. {item['name']} {rarity_emoji.get(item['rarity'], '⚪')}",
                value=f"Overall: **{item['overall']}** | Preço: **${item['price']:,}**\n"
                      f"Time: {item['team']} | Posição: {item['position']}",
                inline=False
            )
        
        embed.set_footer(text="Use /comprar <número> para comprar um jogador")
        return embed
    
    @staticmethod
    def ranking_embed(rankings: Dict, category: str) -> discord.Embed:
        """Cria embed de ranking"""
        titles = {
            'overall': f"{EMOJIS['star']} Ranking por Overall",
            'money': f"{EMOJIS['money']} Ranking por Dinheiro",
            'wins': f"{EMOJIS['trophy']} Ranking por Vitórias"
        }
        
        embed = discord.Embed(
            title=titles.get(category, "Ranking"),
            color=COLORS['gold']
        )
        
        ranking_data = rankings.get(category, [])
        
        for i, entry in enumerate(ranking_data[:10], 1):
            if category == 'overall':
                value = f"**{entry['username']}** - {entry['team_name']}\nOverall: **{entry['value']}**"
            elif category == 'money':
                value = f"**{entry['username']}** - {entry['team_name']}\nDinheiro: **${entry['value']:,}**"
            else:  # wins
                value = f"**{entry['username']}** - {entry['team_name']}\nVitórias: **{entry['value']}**"
            
            embed.add_field(
                name=f"{i}. {entry['team_name']}",
                value=value,
                inline=False
            )
        
        return embed
    
    @staticmethod
    def match_embed(challenger: str, challenged: str, match_id: int) -> discord.Embed:
        """Cria embed de desafio"""
        embed = discord.Embed(
            title=f"{EMOJIS['game']} Desafio de Basquete!",
            description=f"**{challenger}** desafia **{challenged}** para uma partida!",
            color=COLORS['warning']
        )
        
        embed.add_field(
            name="🏆 Prêmio",
            value=f"Ganhador: +${500}\nPerdedor: -${200}",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Tempo",
            value="5 minutos de partida",
            inline=True
        )
        
        embed.set_footer(text=f"Match ID: {match_id}")
        return embed

class ButtonBuilder:
    """Classe para criar botões interativos"""
    
    @staticmethod
    def accept_decline_buttons() -> List[discord.ui.Button]:
        """Cria botões de aceitar/recusar"""
        return [
            discord.ui.Button(
                style=discord.ButtonStyle.green,
                label="Aceitar",
                emoji=EMOJIS['check'],
                custom_id="accept_match"
            ),
            discord.ui.Button(
                style=discord.ButtonStyle.red,
                label="Recusar",
                emoji=EMOJIS['cross'],
                custom_id="decline_match"
            )
        ]
    
    @staticmethod
    def shop_buttons() -> List[discord.ui.Button]:
        """Cria botões da loja"""
        return [
            discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="Atualizar",
                emoji=EMOJIS['reload'],
                custom_id="refresh_shop"
            ),
            discord.ui.Button(
                style=discord.ButtonStyle.success,
                label="Comprar Pack",
                emoji=EMOJIS['shop'],
                custom_id="buy_pack"
            )
        ]
    
    @staticmethod
    def match_buttons() -> List[discord.ui.Button]:
        """Cria botões de partida"""
        return [
            discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="Ofensiva",
                emoji="⚡",
                custom_id="offensive_play"
            ),
            discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Defensiva",
                emoji="🛡️",
                custom_id="defensive_play"
            ),
            discord.ui.Button(
                style=discord.ButtonStyle.success,
                label="Contra-ataque",
                emoji="🏃",
                custom_id="fast_break"
            )
        ]

class GameLogic:
    """Classe com lógica do jogo"""
    
    @staticmethod
    def calculate_team_overall(players: List[Dict]) -> float:
        """Calcula o overall médio do time"""
        if not players:
            return 0
        
        total_overall = sum(p['overall'] for p in players)
        return total_overall / len(players)
    
    @staticmethod
    def simulate_match(team1_players: List[Dict], team2_players: List[Dict]) -> Tuple[int, int]:
        """Simula uma partida entre dois times"""
        team1_overall = GameLogic.calculate_team_overall(team1_players)
        team2_overall = GameLogic.calculate_team_overall(team2_players)
        
        # Base score
        team1_base = 80 + (team1_overall - 75) * 2
        team2_base = 80 + (team2_overall - 75) * 2
        
        # Random factor
        team1_score = int(team1_base + (random.randint(-10, 10)))
        team2_score = int(team2_base + (random.randint(-10, 10)))
        
        # Ensure minimum score
        team1_score = max(70, team1_score)
        team2_score = max(70, team2_score)
        
        return team1_score, team2_score
    
    @staticmethod
    def format_money(amount: int) -> str:
        """Formata valor monetário"""
        if amount >= 1_000_000:
            return f"${amount/1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"${amount/1_000:.1f}K"
        else:
            return f"${amount:,}"
    
    @staticmethod
    def get_rarity_color(rarity: str) -> int:
        """Obtém cor baseada na raridade"""
        return RARITIES.get(rarity, {}).get('color', COLORS['primary'])

class LanguageManager:
    """Gerenciador de idiomas"""
    
    TRANSLATIONS = {
        'pt': {
            'welcome': 'Bem-vindo ao HoopCore!',
            'team_created': 'Time criado com sucesso!',
            'player_acquired': 'Jogador adquirido!',
            'insufficient_money': 'Dinheiro insuficiente!',
            'match_challenge': 'Desafio enviado!',
            'match_accepted': 'Partida aceita!',
            'match_declined': 'Partida recusada!',
            'victory': 'Vitória!',
            'defeat': 'Derrota!',
            'shop_refreshed': 'Loja atualizada!',
            'daily_reward': 'Recompensa diária coletada!',
            'free_pack': 'Pack gratuito aberto!'
        },
        'en': {
            'welcome': 'Welcome to HoopCore!',
            'team_created': 'Team created successfully!',
            'player_acquired': 'Player acquired!',
            'insufficient_money': 'Insufficient money!',
            'match_challenge': 'Challenge sent!',
            'match_accepted': 'Match accepted!',
            'match_declined': 'Match declined!',
            'victory': 'Victory!',
            'defeat': 'Defeat!',
            'shop_refreshed': 'Shop refreshed!',
            'daily_reward': 'Daily reward collected!',
            'free_pack': 'Free pack opened!'
        },
        'es': {
            'welcome': '¡Bienvenido a HoopCore!',
            'team_created': '¡Equipo creado exitosamente!',
            'player_acquired': '¡Jugador adquirido!',
            'insufficient_money': '¡Dinero insuficiente!',
            'match_challenge': '¡Desafío enviado!',
            'match_accepted': '¡Partido aceptado!',
            'match_declined': '¡Partido rechazado!',
            'victory': '¡Victoria!',
            'defeat': '¡Derrota!',
            'shop_refreshed': '¡Tienda actualizada!',
            'daily_reward': '¡Recompensa diaria recolectada!',
            'free_pack': '¡Pack gratuito abierto!'
        }
    }
    
    @staticmethod
    def get_text(key: str, language: str = 'pt') -> str:
        """Obtém texto traduzido"""
        return LanguageManager.TRANSLATIONS.get(language, LanguageManager.TRANSLATIONS['pt']).get(key, key)
