from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from handlers.messages import start
from keyboards import back, messages_page_keyboard

async def mainPageCallback(callback_query: CallbackQuery, state: FSMContext, is_admin: bool, pool):
    callback_data = callback_query.data

    if callback_data == "home":
        if is_admin:
            await state.clear()
        await start.welcome(callback_query.message, state, is_admin, pool, from_callback=True)
        await callback_query.answer()

    elif callback_data == "onyxStats":
        await callback_query.message.edit_text("здесь будет onyx stats", reply_markup=back.keyboard())
        await callback_query.answer()

    elif callback_data == "messages":
        await callback_query.message.edit_text("Чаты:", reply_markup=messages_page_keyboard.keyboard())
        await callback_query.answer()