from datetime import datetime

def _format_datetime(dt: datetime) -> str:
    return dt.strftime("%H:%M %d.%m.%Y")

def render_session_text(username: str | None, assigned_agent: int | None, msgs: list[tuple[int, str, str | None, str | None, datetime]]) -> tuple[str, list[tuple[int, int]]]:
    header = []
    header.append(f"👤 Клиент: @{username}") if username else "👤 Клиент: (без username)"
    
    if assigned_agent:
        header.append(f"👨‍💼 Оператор: {assigned_agent}")
    header_text = "\n".join(header)


    lines = []
    attachments = []
    n = 1
    for mid, direction, text, file_id, dt in msgs:
        side = "🟢 Клиент" if direction == "fromUser" else "🔵 Оператор"
        if file_id and not text:
            lines.append(f"({_format_datetime(dt)}) {side}: 🖼 Вложение {n}")
            attachments.append((n, mid))
            n+=1
        else:
            lines.append(f"({_format_datetime(dt)}) {side}: {text or '-'}")
    
    body = "\n".join(lines) if lines else "Пока нет сообщений."
    return f"{header_text}\n\n{body}", attachments