import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ..config import Config
from ..constants import MESSAGES
from ..utils.database import JsonDatabase
from ..utils.helpers import format_time_delta, parse_time_input


class ScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.holidays = {}
        self.config = {}
        self.lembretes = []
        self.load_data()

    def load_data(self):
        self.holidays = JsonDatabase.load(Config.FILES['feriados'], Config.DEFAULT_HOLIDAYS)
        self.config = JsonDatabase.load(Config.FILES['config'], Config.DEFAULT_CONFIG)

    def get_time_br(self):
        return datetime.now(ZoneInfo("America/Sao_Paulo")).replace(second=0, microsecond=0)

    def build_embed(self, title, description, color):
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="NextCompany System")
        return embed

    async def start_background_tasks(self):
        self.bot.loop.create_task(self.schedule_check())
        self.bot.loop.create_task(self.check_reminders())

    async def schedule_check(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = self.get_time_br()
                await self.check_time_events(now)
            except Exception as e:
                print(f"Erro no schedule_check: {e}")
            sleep_time = 60 - datetime.now().second
            await asyncio.sleep(sleep_time)

    async def check_reminders(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = datetime.now()
                for lembrete in self.lembretes[:]:
                    if now >= lembrete['quando']:
                        channel = self.bot.get_channel(lembrete['channel_id'])
                        if channel:
                            embed = discord.Embed(
                                title="Lembrete!",
                                description=lembrete['mensagem'],
                                color=discord.Color.orange()
                            )
                            await channel.send(f"<@{lembrete['user_id']}>", embed=embed)
                        self.lembretes.remove(lembrete)
            except Exception as e:
                print(f"Erro no check_reminders: {e}")
            await asyncio.sleep(10)

    async def check_time_events(self, now):
        current_time = now.strftime("%H:%M")
        weekday = now.weekday()
        if now.strftime("%d/%m") in self.holidays or weekday == 6:
            return

        channel_id = Config.DISCORD_CHANNEL_ID if Config.DISCORD_CHANNEL_ID != 0 else Config.DESK_CHANNEL_ID
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        embed = None
        if weekday == 5:
            if current_time == "08:00":
                embed = self.build_embed("Sabado", random.choice(MESSAGES['weekend']), discord.Color.blue())
            elif current_time == "12:00":
                embed = self.build_embed("Fim", random.choice(MESSAGES['weekend_end']), discord.Color.green())
        else:
            if current_time == "08:00":
                embed = self.build_embed("Bom dia", random.choice(MESSAGES['morning']), discord.Color.blue())
            elif current_time == "12:00":
                embed = self.build_embed("Almoco", random.choice(MESSAGES['lunch_start']), discord.Color.gold())
            elif current_time == "14:00":
                embed = self.build_embed("Retorno", random.choice(MESSAGES['lunch_end']), discord.Color.blue())
            elif current_time == "18:00":
                embed = self.build_embed("Saida", random.choice(MESSAGES['eod']), discord.Color.purple())

        if embed:
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Erro ao enviar mensagem programada: {e}")

    @commands.command(name='tempo')
    async def check_time(self, ctx):
        now = self.get_time_br()
        weekday = now.weekday()
        saida_str = self.config.get("saida_hoje", "18:00")
        h_saida, m_saida = map(int, saida_str.split(':'))
        targets = {
            "e": now.replace(hour=8, minute=0),
            "a": now.replace(hour=12, minute=0),
            "v": now.replace(hour=14, minute=0),
            "s": now.replace(hour=h_saida, minute=m_saida)
        }

        msg, cor = "Expediente encerrado. Bom descanso!", discord.Color.dark_grey()

        if weekday < 5:
            if now < targets['e']:
                msg, cor = f"Comecamos em **{format_time_delta(targets['e'] - now)}**", discord.Color.orange()
            elif now < targets['a']:
                msg, cor = f"Almoco em **{format_time_delta(targets['a'] - now)}**", discord.Color.blue()
            elif now < targets['v']:
                msg, cor = f"Retorno em **{format_time_delta(targets['v'] - now)}**", discord.Color.gold()
            elif now < targets['s']:
                prefix = "**PLANTAO**: " if saida_str != "18:00" else ""
                cor_saida = discord.Color.magenta() if saida_str != "18:00" else discord.Color.purple()
                msg, cor = f"{prefix}Saida em **{format_time_delta(targets['s'] - now)}**", cor_saida
        elif weekday == 5:
            targets_sab = {"e": now.replace(hour=8, minute=0), "s": now.replace(hour=12, minute=0)}
            if now < targets_sab['e']:
                msg, cor = f"Sabado! Comeca em **{format_time_delta(targets_sab['e'] - now)}**", discord.Color.orange()
            elif now < targets_sab['s']:
                msg, cor = f"Fim de semana em **{format_time_delta(targets_sab['s'] - now)}**", discord.Color.green()

        embed = discord.Embed(title="Cronometro do Expediente", description=msg, color=cor)
        await ctx.send(embed=embed)

    @commands.command(name='horaextra')
    async def set_hora_extra(self, ctx, horario: str = None):
        if not horario:
            return await ctx.send("Use: `!horaextra HH:MM` (ex: !horaextra 20:00)")
        try:
            datetime.strptime(horario, "%H:%M")
            self.config["saida_hoje"] = horario
            JsonDatabase.save(Config.FILES["config"], self.config)
            await ctx.send(f"Combinado! Saida ajustada para **{horario}**.")
        except ValueError:
            await ctx.send("Formato invalido. Use HH:MM (ex: 20:00)")

    @commands.command(name='normal')
    async def set_hora_normal(self, ctx):
        self.config["saida_hoje"] = "18:00"
        JsonDatabase.save(Config.FILES["config"], self.config)
        await ctx.send("Feito! Horario resetado para **18:00**.")

    @commands.command(name='feriados')
    async def list_feriados(self, ctx):
        if not self.holidays:
            return await ctx.send("Nenhum feriado cadastrado.")

        sorted_holidays = sorted(self.holidays.items(), key=lambda x: (int(x[0].split('/')[1]), int(x[0].split('/')[0])))

        embed = discord.Embed(title="Feriados Cadastrados", color=discord.Color.green())

        chunks = []
        current_chunk = ""
        for data, nome in sorted_holidays:
            line = f"**{data}** - {nome}\n"
            if len(current_chunk) + len(line) > 1000:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += line
        if current_chunk:
            chunks.append(current_chunk)

        for i, chunk in enumerate(chunks):
            field_name = "Lista" if i == 0 else f"Lista (cont. {i+1})"
            embed.add_field(name=field_name, value=chunk, inline=False)

        embed.set_footer(text=f"Total: {len(self.holidays)} feriados")
        await ctx.send(embed=embed)

    @commands.command(name='addferiado')
    async def add_feriado(self, ctx, data: str = None, *, nome: str = None):
        if not data or not nome:
            return await ctx.send("Use: `!addferiado DD/MM Nome do Feriado`\nEx: `!addferiado 20/11 Consciencia Negra`")

        try:
            dia, mes = data.split('/')
            if not (1 <= int(dia) <= 31 and 1 <= int(mes) <= 12):
                raise ValueError
            data_formatada = f"{int(dia):02d}/{int(mes):02d}"
        except:
            return await ctx.send("Data invalida. Use o formato DD/MM")

        self.holidays[data_formatada] = nome
        JsonDatabase.save(Config.FILES["feriados"], self.holidays)
        await ctx.send(f"Feriado adicionado: **{data_formatada}** - {nome}")

    @commands.command(name='rmferiado')
    async def remove_feriado(self, ctx, data: str = None):
        if not data:
            return await ctx.send("Use: `!rmferiado DD/MM`\nEx: `!rmferiado 20/11`")

        try:
            dia, mes = data.split('/')
            data_formatada = f"{int(dia):02d}/{int(mes):02d}"
        except:
            return await ctx.send("Data invalida. Use o formato DD/MM")

        if data_formatada in self.holidays:
            nome = self.holidays.pop(data_formatada)
            JsonDatabase.save(Config.FILES["feriados"], self.holidays)
            await ctx.send(f"Feriado removido: **{data_formatada}** - {nome}")
        else:
            await ctx.send(f"Feriado nao encontrado: {data_formatada}")

    @commands.command(name='lembrete')
    async def set_reminder(self, ctx, tempo: str = None, *, mensagem: str = None):
        if not tempo or not mensagem:
            return await ctx.send("Use: `!lembrete [tempo] [mensagem]`\nExemplos:\n- `!lembrete 30m Reuniao`\n- `!lembrete 2h Almocar`\n- `!lembrete 1h30m Ligar cliente`")

        try:
            total_minutes = parse_time_input(tempo)

            if total_minutes <= 0:
                raise ValueError("Tempo deve ser positivo")
            if total_minutes > 1440:
                return await ctx.send("Limite de 24 horas para lembretes.")

            quando = datetime.now() + timedelta(minutes=total_minutes)
            self.lembretes.append({
                'user_id': ctx.author.id,
                'channel_id': ctx.channel.id,
                'mensagem': mensagem,
                'quando': quando
            })

            hora_lembrete = quando.strftime("%H:%M")
            await ctx.send(f"Lembrete configurado para **{hora_lembrete}** ({total_minutes} minutos)")

        except Exception as e:
            print(f"Erro ao criar lembrete: {e}")
            await ctx.send("Formato invalido. Use: 30m, 2h, 1h30m")


async def setup(bot):
    cog = ScheduleCog(bot)
    await bot.add_cog(cog)
    await cog.start_background_tasks()
