import discord
from discord.ext import commands
from aiohttp import ClientTimeout
from datetime import datetime
from duckduckgo_search import DDGS
import google.generativeai as genai
import random
from collections import defaultdict

from ..config import Config
from ..constants import SUPPORT_MESSAGES
from ..data.pokemon import POKEMON_DB


class ToolsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = defaultdict(dict)
        self.chat_history = defaultdict(list)

        if Config.GEMINI_KEY:
            genai.configure(api_key=Config.GEMINI_KEY)

    def check_cooldown(self, user_id: int, command: str, seconds: int) -> bool:
        now = datetime.now()
        key = f"{user_id}_{command}"
        if key in self.cooldowns:
            last_use = self.cooldowns[key]
            if (now - last_use).total_seconds() < seconds:
                return False
        self.cooldowns[key] = now
        return True

    def get_cooldown_remaining(self, user_id: int, command: str, seconds: int) -> int:
        now = datetime.now()
        key = f"{user_id}_{command}"
        if key in self.cooldowns:
            last_use = self.cooldowns[key]
            remaining = seconds - (now - last_use).total_seconds()
            if remaining > 0:
                return int(remaining)
        return 0

    @commands.command(name='calma')
    async def send_comfort(self, ctx):
        embed = discord.Embed(
            title="Realidade",
            description=f"*{random.choice(SUPPORT_MESSAGES)}*",
            color=discord.Color.dark_red()
        )
        await ctx.send(embed=embed)

    @commands.command(name='status')
    async def check_status(self, ctx):
        msg = await ctx.send("Verificando conexoes... aguarde.")
        s_net, p_net = "Offline", "---"
        try:
            start = datetime.now()
            timeout = ClientTimeout(total=3)
            async with self.bot.session.get("https://www.google.com", timeout=timeout) as resp:
                if resp.status == 200:
                    p_net = f"{int((datetime.now() - start).total_seconds() * 1000)}ms"
                    s_net = "Online"
        except Exception as e:
            print(f"Erro ao verificar internet: {e}")

        from ..utils.database import JsonDatabase
        config = JsonDatabase.load(Config.FILES['config'], Config.DEFAULT_CONFIG)

        embed = discord.Embed(title="Status do Sistema", color=discord.Color.blue())
        embed.add_field(name="Internet", value=f"{s_net} ({p_net})", inline=True)
        embed.add_field(name="Modo Nuvem", value="Ativado", inline=True)
        saida = config.get("saida_hoje", "18:00")
        embed.add_field(name="Saida Prevista", value=saida, inline=True)
        embed.add_field(name="Pokemon Disponiveis", value=str(len(POKEMON_DB)), inline=True)

        holidays = JsonDatabase.load(Config.FILES['feriados'], Config.DEFAULT_HOLIDAYS)
        embed.add_field(name="Feriados Cadastrados", value=str(len(holidays)), inline=True)

        await msg.delete()
        await ctx.send(embed=embed)

    @commands.command(name='sorteio')
    async def sortear(self, ctx):
        mencoes = ctx.message.mentions
        if not mencoes:
            members = [m for m in ctx.channel.members if not m.bot and m != ctx.author]
            if not members:
                return await ctx.send("Ninguem disponivel para o sorteio!")
            sorteado = random.choice(members)
        else:
            sorteado = random.choice(mencoes)

        embed = discord.Embed(
            title="Sorteio!",
            description=f"O escolhido foi: **{sorteado.display_name}**!",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=sorteado.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='pesquisar')
    async def search_web(self, ctx, *, termo: str = None):
        if not termo:
            return await ctx.send("Use: `!pesquisar [termo]`")

        if not self.check_cooldown(ctx.author.id, 'pesquisar', 10):
            remaining = self.get_cooldown_remaining(ctx.author.id, 'pesquisar', 10)
            return await ctx.send(f"Aguarde {remaining}s para pesquisar novamente.")

        msg = await ctx.send(f"Buscando: `{termo}`...")
        try:
            results = DDGS().text(termo, max_results=3)
            if not results:
                await msg.edit(content="Nada encontrado.")
                return

            embed = discord.Embed(title=f"Resultados: {termo}", color=discord.Color.blue())
            for res in results:
                body = res.get('body', '')[:150]
                embed.add_field(
                    name=res.get('title', 'Sem titulo')[:100],
                    value=f"{body}...\n[Link]({res.get('href', '#')})",
                    inline=False
                )
            await msg.delete()
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Erro na pesquisa: {e}")
            await msg.edit(content="Erro na busca. Tente novamente.")

    @commands.command(name='ia')
    async def ask_gemini(self, ctx, *, pergunta: str = None):
        if not Config.GEMINI_KEY:
            return await ctx.send("IA nao configurada (falta GEMINI_KEY).")
        if not pergunta:
            return await ctx.send("Use: `!ia [sua pergunta]`")

        if not self.check_cooldown(ctx.author.id, 'ia', 5):
            remaining = self.get_cooldown_remaining(ctx.author.id, 'ia', 5)
            return await ctx.send(f"Aguarde {remaining}s para perguntar novamente.")

        async with ctx.typing():
            try:
                user_id = str(ctx.author.id)
                history = self.chat_history[user_id][-5:] if user_id in self.chat_history else []

                context = Config.BOT_PERSONALITY + "\n\n"
                if history:
                    context += "Historico recente:\n"
                    for h in history:
                        context += f"Usuario: {h['pergunta']}\nVoce: {h['resposta']}\n"
                context += f"\nPergunta atual: {pergunta}"

                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content(context)
                txt = response.text

                if user_id not in self.chat_history:
                    self.chat_history[user_id] = []
                self.chat_history[user_id].append({'pergunta': pergunta, 'resposta': txt[:200]})
                if len(self.chat_history[user_id]) > 10:
                    self.chat_history[user_id] = self.chat_history[user_id][-10:]

                if len(txt) > 2000:
                    for i in range(0, len(txt), 1900):
                        await ctx.send(txt[i:i+1900])
                else:
                    await ctx.send(txt)
            except Exception as e:
                print(f"Erro na IA: {e}")
                await ctx.send("Ops, deu um erro na IA. Tenta de novo!")

    @commands.command(name='help')
    async def show_help(self, ctx):
        embed = discord.Embed(
            title="Comandos do Bot NextCompany",
            description="Lista de comandos disponiveis",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Pokemon",
            value="`!pokemon` - Encontrar Pokemon\n`!pokebola` - Capturar\n`!pokedex` - Ver colecao\n`!evoluir [nome]` - Evoluir\n`!ranking` - Ver ranking",
            inline=False
        )

        embed.add_field(
            name="Horarios",
            value="`!tempo` - Tempo restante\n`!horaextra HH:MM` - Ajustar saida\n`!normal` - Resetar horario\n`!lembrete [tempo] [msg]` - Criar lembrete",
            inline=False
        )

        embed.add_field(
            name="Feriados",
            value="`!feriados` - Listar\n`!addferiado DD/MM Nome` - Adicionar\n`!rmferiado DD/MM` - Remover",
            inline=False
        )

        embed.add_field(
            name="Utilidades",
            value="`!status` - Status do sistema\n`!pesquisar [termo]` - Buscar na web\n`!ia [pergunta]` - Perguntar para IA\n`!sorteio` - Sortear pessoa\n`!calma` - Mensagem de suporte",
            inline=False
        )

        embed.set_footer(text="NextCompany Bot - Feito com carinho pelo time!")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ToolsCog(bot))
