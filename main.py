import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime
from database import Database
from utils import EmbedBuilder, ButtonBuilder, GameLogic
from config import BOT_TOKEN, COLORS, EMOJIS, ECONOMY

class HoopCoreBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            application_id=None  # Será definido automaticamente
        )
        self.db = Database()
        self.start_time = datetime.now()
    
    async def setup_hook(self):
        """Configuração inicial do bot"""
        print("🔄 Carregando cogs...")
        
        # Carrega todos os cogs
        await self.load_extension("cogs.teams")
        await self.load_extension("cogs.shop")
        await self.load_extension("cogs.matches")
        await self.load_extension("cogs.general")
        
        print("✅ Cogs carregados com sucesso!")
        
        # Sincroniza comandos slash
        print("🔄 Sincronizando comandos slash...")
        await self.tree.sync()
        print("✅ Comandos sincronizados!")
    
    async def on_ready(self):
        """Evento executado quando o bot fica online"""
        print("=" * 50)
        print(f"🏀 HoopCore está online!")
        print(f"👤 Logado como: {self.user.name}#{self.user.discriminator}")
        print(f"🆔 ID do Bot: {self.user.id}")
        print(f"📊 Servidores: {len(self.guilds)}")
        print(f"👥 Usuários: {sum(guild.member_count for guild in self.guilds):,}")
        print(f"⏰ Iniciado em: {self.start_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 50)
        
        # Atualiza status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="🏀 NBA 2025 | /ajuda"
            ),
            status=discord.Status.online
        )
    
    async def on_guild_join(self, guild):
        """Evento executado quando o bot entra em um servidor"""
        print(f"🎉 Entrei no servidor: {guild.name} ({guild.id})")
        
        # Envia mensagem de boas-vindas
        try:
            system_channel = guild.system_channel or guild.text_channels[0]
            embed = discord.Embed(
                title="🏀 HoopCore - Bem-vindo!",
                description="Obrigado por me adicionar ao seu servidor!\n\n"
                           "**HoopCore** é um RPG de basquete da NBA 2025 onde você pode:\n"
                           "• Criar e gerenciar seu próprio time\n"
                           "• Colecionar jogadores reais da NBA\n"
                           "• Competir contra outros jogadores\n"
                           "• Construir a melhor equipe possível\n\n"
                           "**Use `/ajuda` para ver todos os comandos!**",
                color=0x1e90ff
            )
            embed.add_field(
                name="🚀 Começando",
                value="1. Use `/criartime` para criar seu time\n"
                      "2. Use `/pack` para obter jogadores gratuitos\n"
                      "3. Use `/loja` para comprar jogadores\n"
                      "4. Use `/desafiar` para competir",
                inline=False
            )
            embed.set_footer(text="HoopCore - RPG de Basquete da NBA 2025")
            
            await system_channel.send(embed=embed)
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem de boas-vindas: {e}")
    
    async def on_guild_remove(self, guild):
        """Evento executado quando o bot sai de um servidor"""
        print(f"👋 Saí do servidor: {guild.name} ({guild.id})")
    
    async def on_command_error(self, ctx, error):
        """Tratamento de erros de comandos"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignora comandos não encontrados
        
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você não tem permissão para usar este comando.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão do Bot Insuficiente",
                description="Eu não tenho as permissões necessárias para executar este comando.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        # Log do erro
        print(f"❌ Erro no comando {ctx.command}: {error}")
        
        # Mensagem genérica de erro
        embed = discord.Embed(
            title="❌ Erro",
            description="Ocorreu um erro ao executar o comando. Tente novamente.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
    
    async def on_interaction(self, interaction):
        """Evento executado quando há uma interação"""
        if interaction.type == discord.InteractionType.component:
            # Trata interações de botões
            await self.handle_button_interaction(interaction)
    
    async def handle_button_interaction(self, interaction):
        """Trata interações de botões"""
        custom_id = interaction.data.get("custom_id", "")
        
        try:
            if custom_id.startswith("accept_challenge_"):
                # Aceitar desafio
                challenger_id = int(custom_id.split("_")[-1])
                await self.accept_challenge(interaction, challenger_id)
            
            elif custom_id.startswith("decline_challenge_"):
                # Recusar desafio
                challenger_id = int(custom_id.split("_")[-1])
                await self.decline_challenge(interaction, challenger_id)
            
            elif custom_id == "refresh_shop":
                # Atualizar loja
                await self.refresh_shop(interaction)
            
            elif custom_id == "buy_pack":
                # Comprar pack
                await self.buy_pack(interaction)
            
            elif custom_id.startswith("ranking_"):
                # Mudar ranking
                category = custom_id.split("_")[-1]
                await self.change_ranking(interaction, category)
            
            elif custom_id.startswith("sell_confirm_"):
                # Confirmar venda
                player_id = int(custom_id.split("_")[-1])
                await self.confirm_sell(interaction, player_id)
            
            elif custom_id == "sell_cancel":
                # Cancelar venda
                await self.cancel_sell(interaction)
            
            else:
                # Botão não reconhecido
                await interaction.response.send_message(
                    "❌ Botão não reconhecido.", 
                    ephemeral=True
                )
                
        except Exception as e:
            print(f"❌ Erro ao processar interação de botão: {e}")
            await interaction.response.send_message(
                "❌ Erro ao processar interação. Tente novamente.", 
                ephemeral=True
            )
    
    async def accept_challenge(self, interaction, challenger_id):
        """Aceita um desafio"""
        try:
            embed = discord.Embed(
                title="✅ Desafio Aceito!",
                description="A partida será iniciada em breve...",
                color=0x00ff00
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            print(f"Erro ao aceitar desafio: {e}")
            await interaction.response.send_message("❌ Erro ao aceitar desafio.", ephemeral=True)
    
    async def decline_challenge(self, interaction, challenger_id):
        """Recusa um desafio"""
        try:
            embed = discord.Embed(
                title="❌ Desafio Recusado",
                description="O desafio foi recusado.",
                color=0xff0000
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            print(f"Erro ao recusar desafio: {e}")
            await interaction.response.send_message("❌ Erro ao recusar desafio.", ephemeral=True)
    
    async def refresh_shop(self, interaction):
        """Atualiza a loja"""
        try:
            # Atualiza a loja no banco de dados
            self.db.refresh_shop()
            
            embed = discord.Embed(
                title="🔄 Loja Atualizada",
                description="A loja foi atualizada! Use `/loja` para ver os novos itens.",
                color=0x1e90ff
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Erro ao atualizar loja: {e}")
            await interaction.response.send_message("❌ Erro ao atualizar loja.", ephemeral=True)
    
    async def buy_pack(self, interaction):
        """Compra um pack"""
        try:
            embed = discord.Embed(
                title="🛒 Comprar Pack",
                description="Use `/packpremium` para comprar um pack premium!\n\n"
                           "**Pack Premium:** $5,000\n"
                           "**Conteúdo:** 3 jogadores com chances melhoradas de raridade",
                color=0x8a2be2
            )
            embed.add_field(
                name="💡 Alternativa Gratuita",
                value="Use `/pack` para abrir um pack gratuito a cada 25 minutos!",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Erro ao mostrar pack: {e}")
            await interaction.response.send_message("❌ Erro ao mostrar informações do pack.", ephemeral=True)
    
    async def change_ranking(self, interaction, category):
        """Muda o tipo de ranking"""
        try:
            category_names = {
                'overall': 'Times Mais Fortes',
                'money': 'Times Mais Ricos',
                'wins': 'Mais Vitórias'
            }
            
            embed = discord.Embed(
                title=f"📊 {category_names.get(category, 'Ranking')}",
                description=f"Use `/ranking {category}` para ver este ranking.",
                color=0xffd700
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Erro ao mostrar ranking: {e}")
            await interaction.response.send_message("❌ Erro ao mostrar ranking.", ephemeral=True)
    
    async def confirm_sell(self, interaction, player_id):
        """Confirma a venda de um jogador"""
        try:
            embed = discord.Embed(
                title="💰 Venda Confirmada",
                description="Jogador vendido com sucesso!",
                color=0x00ff00
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            print(f"Erro ao confirmar venda: {e}")
            await interaction.response.send_message("❌ Erro ao confirmar venda.", ephemeral=True)
    
    async def cancel_sell(self, interaction):
        """Cancela a venda de um jogador"""
        try:
            embed = discord.Embed(
                title="❌ Venda Cancelada",
                description="A venda foi cancelada.",
                color=0xff0000
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            print(f"Erro ao cancelar venda: {e}")
            await interaction.response.send_message("❌ Erro ao cancelar venda.", ephemeral=True)

async def main():
    """Função principal"""
    print("🏀 Iniciando HoopCore...")
    
    # Verifica se o token está configurado
    if BOT_TOKEN == "SEU_TOKEN_AQUI":
        print("❌ ERRO: Configure o token do bot no arquivo config.py!")
        return
    
    # Cria e executa o bot
    bot = HoopCoreBot()
    
    try:
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        print("\n🛑 Bot interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar o bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    # Executa o bot
    asyncio.run(main())
