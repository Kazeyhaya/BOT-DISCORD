from datetime import timedelta


def fix_text(texto):
    if not texto:
        return ""
    try:
        return str(texto).encode('cp1252').decode('utf-8')
    except:
        return str(texto)


def get_protocolo(data):
    campos = ['chamado', 'chave', 'protocolo', 'TicketID']
    for campo in campos:
        valor = str(data.get(campo, ''))
        if '-' in valor and len(valor) > 5:
            return valor
    return data.get('chamado_cod', 'N/A')


def format_time_delta(dt: timedelta) -> str:
    total_seconds = int(dt.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}h e {minutes}m"


def parse_time_input(tempo: str) -> int:
    total_minutes = 0
    tempo_lower = tempo.lower()

    if 'h' in tempo_lower:
        parts = tempo_lower.split('h')
        total_minutes += int(parts[0]) * 60
        if len(parts) > 1 and parts[1]:
            min_part = parts[1].replace('m', '')
            if min_part:
                total_minutes += int(min_part)
    elif 'm' in tempo_lower:
        total_minutes = int(tempo_lower.replace('m', ''))
    else:
        total_minutes = int(tempo_lower)

    return total_minutes
