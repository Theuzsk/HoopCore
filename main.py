import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime
from database import Database
from utils import EmbedBuilder, ButtonBuilder, GameLogic
from config import BOT_TOKEN, COLORS, EMOJIS, ECONOMY
import random

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
                title="🏀 Bem-vindo ao HoopCore!",
                description="**HoopCore** é um jogo de basquete da NBA 2025 onde você pode:\n"
                           "• Criar e gerenciar seu próprio time\n"
                           "• Colecionar jogadores da NBA\n"
                           "• Competir em partidas emocionantes\n"
                           "• Construir o melhor time da liga!",
                color=0x1e90ff
            )
            embed.add_field(
                name="🚀 Como Começar",
                value="1. Use `/criartime` para criar seu time\n"
                      "2. Use `/pack` para ganhar jogadores\n"
                      "3. Use `/loja` para comprar jogadores\n"
                      "4. Use `/desafiar` para competir",
                inline=False
            )
            embed.set_footer(text="HoopCore - Jogo de Basquete da NBA 2025 | Criado por Theus.zk")
            
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
        """Lida com todas as interações"""
        if interaction.type == discord.InteractionType.component:
            if interaction.data.get("component_type") == 2:  # Button
                await self.handle_button_interaction(interaction)
            elif interaction.data.get("component_type") == 3:  # Select Menu
                await self.handle_select_interaction(interaction)
    
    async def handle_select_interaction(self, interaction):
        """Lida com interações de select menu"""
        custom_id = interaction.data.get("custom_id", "")
        
        try:
            if custom_id == "select_starter":
                # Selecionar jogador para titular
                await self.handle_starter_selection(interaction)
            
            elif custom_id == "select_bench":
                # Selecionar jogador para reserva
                await self.handle_bench_selection(interaction)
            
            elif custom_id == "select_sell":
                # Selecionar jogador para venda
                await self.handle_sell_selection(interaction)
            
            else:
                # Select menu não reconhecido
                await interaction.response.send_message(
                    "❌ Select menu não reconhecido.", 
                    ephemeral=True
                )
                
        except Exception as e:
            print(f"❌ Erro ao processar interação de select menu: {e}")
            await interaction.response.send_message(
                "❌ Erro ao processar interação. Tente novamente.",
                ephemeral=True
            )
    
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
            
            elif custom_id == "view_players":
                # Ver jogadores
                await self.view_players(interaction)
            
            elif custom_id == "manage_team":
                # Gerenciar time
                await self.manage_team(interaction)
            
            elif custom_id.startswith("sell_player_"):
                # Selecionar jogador para venda
                player_id = int(custom_id.split("_")[-1])
                await self.select_player_for_sale(interaction, player_id)
            
            # Botões administrativos
            elif custom_id == "admin_add_money":
                await self.admin_add_money(interaction)
            
            elif custom_id == "admin_add_player":
                await self.admin_add_player(interaction)
            
            elif custom_id == "admin_reset_cooldowns":
                await self.admin_reset_cooldowns(interaction)
            
            elif custom_id == "admin_server_stats":
                await self.admin_server_stats(interaction)
            
            # Botões de posição
            elif custom_id.startswith("position_"):
                position = custom_id.split("_")[1]
                await self.handle_position_selection(interaction, position)
            
            # Botões de partida
            elif custom_id == "start_match":
                await self.start_match_game(interaction)
            
            elif custom_id.startswith("match_"):
                await self.handle_match_action(interaction, custom_id)
            
            elif custom_id.startswith("continue_match_"):
                await self.continue_match(interaction, custom_id)
            
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
            # Obtém o ranking solicitado
            rankings = await self.db.get_rankings()
            
            if not rankings or not rankings.get(category) or len(rankings[category]) == 0:
                if category == "overall":
                    message = "Nenhum time com 5 titulares ainda para calcular overall."
                elif category == "money":
                    message = "Nenhum time criado ainda."
                else:
                    message = "Nenhuma partida jogada ainda."
                
                embed = discord.Embed(
                    title="📊 Ranking",
                    description=message,
                    color=0x808080
                )
            else:
                # Cria embed do ranking
                from utils import EmbedBuilder
                embed = EmbedBuilder.ranking_embed(rankings, category)
            
            await interaction.response.edit_message(embed=embed)
            
        except Exception as e:
            print(f"Erro ao mostrar ranking: {e}")
            await interaction.response.send_message("❌ Erro ao mostrar ranking.", ephemeral=True)
    
    async def confirm_sell(self, interaction, player_id):
        """Confirma a venda de um jogador"""
        try:
            user_id = interaction.user.id
            
            # Vende o jogador
            sell_value = await self.db.sell_player(user_id, player_id)
            
            if sell_value is not None:
                embed = discord.Embed(
                    title="💰 Venda Confirmada",
                    description=f"Jogador vendido com sucesso por **${sell_value:,}**!",
                    color=0x00ff00
                )
                embed.add_field(
                    name="💡 Dica",
                    value="Use o dinheiro para comprar novos jogadores na loja!",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Erro na Venda",
                    description="Erro ao vender o jogador. Tente novamente.",
                    color=0xff0000
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
    
    async def view_players(self, interaction):
        """Mostra jogadores do time"""
        try:
            embed = discord.Embed(
                title="👥 Seus Jogadores",
                description="Use `/jogadores` para ver uma lista completa dos seus jogadores.",
                color=0x1e90ff
            )
            embed.add_field(
                name="💡 Comandos Úteis",
                value="• `/titular [nome]` - Define jogador como titular\n"
                      "• `/reserva [nome]` - Define jogador como reserva\n"
                      "• `/vender` - Vende um jogador",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Erro ao mostrar jogadores: {e}")
            await interaction.response.send_message("❌ Erro ao mostrar jogadores.", ephemeral=True)
    
    async def manage_team(self, interaction):
        """Gerenciar time"""
        try:
            embed = discord.Embed(
                title="⚙️ Gerenciar Time",
                description="Comandos para gerenciar seu time:",
                color=0x8a2be2
            )
            embed.add_field(
                name="🏀 Jogadores",
                value="• `/jogadores` - Ver todos os jogadores\n"
                      "• `/titular [nome]` - Definir titular\n"
                      "• `/reserva [nome]` - Definir reserva\n"
                      "• `/vender` - Vender jogador",
                inline=False
            )
            embed.add_field(
                name="📊 Time",
                value="• `/time` - Informações do time\n"
                      "• `/estatisticas` - Suas estatísticas",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Erro ao mostrar gerenciamento: {e}")
            await interaction.response.send_message("❌ Erro ao mostrar gerenciamento.", ephemeral=True)
    
    async def select_player_for_sale(self, interaction, player_id):
        """Seleciona jogador para venda"""
        try:
            # Obtém informações do jogador
            user_id = interaction.user.id
            
            # Busca jogador no banco
            players = await self.db.get_user_players(user_id)
            target_player = None
            
            for player in players:
                if player['id'] == player_id:
                    target_player = player
                    break
            
            if not target_player:
                await interaction.response.send_message("❌ Jogador não encontrado.", ephemeral=True)
                return
            
            # Calcula valor de venda
            sell_value = int(target_player['market_value'] * 0.8)
            
            # Confirma venda
            embed = discord.Embed(
                title="💰 Confirmar Venda",
                description=f"Você está vendendo **{target_player['name']}** por **${sell_value:,}**\n\n"
                           f"Overall: {target_player['overall']} | Time: {target_player['team']}\n"
                           f"Raridade: {target_player['rarity']} | Posição: {target_player['position']}",
                color=0xffa500
            )
            
            # Adiciona botões de confirmação
            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.green,
                label="Confirmar Venda",
                emoji="💰",
                custom_id=f"sell_confirm_{player_id}"
            ))
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.red,
                label="Cancelar",
                emoji="❌",
                custom_id="sell_cancel"
            ))
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            print(f"Erro ao selecionar jogador para venda: {e}")
            await interaction.response.send_message("❌ Erro ao selecionar jogador.", ephemeral=True)
    
    # Métodos Administrativos
    async def admin_add_money(self, interaction):
        """Adiciona dinheiro para um usuário"""
        try:
            # Verifica se é o dono - SUBSTITUA PELO SEU ID REAL
            OWNER_ID = 960343374727114752  # ✅ ID do Theus.zk
            
            if interaction.user.id != OWNER_ID:
                await interaction.response.send_message("❌ Acesso negado.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="💰 Adicionar Dinheiro",
                description="Digite o ID do usuário e o valor a adicionar:\n\n"
                           "Formato: `ID VALOR`\n"
                           "Exemplo: `123456789 10000`",
                color=0x00ff00
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"Erro no comando admin: {e}")
            await interaction.response.send_message("❌ Erro no comando.", ephemeral=True)
    
    async def admin_add_player(self, interaction):
        """Adiciona jogador para um usuário"""
        try:
            # Verifica se é o dono - SUBSTITUA PELO SEU ID REAL
            OWNER_ID = 960343374727114752  # ✅ ID do Theus.zk
            
            if interaction.user.id != OWNER_ID:
                await interaction.response.send_message("❌ Acesso negado.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🏀 Adicionar Jogador",
                description="Digite o ID do usuário e o ID do jogador:\n\n"
                           "Formato: `ID_USUARIO ID_JOGADOR`\n"
                           "Exemplo: `123456789 1`",
                color=0x00ff00
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"Erro no comando admin: {e}")
            await interaction.response.send_message("❌ Erro no comando.", ephemeral=True)
    
    async def admin_reset_cooldowns(self, interaction):
        """Reseta cooldowns de um usuário"""
        try:
            # Verifica se é o dono - SUBSTITUA PELO SEU ID REAL
            OWNER_ID = 960343374727114752  # ✅ ID do Theus.zk
            
            if interaction.user.id != OWNER_ID:
                await interaction.response.send_message("❌ Acesso negado.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="⏰ Resetar Cooldowns",
                description="Digite o ID do usuário para resetar cooldowns:\n\n"
                           "Formato: `ID`\n"
                           "Exemplo: `123456789`",
                color=0x00ff00
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"Erro no comando admin: {e}")
            await interaction.response.send_message("❌ Erro no comando.", ephemeral=True)
    
    async def admin_server_stats(self, interaction):
        """Mostra estatísticas do servidor"""
        try:
            # Verifica se é o dono - SUBSTITUA PELO SEU ID REAL
            OWNER_ID = 960343374727114752  # ✅ ID do Theus.zk
            
            if interaction.user.id != OWNER_ID:
                await interaction.response.send_message("❌ Acesso negado.", ephemeral=True)
                return
            
            # Obtém estatísticas do servidor
            total_users = len(self.db.get_all_users())
            total_teams = len(self.db.get_all_teams())
            
            embed = discord.Embed(
                title="📊 Estatísticas do Servidor",
                color=0x00ff00
            )
            embed.add_field(name="👥 Total de Usuários", value=str(total_users), inline=True)
            embed.add_field(name="🏀 Total de Times", value=str(total_teams), inline=True)
            embed.add_field(name="🤖 Servidores", value=str(len(self.guilds)), inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"Erro no comando admin: {e}")
            await interaction.response.send_message("❌ Erro no comando.", ephemeral=True)
    
    async def handle_position_selection(self, interaction, position):
        """Lida com seleção de posição"""
        try:
            # Obtém o valor selecionado
            selected_value = interaction.data.get("values", [None])[0]
            if not selected_value:
                await interaction.response.send_message("❌ Nenhum jogador selecionado.", ephemeral=True)
                return
            
            # Formato: POS_ID (ex: PG_123)
            parts = selected_value.split("_")
            if len(parts) != 2:
                await interaction.response.send_message("❌ Formato inválido.", ephemeral=True)
                return
            
            pos, player_id = parts[0], int(parts[1])
            user_id = interaction.user.id
            
            # Busca jogador no banco
            players = await self.db.get_user_players(user_id)
            target_player = None
            
            for player in players:
                if player['id'] == player_id:
                    target_player = player
                    break
            
            if not target_player:
                await interaction.response.send_message("❌ Jogador não encontrado.", ephemeral=True)
                return
            
            # Verifica se a posição é recomendada
            is_recommended = target_player['position'] == pos
            recommendation_text = "⭐ Posição recomendada!" if is_recommended else "⚠️ Posição não recomendada"
            
            # Confirma posição
            embed = discord.Embed(
                title=f"🏀 Posição Definida: {pos}",
                description=f"**{target_player['name']}** será o {pos} do seu time!\n\n"
                           f"Overall: {target_player['overall']} | Time: {target_player['team']}\n"
                           f"Posição Natural: {target_player['position']}\n\n"
                           f"{recommendation_text}",
                color=0x00ff00 if is_recommended else 0xffa500
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            print(f"Erro ao definir posição: {e}")
            await interaction.response.send_message("❌ Erro ao definir posição.", ephemeral=True)
    
    # Métodos de Seleção de Jogadores
    async def handle_starter_selection(self, interaction):
        """Lida com seleção de jogador para titular"""
        try:
            # Obtém o valor selecionado
            selected_value = interaction.data.get("values", [None])[0]
            if not selected_value:
                await interaction.response.send_message("❌ Nenhum jogador selecionado.", ephemeral=True)
                return
            
            player_id = int(selected_value)
            user_id = interaction.user.id
            
            # Busca jogador no banco
            players = await self.db.get_user_players(user_id)
            target_player = None
            
            for player in players:
                if player['id'] == player_id:
                    target_player = player
                    break
            
            if not target_player:
                await interaction.response.send_message("❌ Jogador não encontrado.", ephemeral=True)
                return
            
            # Verifica se já é titular
            if target_player['is_starter']:
                embed = discord.Embed(
                    title="ℹ️ Já é Titular",
                    description=f"{target_player['name']} já é titular do seu time.",
                    color=0x808080
                )
                await interaction.response.edit_message(embed=embed, view=None)
                return
            
            # Define como titular
            success = await self.db.update_player_starter_status(user_id, target_player['player_id'], True)
            
            if success:
                embed = discord.Embed(
                    title="✅ Titular Definido",
                    description=f"{target_player['name']} agora é titular do seu time!",
                    color=0x00ff00
                )
                embed.add_field(
                    name="💡 Dica",
                    value="Use `/reserva` para remover jogadores do time titular.",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Você já tem 5 titulares. Remova um titular primeiro com `/reserva`.",
                    color=0xff0000
                )
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            print(f"Erro ao definir titular: {e}")
            await interaction.response.send_message("❌ Erro ao definir titular.", ephemeral=True)
    
    async def handle_bench_selection(self, interaction):
        """Lida com seleção de jogador para reserva"""
        try:
            # Obtém o valor selecionado
            selected_value = interaction.data.get("values", [None])[0]
            if not selected_value:
                await interaction.response.send_message("❌ Nenhum jogador selecionado.", ephemeral=True)
                return
            
            player_id = int(selected_value)
            user_id = interaction.user.id
            
            # Busca jogador no banco
            players = await self.db.get_user_players(user_id)
            target_player = None
            
            for player in players:
                if player['id'] == player_id:
                    target_player = player
                    break
            
            if not target_player:
                await interaction.response.send_message("❌ Jogador não encontrado.", ephemeral=True)
                return
            
            # Verifica se já é reserva
            if not target_player['is_starter']:
                embed = discord.Embed(
                    title="ℹ️ Já é Reserva",
                    description=f"{target_player['name']} já é reserva do seu time.",
                    color=0x808080
                )
                await interaction.response.edit_message(embed=embed, view=None)
                return
            
            # Define como reserva
            success = await self.db.update_player_starter_status(user_id, target_player['player_id'], False)
            
            if success:
                embed = discord.Embed(
                    title="✅ Reserva Definido",
                    description=f"{target_player['name']} agora é reserva do seu time!",
                    color=0x00ff00
                )
                embed.add_field(
                    name="💡 Dica",
                    value="Use `/titular` para definir jogadores como titular.",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Erro ao definir jogador como reserva. Tente novamente.",
                    color=0xff0000
                )
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            print(f"Erro ao definir reserva: {e}")
            await interaction.response.send_message("❌ Erro ao definir reserva.", ephemeral=True)
    
    async def handle_sell_selection(self, interaction):
        """Lida com seleção de jogador para venda"""
        try:
            # Obtém o valor selecionado
            selected_value = interaction.data.get("values", [None])[0]
            if not selected_value:
                await interaction.response.send_message("❌ Nenhum jogador selecionado.", ephemeral=True)
                return
            
            player_id = int(selected_value)
            user_id = interaction.user.id
            
            # Busca jogador no banco
            players = await self.db.get_user_players(user_id)
            target_player = None
            
            for player in players:
                if player['id'] == player_id:
                    target_player = player
                    break
            
            if not target_player:
                await interaction.response.send_message("❌ Jogador não encontrado.", ephemeral=True)
                return
            
            # Calcula valor de venda
            sell_value = int(target_player['market_value'] * 0.8)
            
            # Confirma venda
            embed = discord.Embed(
                title="💰 Confirmar Venda",
                description=f"Você está vendendo **{target_player['name']}** por **${sell_value:,}**\n\n"
                           f"Overall: {target_player['overall']} | Time: {target_player['team']}\n"
                           f"Raridade: {target_player['rarity']} | Posição: {target_player['position']}",
                color=0xffa500
            )
            
            # Adiciona botões de confirmação
            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.green,
                label="Confirmar Venda",
                emoji="💰",
                custom_id=f"sell_confirm_{player_id}"
            ))
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.red,
                label="Cancelar",
                emoji="❌",
                custom_id="sell_cancel"
            ))
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            print(f"Erro ao selecionar jogador para venda: {e}")
            await interaction.response.send_message("❌ Erro ao selecionar jogador.", ephemeral=True)
    
    # Métodos de Partida Interativa
    async def start_match_game(self, interaction):
        """Inicia o jogo de partida"""
        try:
            # Inicia no primeiro quarto
            quarter = 1
            time = 720  # 12 minutos = 720 segundos
            score_player = 0
            score_cpu = 0
            
            # Cria primeira situação
            await self.create_match_situation(interaction, quarter, time, score_player, score_cpu)
            
        except Exception as e:
            print(f"Erro ao iniciar partida: {e}")
            await interaction.response.send_message("❌ Erro ao iniciar partida.", ephemeral=True)
    
    async def create_match_situation(self, interaction, quarter, time, score_player, score_cpu):
        """Cria uma nova situação na partida"""
        try:
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
            
        except Exception as e:
            print(f"Erro ao criar situação: {e}")
            await interaction.response.send_message("❌ Erro ao criar situação.", ephemeral=True)
    
    async def handle_match_action(self, interaction, custom_id):
        """Lida com ação escolhida na partida"""
        try:
            # Formato: match_ACTION_QUARTER_TIME_SCORE_PLAYER_SCORE_CPU
            parts = custom_id.split("_")
            if len(parts) < 6:
                await interaction.response.send_message("❌ Formato inválido.", ephemeral=True)
                return
            
            action = parts[1]
            quarter = int(parts[2])
            time = int(parts[3])
            score_player = int(parts[4])
            score_cpu = int(parts[5])
            
            # Resolve a ação
            await self.resolve_match_action(interaction, action, quarter, time, score_player, score_cpu)
            
        except Exception as e:
            print(f"Erro ao processar ação: {e}")
            await interaction.response.send_message("❌ Erro ao processar ação.", ephemeral=True)
    
    async def resolve_match_action(self, interaction, action, quarter, time, score_player, score_cpu):
        """Resolve a ação escolhida na partida"""
        try:
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
            result = action_results.get(action, {"success": "✅ Ação bem-sucedida!", "fail": "❌ Ação falhou"})
            
            # Simula dados de RPG (1-100)
            roll = random.randint(1, 100)
            
            # Determina sucesso baseado na taxa de sucesso da ação
            success_rate = 0.5  # Taxa padrão
            
            # Busca taxa de sucesso específica
            for situation in self.get_match_situations():
                for option in situation["options"]:
                    if option["custom_id"] == action:
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
            
        except Exception as e:
            print(f"Erro ao resolver ação: {e}")
            await interaction.response.send_message("❌ Erro ao resolver ação.", ephemeral=True)
    
    async def continue_match(self, interaction, custom_id):
        """Continua a partida após uma jogada"""
        try:
            # Formato: continue_match_QUARTER_TIME_SCORE_PLAYER_SCORE_CPU
            parts = custom_id.split("_")
            if len(parts) < 5:
                await interaction.response.send_message("❌ Formato inválido.", ephemeral=True)
                return
            
            quarter = int(parts[2])
            time = int(parts[3])
            score_player = int(parts[4])
            score_cpu = int(parts[5])
            
            # Simula tempo passando
            time -= random.randint(15, 45)  # 15-45 segundos por jogada
            
            # Verifica se o quarto acabou
            if time <= 0:
                quarter += 1
                if quarter > 4:
                    # Fim do jogo
                    await self.end_match(interaction, score_player, score_cpu)
                    return
                else:
                    time = 720  # Novo quarto
            
            # Cria nova situação
            await self.create_match_situation(interaction, quarter, time, score_player, score_cpu)
            
        except Exception as e:
            print(f"Erro ao continuar partida: {e}")
            await interaction.response.send_message("❌ Erro ao continuar partida.", ephemeral=True)
    
    async def end_match(self, interaction, score_player, score_cpu):
        """Finaliza a partida"""
        try:
            # Determina vencedor
            if score_player > score_cpu:
                result = "🏆 **VITÓRIA!** 🏆"
                color = 0x00ff00
                money_gain = 500
            elif score_cpu > score_player:
                result = "❌ **DERROTA** ❌"
                color = 0xff0000
                money_gain = -200
            else:
                result = "🤝 **EMPATE** 🤝"
                color = 0x808080
                money_gain = 100
            
            # Cria embed final
            embed = discord.Embed(
                title="🏀 Fim de Jogo!",
                description=f"**Placar Final:** {score_player} x {score_cpu}\n\n"
                           f"**Resultado:** {result}\n"
                           f"**Dinheiro:** ${money_gain:+d}",
                color=color
            )
            
            embed.add_field(
                name="📊 Estatísticas",
                value=f"**Seus Pontos:** {score_player}\n"
                      f"**Pontos CPU:** {score_cpu}\n"
                      f"**Diferença:** {abs(score_player - score_cpu)}",
                inline=True
            )
            
            # Botão para jogar novamente
            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.green,
                label="🔄 Jogar Novamente",
                emoji="🏀",
                custom_id="play_again"
            ))
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            print(f"Erro ao finalizar partida: {e}")
            await interaction.response.send_message("❌ Erro ao finalizar partida.", ephemeral=True)
    
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
