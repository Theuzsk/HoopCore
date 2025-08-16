# 🏀 HoopCore - RPG de Basquete da NBA 2025

Um bot do Discord profissional e completo para RPG de basquete, inspirado no bot DreamTeam (futebol), mas adaptado para basquete com jogadores reais da NBA 2025.

## ✨ Funcionalidades

### 🏀 Sistema de Times
- Criação de times personalizados
- Gerenciamento de titulares e reservas
- Sistema de overall baseado nos jogadores
- Estatísticas detalhadas do time

### 👥 Banco de Dados de Jogadores
- **Jogadores Lendários:** LeBron James, Stephen Curry, Giannis Antetokounmpo, Nikola Jokić, etc.
- **Jogadores Épicos:** Ja Morant, Zion Williamson, Anthony Edwards, etc.
- **Jogadores Raros:** Bam Adebayo, De'Aaron Fox, Donovan Mitchell, etc.
- **Jogadores Comuns:** Role players da NBA

### 💰 Sistema Econômico
- Dinheiro virtual para compras
- Loja que atualiza a cada 10 minutos
- Packs gratuitos a cada 25 minutos
- Packs premium por $5,000
- Recompensa diária de $1,000

### 🎮 Sistema de Partidas
- Desafios entre jogadores
- Simulação de partidas baseada no overall
- Sistema de vitórias/derrotas
- Prêmios por vitória (+$500) e penalidades por derrota (-$200)

### 📊 Rankings e Estatísticas
- Ranking por overall do time
- Ranking por dinheiro
- Ranking por vitórias
- Estatísticas individuais detalhadas

### 🌍 Multi-idioma
- Português (padrão)
- Inglês
- Espanhol

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Conta no Discord Developer Portal
- Token de bot do Discord

### Passos de Instalação

1. **Clone o repositório:**
```bash
git clone <url-do-repositorio>
cd HoopCore
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure o token do bot:**
   - Abra o arquivo `config.py`
   - Substitua `'SEU_TOKEN_AQUI'` pelo token do seu bot

4. **Execute o bot:**
```bash
python main.py
```

## 📋 Comandos Disponíveis

### 🏀 Comandos de Time
- `/criartime` - Cria um novo time
- `/time` - Mostra informações do seu time
- `/jogadores` - Lista todos os seus jogadores
- `/titular` - Define jogador como titular
- `/reserva` - Define jogador como reserva
- `/vender` - Vende um jogador

### 🛒 Comandos de Loja
- `/loja` - Mostra a loja de jogadores
- `/comprar` - Compra um jogador da loja
- `/pack` - Abre pack gratuito (25min cooldown)
- `/packpremium` - Compra pack premium ($5,000)
- `/diario` - Coleta recompensa diária
- `/dinheiro` - Mostra seu dinheiro

### 🎮 Comandos de Partida
- `/desafiar` - Desafia outro jogador
- `/partida` - Inicia partida simulada
- `/ranking` - Mostra rankings
- `/estatisticas` - Suas estatísticas
- `/historico` - Histórico de partidas

### ⚙️ Comandos Gerais
- `/ajuda` - Mostra todos os comandos
- `/status` - Status do bot
- `/idioma` - Troca idioma do bot
- `/info` - Informações sobre o bot
- `/creditos` - Créditos do bot
- `/ping` - Testa latência do bot

## 🏗️ Estrutura do Projeto

```
HoopCore/
├── main.py              # Arquivo principal do bot
├── config.py            # Configurações e constantes
├── database.py          # Sistema de banco de dados
├── utils.py             # Utilitários e helpers
├── requirements.txt     # Dependências
├── README.md           # Este arquivo
└── cogs/               # Módulos de comandos
    ├── teams.py        # Comandos de times
    ├── shop.py         # Comandos de loja
    ├── matches.py      # Comandos de partidas
    └── general.py      # Comandos gerais
```

## 🎯 Como Jogar

1. **Crie seu time:**
   - Use `/criartime` para criar um time
   - Escolha um nome e logo (opcional)

2. **Colete jogadores:**
   - Use `/pack` para obter jogadores gratuitos
   - Use `/loja` para comprar jogadores
   - Use `/packpremium` para packs especiais

3. **Monte seu time:**
   - Use `/titular` para definir 5 titulares
   - Use `/reserva` para definir reservas
   - Use `/jogadores` para ver sua coleção

4. **Compita:**
   - Use `/desafiar` para desafiar outros jogadores
   - Use `/partida` para partidas simuladas
   - Use `/ranking` para ver sua posição

5. **Progrida:**
   - Ganhe dinheiro com vitórias
   - Colete jogadores mais raros
   - Melhore seu time constantemente

## 🎨 Características Técnicas

- **Framework:** discord.py 2.3.0+
- **Banco de Dados:** SQLite
- **Comandos:** Slash Commands (app_commands)
- **Embeds:** Profissionais e responsivas
- **Botões:** Interativos para todas as ações
- **Cores:** Sistema de cores consistente
- **Emojis:** Abundantes e temáticos

## 🎮 Sistema de Raridades

- **Lendário (3%):** Jogadores mais fortes da NBA
- **Épico (12%):** Estrelas em ascensão
- **Raro (25%):** Jogadores sólidos
- **Comum (60%):** Role players

## 💰 Sistema Econômico

- **Dinheiro inicial:** $10,000
- **Recompensa diária:** $1,000
- **Vitória em partida:** +$500
- **Derrota em partida:** -$200
- **Pack Premium:** $5,000 (3 jogadores)
- **Venda de jogadores:** 80% do valor de mercado

## 🔧 Configuração Avançada

### Variáveis de Ambiente
```bash
BOT_TOKEN=seu_token_aqui
```

### Personalização
- Edite `config.py` para alterar cores, emojis e configurações
- Modifique `database.py` para adicionar mais jogadores
- Ajuste `utils.py` para personalizar embeds

## 🐛 Solução de Problemas

### Erro de Token
```
❌ ERRO: Configure o token do bot no arquivo config.py!
```
**Solução:** Configure o token no arquivo `config.py`

### Erro de Dependências
```
ModuleNotFoundError: No module named 'discord'
```
**Solução:** Execute `pip install -r requirements.txt`

### Erro de Permissões
```
BotMissingPermissions
```
**Solução:** Dê as permissões necessárias ao bot no servidor

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🙏 Agradecimentos

- Comunidade Discord
- Desenvolvedores do discord.py
- Fãs de basquete da NBA
- Inspiração do bot DreamTeam

## 📞 Suporte

Se você encontrar algum problema ou tiver dúvidas:

1. Verifique a seção de solução de problemas
2. Abra uma issue no GitHub
3. Entre em contato com o desenvolvedor

---

**🏀 HoopCore - O melhor RPG de basquete da NBA 2025!**

*Desenvolvido com ❤️ e discord.py*
