import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio
from datetime import datetime
from database import Database
from utils import EmbedBuilder, LanguageManager
from config import COLORS, EMOJIS, LANGUAGES

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    @app_commands.command(name="ajuda", description="Mostra todos os comandos disponíveis")
    async def help_command(self, interaction: discord.Interaction):
        """Mostra todos os comandos disponíveis"""
        await interaction.response.defer()
        
        embed = EmbedBuilder.create_embed(
            f"{EMOJIS['basketball']} HoopCore - Comandos",
            "Lista completa de todos os comandos disponíveis",
            COLORS['primary']
        )
        
        # Comandos de Time
        embed.add_field(
            name="🏀 Comandos de Time",
            value="• `/criartime` - Cria um novo time\n"
                  "• `/time` - Mostra informações do seu time\n"
                  "• `/jogadores` - Lista todos os seus jogadores\n"
                  "• `/titular` - Define jogador como titular\n"
                  "• `/reserva` - Define jogador como reserva\n"
                  "• `/vender` - Vende um jogador",
            inline=False
        )
        
        # Comandos de Loja
        embed.add_field(
            name="🛒 Comandos de Loja",
            value="• `/loja` - Mostra a loja de jogadores\n"
                  "• `/comprar` - Compra um jogador da loja\n"
                  "• `/pack` - Abre pack gratuito (25min cooldown)\n"
                  "• `/packpremium` - Compra pack premium ($5,000)\n"
                  "• `/diario` - Coleta recompensa diária\n"
                  "• `/dinheiro` - Mostra seu dinheiro",
            inline=False
        )
        
        # Comandos de Partida
        embed.add_field(
            name="🎮 Comandos de Partida",
            value="• `/desafiar` - Desafia outro jogador\n"
                  "• `/partida` - Inicia partida simulada\n"
                  "• `/ranking` - Mostra rankings\n"
                  "• `/estatisticas` - Suas estatísticas\n"
                  "• `/historico` - Histórico de partidas",
            inline=False
        )
        
        # Comandos Gerais
        embed.add_field(
            name="⚙️ Comandos Gerais",
            value="• `/ajuda` - Mostra esta lista\n"
                  "• `/status` - Status do bot\n"
                  "• `/idioma` - Troca idioma do bot",
            inline=False
        )
        
        embed.add_field(
            name="💡 Dicas",
            value="• Crie um time primeiro com `/criartime`\n"
                  "• Use `/pack` para obter jogadores gratuitos\n"
                  "• Complete seu time com 5 titulares\n"
                  "• Desafie outros jogadores para ganhar dinheiro",
            inline=False
        )
        
        embed.set_footer(text="HoopCore - RPG de Basquete da NBA 2025")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="status", description="Mostra status do bot")
    async def bot_status(self, interaction: discord.Interaction):
        """Mostra status do bot"""
        await interaction.response.defer()
        
        # Calcula uptime
        uptime = datetime.now() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
        
        # Obtém estatísticas
        total_guilds = len(self.bot.guilds)
        total_users = sum(guild.member_count for guild in self.bot.guilds)
        
        embed = EmbedBuilder.create_embed(
            f"{EMOJIS['basketball']} Status do HoopCore",
            "Informações sobre o bot e sua performance",
            COLORS['info']
        )
        
        embed.add_field(
            name="📊 Estatísticas",
            value=f"**Servidores:** {total_guilds}\n"
                  f"**Usuários:** {total_users:,}\n"
                  f"**Latência:** {round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        if uptime:
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        else:
            uptime_str = "Desconhecido"
        
        embed.add_field(
            name="⏰ Uptime",
            value=f"**Tempo Online:** {uptime_str}\n"
                  f"**Versão:** 1.0.0\n"
                  f"**Discord.py:** {discord.__version__}",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Funcionalidades",
            value="• ✅ Sistema de Times\n"
                  "• ✅ Loja de Jogadores\n"
                  "• ✅ Sistema de Partidas\n"
                  "• ✅ Rankings\n"
                  "• ✅ Sistema Econômico\n"
                  "• ✅ Packs de Jogadores",
            inline=False
        )
        
        embed.set_footer(text="HoopCore - Desenvolvido com ❤️")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="idioma", description="Troca o idioma do bot")
    @app_commands.describe(
        idioma="Idioma desejado"
    )
    @app_commands.choices(idioma=[
        app_commands.Choice(name="Português", value="pt"),
        app_commands.Choice(name="English", value="en"),
        app_commands.Choice(name="Español", value="es")
    ])
    async def change_language(self, interaction: discord.Interaction, idioma: str):
        """Troca o idioma do bot"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Verifica se usuário existe
        user = await self.db.get_user(user_id)
        if not user:
            # Cria usuário se não existir
            await self.db.create_user(user_id, interaction.user.display_name)
        
        # Atualiza idioma (implementar no database)
        # Por enquanto, apenas confirma
        
        language_name = LANGUAGES.get(idioma, "Português")
        
        embed = EmbedBuilder.create_embed(
            "🌍 Idioma Alterado",
            f"O idioma do bot foi alterado para **{language_name}**!",
            COLORS['success']
        )
        
        embed.add_field(
            name="ℹ️ Informação",
            value="Algumas mensagens podem continuar em português por enquanto.\n"
                  "A tradução completa será implementada em breve!",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="info", description="Informações sobre o bot")
    async def bot_info(self, interaction: discord.Interaction):
        """Mostra informações sobre o bot"""
        await interaction.response.defer()
        
        embed = EmbedBuilder.create_embed(
            f"{EMOJIS['basketball']} Sobre o HoopCore",
            "Um RPG de basquete inspirado na NBA 2025",
            COLORS['purple']
        )
        
        embed.add_field(
            name="🎯 Sobre",
            value="HoopCore é um bot de RPG de basquete que permite você:\n"
                  "• Criar e gerenciar seu próprio time\n"
                  "• Colecionar jogadores reais da NBA 2025\n"
                  "• Competir contra outros jogadores\n"
                  "• Construir a melhor equipe possível",
            inline=False
        )
        
        embed.add_field(
            name="🏀 Jogadores",
            value="• **Lendários:** LeBron James, Stephen Curry, Giannis, etc.\n"
                  "• **Épicos:** Ja Morant, Zion Williamson, Anthony Edwards\n"
                  "• **Raros:** Bam Adebayo, De'Aaron Fox, Donovan Mitchell\n"
                  "• **Comuns:** Jogadores de role player",
            inline=False
        )
        
        embed.add_field(
            name="💰 Economia",
            value="• **Recompensa Diária:** $1,000\n"
                  "• **Vitória em Partida:** +$500\n"
                  "• **Derrota em Partida:** -$200\n"
                  "• **Pack Premium:** $5,000 (3 jogadores)",
            inline=False
        )
        
        embed.add_field(
            name="📈 Progressão",
            value="• Colete jogadores através de packs\n"
                  "• Monte o melhor time possível\n"
                  "• Compita contra outros jogadores\n"
                  "• Suba nos rankings globais",
            inline=False
        )
        
        embed.set_footer(text="Desenvolvido com discord.py | NBA 2025")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="creditos", description="Mostra os créditos do bot")
    async def credits(self, interaction: discord.Interaction):
        """Mostra os créditos do bot"""
        await interaction.response.defer()
        
        embed = EmbedBuilder.create_embed(
            f"{EMOJIS['star']} Créditos",
            "Pessoas e recursos que tornaram este bot possível",
            COLORS['gold']
        )
        
        embed.add_field(
            name="👨‍💻 Desenvolvimento",
            value="• **Desenvolvedor:** IA Assistant\n"
                  "• **Framework:** discord.py 2.3.0+\n"
                  "• **Banco de Dados:** SQLite\n"
                  "• **Inspiração:** DreamTeam (Futebol)",
            inline=False
        )
        
        embed.add_field(
            name="🏀 NBA 2025",
            value="• **Jogadores:** Baseados na temporada 2025\n"
                  "• **Times:** Todos os 30 times da NBA\n"
                  "• **Overall:** Baseado em estatísticas reais\n"
                  "• **Raridades:** Sistema balanceado",
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Tecnologias",
            value="• **Python 3.8+**\n"
                  "• **discord.py**\n"
                  "• **SQLite**\n"
                  "• **asyncio**",
            inline=False
        )
        
        embed.add_field(
            name="🙏 Agradecimentos",
            value="• Comunidade Discord\n"
                  "• Desenvolvedores do discord.py\n"
                  "• Fãs de basquete da NBA\n"
                  "• Todos os usuários do bot",
            inline=False
        )
        
        embed.set_footer(text="Obrigado por usar o HoopCore! 🏀")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="ping", description="Testa a latência do bot")
    async def ping(self, interaction: discord.Interaction):
        """Testa a latência do bot"""
        await interaction.response.defer()
        
        latency = round(self.bot.latency * 1000)
        
        # Determina cor baseada na latência
        if latency < 100:
            color = COLORS['success']
            status = "Excelente"
        elif latency < 200:
            color = COLORS['warning']
            status = "Boa"
        else:
            color = COLORS['error']
            status = "Lenta"
        
        embed = EmbedBuilder.create_embed(
            "🏓 Pong!",
            f"Latência do bot: **{latency}ms**\nStatus: **{status}**",
            color
        )
        
        embed.add_field(
            name="📊 Informações",
            value=f"• **Latência:** {latency}ms\n"
                  f"• **Status:** {status}\n"
                  f"• **API:** Discord",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GeneralCog(bot))
