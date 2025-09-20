from datetime import datetime


def _format_datetime(dt: datetime) -> str:
    """Форматирует дату и время для отображения"""
    return dt.strftime("%H:%M %d.%m.%Y")


def render_session_text(
    username: str | None, 
    assigned_agent: int | None, 
    msgs: list[tuple[int, str, str | None, str | None, datetime]]
) -> tuple[str, list[tuple[int, int]]]:
    """Рендерит текст сессии с сообщениями и вложениями"""
    # Формируем заголовок
    header_parts = []
    if username:
        header_parts.append(f"👤 Клиент: @{username}")
    else:
        header_parts.append("👤 Клиент: (без username)")
    
    if assigned_agent:
        header_parts.append(f"👨‍💼 Оператор: {assigned_agent}")
    
    header_text = "\n".join(header_parts)

    # Обрабатываем сообщения
    lines = []
    attachments = []
    attachment_counter = 1
    
    for mid, direction, text, file_id, dt in msgs:
        side = "🟢 Клиент" if direction == "fromUser" else "🔵 Оператор"
        timestamp = _format_datetime(dt)
        
        if file_id and not text:
            # Сообщение с вложением
            lines.append(f"({timestamp}) {side}: 🖼 Вложение {attachment_counter}")
            attachments.append((attachment_counter, mid))
            attachment_counter += 1
        else:
            # Обычное текстовое сообщение
            message_text = text or '-'
            lines.append(f"({timestamp}) {side}: {message_text}")
    
    # Формируем итоговый текст
    body = "\n".join(lines) if lines else "Пока нет сообщений."
    return f"{header_text}\n\n{body}", attachments