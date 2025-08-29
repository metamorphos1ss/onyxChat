from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def closed_list_kb(items, page: int, total_pages: int, only_mine: bool):
    """
    items: [(session_id, tgid, username, closed_at), ...]
    callback_data:
      - на карточку:     session:{session_id}
      - пагинация:       done:list:{page}:{mine}   (mine=0/1)
      - toggle:   done:toggle:{page}:{mine}
    """
    mine_flag = 1 if only_mine else 0
    b = InlineKeyboardBuilder()

    for sid, tgid, username, closed_at in items:
        title = f"#{tgid} @{username}" if username else f"#{tgid}"
        suffix = f" • {closed_at:%d.%m %H:%M}" if closed_at else ""
        b.row(InlineKeyboardButton(text=title + suffix, callback_data=f"session:{sid}"))

    title_toggle = "Мои" if not only_mine else "Все"
    b.row(InlineKeyboardButton(text=f"Показать: {title_toggle}", callback_data=f"done:toggle:{page}:{mine_flag}"))

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="‹ Пред", callback_data=f"done:list:{page-1}:{mine_flag}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="След ›", callback_data=f"done:list:{page+1}:{mine_flag}"))
    if nav:
        b.row(*nav)

    # назад
    b.row(InlineKeyboardButton(text="Назад", callback_data="home"))
    return b.as_markup()
