import os
from typing import Dict, List
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Configurações do Bot
BOT_TOKEN = os.getenv('BOT_TOKEN', 'SEU_TOKEN_AQUI')
BOT_PREFIX = '!'

# Cores para Embeds
COLORS = {
    'primary': 0x1e90ff,      # Azul NBA
    'success': 0x00ff00,      # Verde
    'error': 0xff0000,        # Vermelho
    'warning': 0xffa500,      # Laranja
    'info': 0x00bfff,         # Azul claro
    'purple': 0x8a2be2,       # Roxo
    'gold': 0xffd700,         # Dourado
    'silver': 0xc0c0c0,       # Prata
    'bronze': 0xcd7f32        # Bronze
}

# Raridades dos Jogadores
RARITIES = {
    'comum': {'name': 'Comum', 'color': 0x808080, 'chance': 60, 'multiplier': 1.0},
    'raro': {'name': 'Raro', 'color': 0x1e90ff, 'chance': 25, 'multiplier': 2.0},
    'épico': {'name': 'Épico', 'color': 0x8a2be2, 'chance': 12, 'multiplier': 5.0},
    'lendário': {'name': 'Lendário', 'color': 0xffd700, 'chance': 3, 'multiplier': 15.0}
}

# Configurações Econômicas
ECONOMY = {
    'starting_money': 10000,
    'match_win_reward': 500,
    'match_loss_penalty': 200,  # Corrigido de match_lose_penalty
    'daily_reward': 1000,
    'pack_cost': 5000
}

# Configurações de Tempo (em segundos)
TIMERS = {
    'shop_refresh': 600,      # 10 minutos
    'free_pack': 1500,        # 25 minutos
    'daily_reset': 86400      # 24 horas
}

# Times da NBA 2025
NBA_TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks",
    "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns",
    "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors",
    "Utah Jazz", "Washington Wizards"
]

# Idiomas Suportados
LANGUAGES = {
    'pt': 'Português',
    'en': 'English',
    'es': 'Español'
}

# Configurações de Partida
MATCH_SETTINGS = {
    'max_players_per_team': 15,
    'starters_count': 5,
    'bench_count': 10,
    'match_duration': 300,  # 5 minutos
    'decision_time': 30     # 30 segundos para decisões
}

# Emojis
EMOJIS = {
    'basketball': '🏀',
    'money': '💰',
    'trophy': '🏆',
    'star': '⭐',
    'fire': '🔥',
    'check': '✅',
    'cross': '❌',
    'arrow_up': '⬆️',
    'arrow_down': '⬇️',
    'reload': '🔄',
    'shop': '🛒',
    'team': '👥',
    'stats': '📊',
    'game': '🎮'
}
