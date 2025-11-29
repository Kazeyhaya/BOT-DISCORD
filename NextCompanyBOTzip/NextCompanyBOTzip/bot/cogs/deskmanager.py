import discord
from discord.ext import commands
from aiohttp import web
import json
import urllib.parse
import logging

from ..config import Config
from ..utils.helpers import fix_text, get_protocolo

logger = logging.getLogger(__name__)


class DeskManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web_server = None

    async def start_webserver(self):
        self.web_server = web.Application()
        self.web_server.router.add_get('/', self.handle_health)
        self.web_server.router.add_get('/deskwebhook', self.handle_health)
        self.web_server.router.add_post('/deskwebhook', self.handle_deskmanager)
        runner = web.AppRunner(self.web_server)
        await runner.setup()

        site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
        await site.start()
        logger.info(f"Servidor Web iniciado na porta {Config.PORT}")

    async def handle_health(self, request):
        return web.Response(text="Bot NextCompany Online! Webhook: POST /deskwebhook", status=200)

    async def handle_deskmanager(self, request):
        try:
            post_data = await request.post()
            data = {}

            if 'content' in post_data:
                try:
                    data = json.loads(urllib.parse.unquote_plus(post_data['content'], encoding='utf-8'), strict=False)
                except:
                    try:
                        data = json.loads(urllib.parse.unquote_plus(post_data['content'], encoding='iso-8859-1'), strict=False)
                    except:
                        data = dict(post_data)
            else:
                try:
                    data = await request.json()
                except:
                    data = dict(post_data)

            if data.get('action') == 'save.point' or 'TPonto' in data.get('data', {}):
                return web.Response(text="Ignorado", status=200)

            channel = self.bot.get_channel(Config.DESK_CHANNEL_ID)
            if channel:
                raw_assunto = fix_text(data.get('assunto', data.get('Subject', 'Atualizacao')))
                if not raw_assunto:
                    return web.Response(text="Sem assunto", status=200)

                raw_analista = data.get('analista_nome')
                if isinstance(data.get('Operator'), dict):
                    raw_analista = raw_analista or data.get('Operator', {}).get('Name')

                raw_empresa = data.get('cliente_nome')
                if isinstance(data.get('Customer'), dict):
                    raw_empresa = raw_empresa or data.get('Customer', {}).get('Name')
                raw_empresa = fix_text(raw_empresa)

                nome_pessoa = data.get('solicitante_nome') or data.get('contato_nome')
                if isinstance(data.get('Requester'), dict):
                    nome_pessoa = data.get('Requester').get('Name')
                if isinstance(data.get('Contact'), dict):
                    nome_pessoa = nome_pessoa or data.get('Contact').get('Name')
                nome_pessoa = fix_text(nome_pessoa)

                cliente_final = None
                if nome_pessoa and raw_empresa:
                    if nome_pessoa.strip().lower() == raw_empresa.strip().lower():
                        cliente_final = raw_empresa
                    else:
                        cliente_final = f"{nome_pessoa} ({raw_empresa})"
                elif nome_pessoa:
                    cliente_final = nome_pessoa
                elif raw_empresa:
                    cliente_final = raw_empresa

                if not cliente_final or cliente_final == "None":
                    cliente_final = "Nao informado"

                operador_final = fix_text(raw_analista) if raw_analista else None

                status = fix_text(str(data.get('status_nome', 'Novo')))
                status_low = status.lower()
                prioridade = fix_text(data.get('prioridade_nome', ''))

                ticket_visual = get_protocolo(data)
                ticket_id_link = data.get('chamado_cod') or data.get('CodChamado') or data.get('id') or data.get('Id')

                logger.info(f"Webhook data keys: {list(data.keys())}")

                emoji, cor = "🆕", discord.Color.blue()
                if any(x in status_low for x in ['resolvido', 'finalizado', 'encerrado', 'conclu']):
                    emoji, cor = "✅", discord.Color.green()
                elif any(x in status_low for x in ['cancelado', 'rejeitado', 'fechado']):
                    emoji, cor = "❌", discord.Color.red()
                elif any(x in status_low for x in ['andamento', 'progresso', 'atendimento']):
                    emoji, cor = "🔧", discord.Color.orange()
                elif any(x in status_low for x in ['aguardando', 'pendente', 'espera']):
                    emoji, cor = "⏳", discord.Color.gold()

                embed = discord.Embed(title=f"Ticket: {raw_assunto}", description=f"**Status:** {emoji} {status}", color=cor)
                if ticket_visual != 'N/A':
                    embed.add_field(name="ID Ticket", value=f"#{ticket_visual}", inline=True)
                embed.add_field(name="Cliente", value=cliente_final, inline=True)
                if operador_final:
                    embed.add_field(name="Operador", value=operador_final, inline=False)
                if prioridade:
                    embed.add_field(name="Prioridade", value=prioridade, inline=True)

                link = f"https://nextcompany.desk.ms/Ticket/Detail/{ticket_id_link}" if ticket_id_link else "https://nextcompany.desk.ms/"
                embed.add_field(name="Acesso", value=f"[Abrir Painel]({link})", inline=False)
                embed.set_footer(text="DeskManager Integration")
                await channel.send(embed=embed)

            return web.Response(text="OK", status=200)
        except Exception as e:
            logger.error(f"Erro no webhook: {e}")
            return web.Response(text="Erro", status=200)


async def setup(bot):
    cog = DeskManagerCog(bot)
    await bot.add_cog(cog)
    await cog.start_webserver()
