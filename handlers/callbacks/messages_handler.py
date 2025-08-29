from aiogram.types import CallbackQuery

from sql import reqs

import texts

from keyboards import back
from keyboards.messages_keyboard import waiting_keyboard, closed_kb

import math


async def done_list_page(callback_query: CallbackQuery, pool):
    _, _, page_str, mine_str = callback_query.data.split(":")
    page = int(page_str)
    only_mine = bool(int(mine_str))
    await _render_done_page(callback_query, pool, page=page, only_mine=only_mine, agent_id=callback_query.from_user.id)
    await callback_query.answer()

async def done_toggle(callback_query: CallbackQuery, pool):
    _, _, page_str, mine_str = callback_query.data.split(":")
    page = int(page_str)
    only_mine = not bool(int(mine_str))
    await _render_done_page(callback_query, pool, page=page, only_mine=only_mine, agent_id=callback_query.from_user.id)
    await callback_query.answer



async def _render_done_page(callback_query, pool, page: int, only_mine: bool, agent_id: int):
    total = await reqs.count_closed(pool, only_mine=only_mine, agent_id=agent_id)
    total_pages = max(1, math.ceil(total / reqs.CLOSED_PER_PAGE))
    page = max(1, min(page, total_pages))

    rows = await reqs.fetch_closed(pool, page=page, only_mine=only_mine, agent_id=agent_id)
    
    title = "Закрытые чаты - Мои" if only_mine else "Закрытые чаты - Все"
    if not rows:
        title += "\n\nПока нет закрытых чатов в этом режиме."
        
    kb = closed_kb.closed_list_kb(rows, page=page, total_pages=total_pages, only_mine=only_mine)
    await callback_query.message.edit_text(title, reply_markup=kb)

async def messages(callback_query: CallbackQuery, is_admin: bool, pool):
    if not is_admin:
        return

    callback_data = callback_query.data.removeprefix("msg:")


    if callback_data == "toServe":
        items = await reqs.fetch_sessions(pool, "toServe")
        count = await reqs.count_sessions(pool, "toServe")
        if not items:
            await callback_query.message.edit_text(texts.NONE_TO_SERVE, reply_markup=back.keyboard())
            return

        await callback_query.message.edit_text(texts.COUNT_TO_SERVE.format(count=count), reply_markup=waiting_keyboard.kb(items))
        await callback_query.answer()

    elif callback_data == "processing_mine":
        items = await reqs.fetch_sessions(pool, "processing_mine", agent_id=callback_query.from_user.id)
        count = await reqs.count_sessions(pool, "processing_mine", agent_id=callback_query.from_user.id)
        if not items:
            await callback_query.message.edit_text(texts.NO_ONE_ASSIGNED_TO_ADMIN, reply_markup=back.keyboard())
            return
        if count == 1:
            text = texts.MINE_ASSIGNED_1.format(count=count)
        elif count in [2, 3, 4]:
            text = texts.MINE_ASSIGNED_2_3_4.format(count=count)
        else:
            text = texts.MINE_ASSIGNED_OTHER.format(count=count)
        await callback_query.message.edit_text(text=text, reply_markup=waiting_keyboard.kb(items))
        await callback_query.answer()

    elif callback_data == "processing":
        items = await reqs.fetch_sessions(pool, "processing", agent_id=callback_query.from_user.id)
        count = await reqs.count_sessions(pool, "processing", agent_id=callback_query.from_user.id)
        if not items:
            await callback_query.message.edit_text(texts.NO_ONE_ASSGINED, reply_markup=back.keyboard())
            return
        if count == 1:
            text = texts.OTHER_ASSIGNED_1.format(count=count)
        elif count in [2, 3, 4]:
            text = texts.OTHER_ASSIGNED_2_3_4.format(count=count)
        else:
            text = texts.OTHER_ASSIGNED_OTHER.format(count=count)
        await callback_query.message.edit_text(text=text, reply_markup=waiting_keyboard.kb(items))
        await callback_query.answer()
    
    elif callback_data == "done":
        await _render_done_page(callback_query, pool, page=1, only_mine=False, agent_id=callback_query.from_user.id)
        await callback_query.answer()