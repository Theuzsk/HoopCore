import sqlite3
import json
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import random
from config import ECONOMY, NBA_TEAMS, RARITIES

class Database:
    def __init__(self, db_path: str = "hoopcore.db"):
        self.db_path = db_path
        self.init_database()
        self.load_players_data()
        self.refresh_shop()  # Inicializa a loja
    
    def init_database(self):
        """Inicializa o banco de dados com todas as tabelas necessárias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                money INTEGER DEFAULT 10000,
                language TEXT DEFAULT 'pt',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_daily TIMESTAMP,
                last_free_pack TIMESTAMP
            )
        ''')
        
        # Tabela de times
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                team_name TEXT NOT NULL,
                team_logo TEXT,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Tabela de jogadores (banco de dados de jogadores reais)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                overall INTEGER NOT NULL,
                height TEXT NOT NULL,
                team TEXT NOT NULL,
                rarity TEXT NOT NULL,
                market_value INTEGER NOT NULL,
                position TEXT NOT NULL
            )
        ''')
        
        # Tabela de jogadores dos usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                player_id INTEGER,
                is_starter BOOLEAN DEFAULT FALSE,
                acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (player_id) REFERENCES players (player_id)
            )
        ''')
        
        # Tabela de loja
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER,
                price INTEGER NOT NULL,
                expires_at TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players (player_id)
            )
        ''')
        
        # Tabela de partidas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER,
                challenged_id INTEGER,
                status TEXT DEFAULT 'pending',
                winner_id INTEGER,
                challenger_score INTEGER DEFAULT 0,
                challenged_score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                FOREIGN KEY (challenger_id) REFERENCES users (user_id),
                FOREIGN KEY (challenged_id) REFERENCES users (user_id),
                FOREIGN KEY (winner_id) REFERENCES users (user_id)
            )
        ''')
        
        # Tabela de configurações do servidor
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_settings (
                server_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'pt',
                prefix TEXT DEFAULT '!'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_players_data(self):
        """Carrega dados dos jogadores da NBA 2025"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verifica se já existem jogadores
        cursor.execute("SELECT COUNT(*) FROM players")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        # Dados dos jogadores da NBA 2025 (exemplos)
        players_data = [
            # Lendários
            ("LeBron James", 95, "2.06m", "Los Angeles Lakers", "lendário", 50000000, "SF"),
            ("Stephen Curry", 94, "1.88m", "Golden State Warriors", "lendário", 48000000, "PG"),
            ("Kevin Durant", 93, "2.08m", "Phoenix Suns", "lendário", 45000000, "SF"),
            ("Giannis Antetokounmpo", 96, "2.11m", "Milwaukee Bucks", "lendário", 52000000, "PF"),
            ("Nikola Jokić", 97, "2.11m", "Denver Nuggets", "lendário", 55000000, "C"),
            ("Luka Dončić", 94, "2.01m", "Dallas Mavericks", "lendário", 47000000, "PG"),
            ("Joel Embiid", 95, "2.13m", "Philadelphia 76ers", "lendário", 50000000, "C"),
            ("Jayson Tatum", 92, "2.03m", "Boston Celtics", "lendário", 43000000, "SF"),
            
            # Épicos
            ("Ja Morant", 89, "1.88m", "Memphis Grizzlies", "épico", 35000000, "PG"),
            ("Zion Williamson", 88, "1.98m", "New Orleans Pelicans", "épico", 32000000, "PF"),
            ("Anthony Edwards", 87, "1.93m", "Minnesota Timberwolves", "épico", 30000000, "SG"),
            ("Tyrese Haliburton", 86, "1.96m", "Indiana Pacers", "épico", 28000000, "PG"),
            ("Shai Gilgeous-Alexander", 90, "1.98m", "Oklahoma City Thunder", "épico", 38000000, "PG"),
            ("Devin Booker", 88, "1.96m", "Phoenix Suns", "épico", 33000000, "SG"),
            ("Damian Lillard", 87, "1.88m", "Milwaukee Bucks", "épico", 31000000, "PG"),
            ("Jimmy Butler", 88, "2.01m", "Miami Heat", "épico", 34000000, "SF"),
            
            # Raros
            ("Bam Adebayo", 85, "2.06m", "Miami Heat", "raro", 25000000, "C"),
            ("Pascal Siakam", 84, "2.03m", "Indiana Pacers", "raro", 22000000, "PF"),
            ("De'Aaron Fox", 86, "1.91m", "Sacramento Kings", "raro", 26000000, "PG"),
            ("Donovan Mitchell", 85, "1.85m", "Cleveland Cavaliers", "raro", 24000000, "SG"),
            ("Jaylen Brown", 86, "1.98m", "Boston Celtics", "raro", 27000000, "SG"),
            ("Zach LaVine", 83, "1.96m", "Chicago Bulls", "raro", 20000000, "SG"),
            ("Karl-Anthony Towns", 84, "2.11m", "Minnesota Timberwolves", "raro", 23000000, "C"),
            ("Bradley Beal", 82, "1.93m", "Phoenix Suns", "raro", 18000000, "SG"),
            
            # Comuns
            ("Marcus Smart", 78, "1.93m", "Memphis Grizzlies", "comum", 12000000, "PG"),
            ("Brook Lopez", 77, "2.13m", "Milwaukee Bucks", "comum", 10000000, "C"),
            ("Duncan Robinson", 75, "2.01m", "Miami Heat", "comum", 8000000, "SF"),
            ("Pat Connaughton", 74, "1.96m", "Milwaukee Bucks", "comum", 7000000, "SG"),
            ("Dorian Finney-Smith", 76, "2.03m", "Brooklyn Nets", "comum", 9000000, "PF"),
            ("Josh Green", 73, "1.96m", "Dallas Mavericks", "comum", 6000000, "SG"),
            ("Onyeka Okongwu", 75, "2.06m", "Atlanta Hawks", "comum", 8500000, "C"),
            ("Jaden McDaniels", 74, "2.06m", "Minnesota Timberwolves", "comum", 6500000, "PF"),
        ]
        
        cursor.executemany('''
            INSERT INTO players (name, overall, height, team, rarity, market_value, position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', players_data)
        
        conn.commit()
        conn.close()
    
    def refresh_shop(self):
        """Atualiza a loja com novos jogadores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Remove itens expirados
        cursor.execute("DELETE FROM shop WHERE expires_at < datetime('now')")
        
        # Adiciona novos itens se a loja estiver vazia
        cursor.execute("SELECT COUNT(*) FROM shop")
        if cursor.fetchone()[0] == 0:
            # Gera 6 jogadores aleatórios para a loja
            for _ in range(6):
                # Seleciona jogador aleatório
                cursor.execute('''
                    SELECT player_id, market_value FROM players 
                    ORDER BY RANDOM() LIMIT 1
                ''')
                result = cursor.fetchone()
                if result:
                    player_id, market_value = result
                    # Preço com variação de ±20%
                    price_variation = random.uniform(0.8, 1.2)
                    price = int(market_value * price_variation)
                    
                    # Expira em 10 minutos
                    expires_at = datetime.now() + timedelta(minutes=10)
                    
                    cursor.execute('''
                        INSERT INTO shop (player_id, price, expires_at)
                        VALUES (?, ?, ?)
                    ''', (player_id, price, expires_at))
        
        conn.commit()
        conn.close()
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Obtém dados de um usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, money, language, created_at, last_daily, last_free_pack
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'money': result[2],
                'language': result[3],
                'created_at': result[4],
                'last_daily': result[5],
                'last_free_pack': result[6]
            }
        return None
    
    async def create_user(self, user_id: int, username: str) -> bool:
        """Cria um novo usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, money)
                VALUES (?, ?, ?)
            ''', (user_id, username, ECONOMY['starting_money']))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    async def get_team(self, user_id: int) -> Optional[Dict]:
        """Obtém o time de um usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT team_id, team_name, team_logo, wins, losses, created_at
            FROM teams WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'team_id': result[0],
                'team_name': result[1],
                'team_logo': result[2],
                'wins': result[3],
                'losses': result[4],
                'created_at': result[5]
            }
        return None
    
    async def create_team(self, user_id: int, team_name: str, team_logo: str = None) -> bool:
        """Cria um novo time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO teams (user_id, team_name, team_logo)
                VALUES (?, ?, ?)
            ''', (user_id, team_name, team_logo))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    async def get_user_players(self, user_id: int) -> List[Dict]:
        """Obtém todos os jogadores de um usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT up.id, p.player_id, p.name, p.overall, p.height, p.team, p.rarity, 
                   p.market_value, p.position, up.is_starter
            FROM user_players up
            JOIN players p ON up.player_id = p.player_id
            WHERE up.user_id = ?
            ORDER BY up.is_starter DESC, p.overall DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        players = []
        for result in results:
            players.append({
                'id': result[0],
                'player_id': result[1],
                'name': result[2],
                'overall': result[3],
                'height': result[4],
                'team': result[5],
                'rarity': result[6],
                'market_value': result[7],
                'position': result[8],
                'is_starter': bool(result[9])
            })
        
        return players
    
    async def add_player_to_user(self, user_id: int, player_id: int) -> bool:
        """Adiciona um jogador ao usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_players (user_id, player_id)
                VALUES (?, ?)
            ''', (user_id, player_id))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    async def get_random_player(self) -> Optional[Dict]:
        """Obtém um jogador aleatório baseado na raridade"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determina raridade baseada nas probabilidades
        rand = random.randint(1, 100)
        if rand <= 3:
            rarity = 'lendário'
        elif rand <= 15:
            rarity = 'épico'
        elif rand <= 40:
            rarity = 'raro'
        else:
            rarity = 'comum'
        
        cursor.execute('''
            SELECT player_id, name, overall, height, team, rarity, market_value, position
            FROM players WHERE rarity = ? ORDER BY RANDOM() LIMIT 1
        ''', (rarity,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'player_id': result[0],
                'name': result[1],
                'overall': result[2],
                'height': result[3],
                'team': result[4],
                'rarity': result[5],
                'market_value': result[6],
                'position': result[7]
            }
        return None
    
    async def update_money(self, user_id: int, amount: int) -> bool:
        """Atualiza o dinheiro de um usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET money = money + ? WHERE user_id = ?
        ''', (amount, user_id))
        
        conn.commit()
        conn.close()
        return True
    
    async def update_player_starter_status(self, user_id: int, player_id: int, is_starter: bool) -> bool:
        """Atualiza o status de titular/reserva de um jogador"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Se está definindo como titular, verifica se já tem 5 titulares
            if is_starter:
                cursor.execute('''
                    SELECT COUNT(*) FROM user_players 
                    WHERE user_id = ? AND is_starter = 1
                ''', (user_id,))
                current_starters = cursor.fetchone()[0]
                
                if current_starters >= 5:
                    conn.close()
                    return False
            
            # Atualiza o status
            cursor.execute('''
                UPDATE user_players 
                SET is_starter = ? 
                WHERE user_id = ? AND player_id = ?
            ''', (is_starter, user_id, player_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar status do jogador: {e}")
            conn.close()
            return False
    
    async def sell_player(self, user_id: int, player_id: int) -> Optional[int]:
        """Vende um jogador e retorna o valor da venda"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Obtém informações do jogador
            cursor.execute('''
                SELECT p.market_value FROM user_players up
                JOIN players p ON up.player_id = p.player_id
                WHERE up.user_id = ? AND up.player_id = ?
            ''', (user_id, player_id))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return None
            
            market_value = result[0]
            sell_value = int(market_value * 0.8)  # 80% do valor de mercado
            
            # Remove o jogador do usuário
            cursor.execute('''
                DELETE FROM user_players 
                WHERE user_id = ? AND player_id = ?
            ''', (user_id, player_id))
            
            # Adiciona o dinheiro da venda
            cursor.execute('''
                UPDATE users SET money = money + ? WHERE user_id = ?
            ''', (sell_value, user_id))
            
            conn.commit()
            conn.close()
            return sell_value
        except Exception as e:
            print(f"Erro ao vender jogador: {e}")
            conn.close()
            return None
    
    async def update_last_free_pack(self, user_id: int) -> bool:
        """Atualiza o timestamp do último pack gratuito"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_free_pack = datetime('now') WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        return True
    
    async def update_last_daily(self, user_id: int) -> bool:
        """Atualiza o timestamp da última recompensa diária"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_daily = datetime('now') WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        return True
    
    async def get_shop_items(self) -> List[Dict]:
        """Obtém itens da loja"""
        # Atualiza a loja primeiro
        self.refresh_shop()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.id, p.player_id, p.name, p.overall, p.height, p.team, p.rarity, 
                   p.market_value, p.position, s.price, s.expires_at
            FROM shop s
            JOIN players p ON s.player_id = p.player_id
            WHERE s.expires_at > datetime('now')
            ORDER BY p.rarity DESC, p.overall DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        items = []
        for result in results:
            items.append({
                'id': result[0],
                'player_id': result[1],
                'name': result[2],
                'overall': result[3],
                'height': result[4],
                'team': result[5],
                'rarity': result[6],
                'market_value': result[7],
                'position': result[8],
                'price': result[9],
                'expires_at': result[10]
            })
        
        return items
    
    async def buy_player(self, user_id: int, shop_item_id: int) -> bool:
        """Compra um jogador da loja"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Obtém informações do item da loja
            cursor.execute('''
                SELECT s.price, s.player_id, u.money
                FROM shop s
                JOIN users u ON u.user_id = ?
                WHERE s.id = ? AND s.expires_at > datetime('now')
            ''', (user_id, shop_item_id))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False
            
            price, player_id, user_money = result
            
            if user_money < price:
                conn.close()
                return False
            
            # Remove dinheiro do usuário
            cursor.execute('''
                UPDATE users SET money = money - ? WHERE user_id = ?
            ''', (price, user_id))
            
            # Adiciona jogador ao usuário
            cursor.execute('''
                INSERT INTO user_players (user_id, player_id)
                VALUES (?, ?)
            ''', (user_id, player_id))
            
            # Remove item da loja
            cursor.execute('DELETE FROM shop WHERE id = ?', (shop_item_id,))
            
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False
    
    async def update_match_result(self, match_id: int, winner_id: int, 
                                challenger_score: int, challenged_score: int) -> bool:
        """Atualiza resultado de uma partida"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Obtém informações da partida
            cursor.execute('''
                SELECT challenger_id, challenged_id FROM matches WHERE match_id = ?
            ''', (match_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False
            
            challenger_id, challenged_id = result
            
            # Atualiza resultado da partida
            cursor.execute('''
                UPDATE matches 
                SET status = 'completed', winner_id = ?, challenger_score = ?, 
                    challenged_score = ?, ended_at = datetime('now')
                WHERE match_id = ?
            ''', (winner_id, challenger_score, challenged_score, match_id))
            
            # Atualiza estatísticas dos times
            if winner_id == challenger_id:
                # Desafiador venceu
                cursor.execute('''
                    UPDATE teams SET wins = wins + 1 WHERE user_id = ?
                ''', (challenger_id,))
                cursor.execute('''
                    UPDATE teams SET losses = losses + 1 WHERE user_id = ?
                ''', (challenged_id,))
                
                # Adiciona dinheiro ao vencedor
                cursor.execute('''
                    UPDATE users SET money = money + ? WHERE user_id = ?
                ''', (ECONOMY['match_win_reward'], challenger_id))
                
                # Remove dinheiro do perdedor
                cursor.execute('''
                    UPDATE users SET money = money - ? WHERE user_id = ?
                ''', (ECONOMY['match_loss_penalty'], challenged_id))
            else:
                # Desafiado venceu
                cursor.execute('''
                    UPDATE teams SET wins = wins + 1 WHERE user_id = ?
                ''', (challenged_id,))
                cursor.execute('''
                    UPDATE teams SET losses = losses + 1 WHERE user_id = ?
                ''', (challenger_id,))
                
                # Adiciona dinheiro ao vencedor
                cursor.execute('''
                    UPDATE users SET money = money + ? WHERE user_id = ?
                ''', (ECONOMY['match_win_reward'], challenged_id))
                
                # Remove dinheiro do perdedor
                cursor.execute('''
                    UPDATE users SET money = money - ? WHERE user_id = ?
                ''', (ECONOMY['match_loss_penalty'], challenger_id))
            
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False
    
    async def get_rankings(self) -> Dict:
        """Obtém rankings do servidor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ranking por overall
        cursor.execute('''
            SELECT t.team_name, u.username, 
                   (SELECT AVG(p.overall) FROM user_players up 
                    JOIN players p ON up.player_id = p.player_id 
                    WHERE up.user_id = u.user_id AND up.is_starter = 1) as avg_overall
            FROM teams t
            JOIN users u ON t.user_id = u.user_id
            WHERE (SELECT COUNT(*) FROM user_players up WHERE up.user_id = u.user_id AND up.is_starter = 1) >= 5
            ORDER BY avg_overall DESC
            LIMIT 10
        ''')
        
        overall_ranking = []
        for result in cursor.fetchall():
            if result[2]:  # Se tem overall calculado
                overall_ranking.append({
                    'team_name': result[0],
                    'username': result[1],
                    'value': round(result[2], 1)
                })
        
        # Ranking por dinheiro
        cursor.execute('''
            SELECT t.team_name, u.username, u.money
            FROM teams t
            JOIN users u ON t.user_id = u.user_id
            ORDER BY u.money DESC
            LIMIT 10
        ''')
        
        money_ranking = []
        for result in cursor.fetchall():
            money_ranking.append({
                'team_name': result[0],
                'username': result[1],
                'value': result[2]
            })
        
        # Ranking por vitórias
        cursor.execute('''
            SELECT t.team_name, u.username, t.wins
            FROM teams t
            JOIN users u ON t.user_id = u.user_id
            ORDER BY t.wins DESC
            LIMIT 10
        ''')
        
        wins_ranking = []
        for result in cursor.fetchall():
            wins_ranking.append({
                'team_name': result[0],
                'username': result[1],
                'value': result[2]
            })
        
        conn.close()
        
        return {
            'overall': overall_ranking,
            'money': money_ranking,
            'wins': wins_ranking
        }
