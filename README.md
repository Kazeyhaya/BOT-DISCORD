# NextCompany Discord Bot

# Overview
Bot do Discord para o time NextCompany com funcionalidades de gestão de horários, sistema de Pokemon, integração com IA Gemini e webhook do DeskManager.

## Estrutura do Projeto

```
/
├── main.py                 # Entry point
├── bot/
│   ├── __init__.py
│   ├── workbot.py          # Classe principal do bot
│   ├── config.py           # Configuracoes e variaveis de ambiente
│   ├── constants.py        # Constantes (mensagens, cores, etc)
│   ├── cogs/
│   │   ├── __init__.py
│   │   ├── pokemon.py      # Comandos de Pokemon (!pokemon, !pokebola, !pokedex)
│   │   ├── schedule.py     # Comandos de horarios (!tempo, !lembrete, !feriados)
│   │   ├── tools.py        # Ferramentas (!ia, !pesquisar, !status, !calma)
│   │   └── deskmanager.py  # Webhook do DeskManager
│   ├── data/
│   │   ├── __init__.py
│   │   └── pokemon.py      # Banco de dados de Pokemon
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py      # Funcoes auxiliares
│       └── database.py     # Gerenciamento de JSON
├── config.json             # Configuracoes persistentes
├── feriados.json           # Lista de feriados
└── pokedex.json            # Dados das pokedex dos usuarios
```

## Comandos Disponiveis

### Pokemon
- `!pokemon` - Encontrar um Pokemon selvagem
- `!pokebola` - Tentar capturar o Pokemon
- `!pokedex [@usuario]` - Ver colecao com navegacao visual
- `!evoluir [nome]` - Evoluir Pokemon (precisa de 3 iguais)
- `!ranking` - Ver ranking de capturas

### Horarios
- `!tempo` - Ver tempo restante ate proximo evento
- `!horaextra HH:MM` - Ajustar horario de saida
- `!normal` - Resetar horario para 18:00
- `!lembrete [tempo] [mensagem]` - Criar lembrete (ex: 30m, 2h, 1h30m)

### Feriados
- `!feriados` - Listar feriados cadastrados
- `!addferiado DD/MM Nome` - Adicionar feriado
- `!rmferiado DD/MM` - Remover feriado

### Utilidades
- `!status` - Ver status do sistema
- `!pesquisar [termo]` - Buscar na web
- `!ia [pergunta]` - Perguntar para IA Gemini
- `!sorteio` - Sortear pessoa do canal
- `!calma` - Mensagem de suporte de TI
- `!help` - Ver todos os comandos

## Variaveis de Ambiente Necessarias
- `DISCORD_TOKEN` - Token do bot Discord
- `DISCORD_CHANNEL_ID` - ID do canal principal
- `DISCORD_ROLE_ID` - ID da role para mencoes (opcional)
- `GEMINI_KEY` - Chave da API do Google Gemini
- `DESK_CHANNEL_ID` - ID do canal para notificacoes do DeskManager

## Webhook DeskManager
O bot expoe um endpoint em `/deskwebhook` para receber notificacoes do DeskManager.

## Mudancas Recentes (Nov 2025)
- Refatoracao completa do codigo em modulos separados (Cogs)
- Nova Pokedex visual com navegacao por botoes e imagens oficiais
- Adicionado tipo e informacoes extras aos Pokemon
- Melhor organizacao com pastas separadas para config, data e utils
- Novo comando !help com lista completa de comandos
