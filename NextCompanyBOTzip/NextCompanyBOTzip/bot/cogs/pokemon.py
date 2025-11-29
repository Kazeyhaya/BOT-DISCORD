import discord
from discord.ext import commands
from discord import ui
import random
from datetime import datetime
from collections import defaultdict

from ..config import Config
from ..constants import RARITY_COLORS, RARITY_EMOJIS
from ..data.pokemon import POKEMON_DB, get_pokemon_by_name, get_pokemon_by_rarity, get_pokemon_art_url, get_pokemon_card_url
from ..utils.database import JsonDatabase


class PokedexView(ui.View):
    def __init__(self, pokemon_list: list, owner_name: str, owner_id: int):
        super().__init__(timeout=120)
        self.pokemon_list = pokemon_list
        self.owner_name = owner_name
        self.owner_id = owner_id
        self.current_index = 0

    def update_buttons(self):
        for child in self.children:
            if hasattr(child, 'custom_id'):
                if child.custom_id == 'prev':
                    child.disabled = self.current_index == 0
                elif child.custom_id == 'next':
                    child.disabled = self.current_index >= len(self.pokemon_list) - 1

    def get_current_embed(self) -> discord.Embed:
        if not self.pokemon_list:
            return discord.Embed(
                title=f"Pokedex de {self.owner_name}",
                description="Nenhum Pokemon capturado ainda!",
                color=discord.Color.red()
            )

        poke_name, quantidade = self.pokemon_list[self.current_index]
        poke_info = get_pokemon_by_name(poke_name)

        if not poke_info:
            return discord.Embed(
                title="Pokemon nao encontrado",
                color=discord.Color.red()
            )

        raridade = poke_info.get('raridade', 'Comum')
        cor = RARITY_COLORS.get(raridade, 0x95a5a6)
        emoji = RARITY_EMOJIS.get(raridade, '')
        tipo = poke_info.get('tipo', 'Normal')
        evolui = poke_info.get('evolui_para')
        poke_id = poke_info.get('id', 1)

        embed = discord.Embed(
            title=f"{emoji} {poke_name}",
            color=cor
        )

        embed.add_field(name="Tipo", value=tipo, inline=True)
        embed.add_field(name="Raridade", value=raridade, inline=True)
        embed.add_field(name="Quantidade", value=f"x{quantidade}", inline=True)

        if evolui:
            embed.add_field(name="Evolui para", value=evolui, inline=True)
        else:
            embed.add_field(name="Evolucao", value="Forma Final", inline=True)

        if quantidade >= 3 and evolui:
            embed.add_field(name="Dica", value=f"Voce pode usar `!evoluir {poke_name}` para evoluir!", inline=False)

        art_url = get_pokemon_card_url(poke_id)
        embed.set_image(url=art_url)

        embed.set_footer(text=f"Pokemon {self.current_index + 1} de {len(self.pokemon_list)} | Pokedex de {self.owner_name}")

        return embed

    @ui.button(label="Anterior", style=discord.ButtonStyle.secondary, emoji="⬅️", custom_id="prev", disabled=True)
    async def prev_btn(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.owner_id:
            return await interaction.response.send_message("Essa Pokedex nao e sua!", ephemeral=True)

        if self.current_index > 0:
            self.current_index -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_current_embed(), view=self)
        else:
            await interaction.response.defer()

    @ui.button(label="Proximo", style=discord.ButtonStyle.secondary, emoji="➡️", custom_id="next")
    async def next_btn(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.owner_id:
            return await interaction.response.send_message("Essa Pokedex nao e sua!", ephemeral=True)

        if self.current_index < len(self.pokemon_list) - 1:
            self.current_index += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_current_embed(), view=self)
        else:
            await interaction.response.defer()

    @ui.button(label="Lista", style=discord.ButtonStyle.primary, emoji="📋", custom_id="list")
    async def list_btn(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.owner_id:
            return await interaction.response.send_message("Essa Pokedex nao e sua!", ephemeral=True)

        total = sum(qtd for _, qtd in self.pokemon_list)
        especies = len(self.pokemon_list)

        txt = "\n".join([f"**{nome}**: x{qtd}" for nome, qtd in self.pokemon_list[:15]])
        if len(self.pokemon_list) > 15:
            txt += f"\n... e mais {len(self.pokemon_list) - 15} especies"

        embed = discord.Embed(
            title=f"Pokedex de {self.owner_name}",
            description=f"**Total capturados:** {total}\n**Especies unicas:** {especies}\n\n{txt}",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=self)


class PokemonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pokemon_atual = None
        self.cooldowns = defaultdict(dict)

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

    @commands.command(name='pokemon')
    async def spawn_pokemon(self, ctx):
        if not self.check_cooldown(ctx.author.id, 'pokemon', 30):
            remaining = self.get_cooldown_remaining(ctx.author.id, 'pokemon', 30)
            return await ctx.send(f"Aguarde {remaining}s para chamar outro Pokemon.")

        chance = random.randint(1, 100)
        if chance <= 3:
            pool = get_pokemon_by_rarity('Lendario')
        elif chance <= 15:
            pool = get_pokemon_by_rarity('Epico')
        elif chance <= 40:
            pool = get_pokemon_by_rarity('Raro')
        else:
            pool = get_pokemon_by_rarity('Comum')

        poke = random.choice(pool)
        self.pokemon_atual = poke

        cor = RARITY_COLORS.get(poke['raridade'], 0x95a5a6)
        emoji = RARITY_EMOJIS.get(poke['raridade'], '')

        embed = discord.Embed(
            title=f"{emoji} Um {poke['nome']} selvagem apareceu!",
            description=f"**Raridade:** {poke['raridade']}\n**Tipo:** {poke.get('tipo', 'Normal')}\n\nUse `!pokebola` para capturar!",
            color=cor
        )
        embed.set_image(url=get_pokemon_card_url(poke['id']))
        await ctx.send(embed=embed)

    @commands.command(name='pokebola')
    async def catch_pokemon(self, ctx):
        if not self.pokemon_atual:
            return await ctx.send("Nenhum Pokemon para capturar! Use `!pokemon` primeiro.")

        poke = self.pokemon_atual
        chances = {'Comum': 70, 'Raro': 50, 'Epico': 30, 'Lendario': 10}
        chance = chances.get(poke['raridade'], 50)

        if random.randint(1, 100) <= chance:
            pokedex = JsonDatabase.load(Config.FILES['pokedex'], {})
            uid = str(ctx.author.id)
            if uid not in pokedex:
                pokedex[uid] = {"nome": ctx.author.name, "capturas": []}
            pokedex[uid]["capturas"].append(poke['nome'])
            JsonDatabase.save(Config.FILES['pokedex'], pokedex)
            self.pokemon_atual = None

            embed = discord.Embed(
                title=f"GOTCHA! Voce capturou **{poke['nome']}**!",
                description=f"Use `!pokedex` para ver sua colecao!",
                color=discord.Color.gold()
            )
            embed.set_image(url=get_pokemon_card_url(poke['id']))
            await ctx.send(embed=embed)
        else:
            self.pokemon_atual = None
            await ctx.send(f"**{poke['nome']}** escapou da pokebola!")

    @commands.command(name='evoluir')
    async def evolve_pokemon(self, ctx, *, nome_poke: str = None):
        if not nome_poke:
            return await ctx.send("Use: `!evoluir [nome do pokemon]`")

        uid = str(ctx.author.id)
        pokedex = JsonDatabase.load(Config.FILES['pokedex'], {})

        if uid not in pokedex or not pokedex[uid].get("capturas"):
            return await ctx.send("Voce ainda nao tem Pokemon! Use `!pokemon` para comecar.")

        nome_poke = nome_poke.title()
        info = get_pokemon_by_name(nome_poke)

        if not info:
            return await ctx.send(f"Pokemon `{nome_poke}` nao encontrado.")
        if not info['evolui_para']:
            return await ctx.send(f"**{nome_poke}** ja esta no nivel maximo!")

        qtd = pokedex[uid]['capturas'].count(info['nome'])
        if qtd < 3:
            return await ctx.send(f"Voce precisa de 3 **{info['nome']}** para evoluir. Tem apenas {qtd}.")

        for _ in range(3):
            pokedex[uid]['capturas'].remove(info['nome'])
        novo = info['evolui_para']
        pokedex[uid]['capturas'].append(novo)
        JsonDatabase.save(Config.FILES['pokedex'], pokedex)

        info_novo = get_pokemon_by_name(novo)
        embed = discord.Embed(
            title=f"Parabens! Seu {info['nome']} evoluiu para **{novo}**!",
            color=discord.Color.gold()
        )
        if info_novo:
            embed.set_image(url=get_pokemon_card_url(info_novo['id']))
        await ctx.send(content=f"{ctx.author.mention}", embed=embed)

    @commands.command(name='pokedex')
    async def show_pokedex(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        pokedex = JsonDatabase.load(Config.FILES['pokedex'], {})
        uid = str(target.id)

        if uid not in pokedex or not pokedex[uid].get("capturas"):
            if target == ctx.author:
                return await ctx.send("Sua Pokedex esta vazia! Use `!pokemon` para comecar.")
            return await ctx.send(f"A Pokedex de {target.display_name} esta vazia.")

        lista = pokedex[uid]["capturas"]
        contagem = {}
        for pokemon in lista:
            contagem[pokemon] = contagem.get(pokemon, 0) + 1

        sorted_pokemon = sorted(contagem.items(), key=lambda x: (-x[1], x[0]))

        view = PokedexView(sorted_pokemon, target.display_name, target.id)
        await ctx.send(embed=view.get_current_embed(), view=view)

    @commands.command(name='ranking')
    async def pokemon_ranking(self, ctx):
        pokedex = JsonDatabase.load(Config.FILES['pokedex'], {})

        if not pokedex:
            return await ctx.send("Ninguem capturou Pokemon ainda!")

        ranking = []
        for uid, data in pokedex.items():
            if data.get("capturas"):
                total = len(data["capturas"])
                especies = len(set(data["capturas"]))
                lendarios = sum(1 for p in data["capturas"] if any(pk['nome'] == p and pk['raridade'] == 'Lendario' for pk in POKEMON_DB))
                ranking.append({
                    'nome': data.get('nome', 'Desconhecido'),
                    'total': total,
                    'especies': especies,
                    'lendarios': lendarios
                })

        ranking.sort(key=lambda x: (-x['total'], -x['lendarios'], -x['especies']))

        embed = discord.Embed(title="Ranking Pokemon", color=discord.Color.gold())

        medalhas = ["🥇", "🥈", "🥉"]
        txt = ""
        for i, player in enumerate(ranking[:10]):
            medalha = medalhas[i] if i < 3 else f"{i+1}."
            lend_txt = f" ⭐{player['lendarios']}" if player['lendarios'] > 0 else ""
            txt += f"{medalha} **{player['nome']}** - {player['total']} capturas, {player['especies']} especies{lend_txt}\n"

        if not txt:
            txt = "Ninguem capturou Pokemon ainda!"

        embed.description = txt
        embed.set_footer(text="Use !pokemon para comecar a capturar!")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PokemonCog(bot))
