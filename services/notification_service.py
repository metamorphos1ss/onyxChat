"""
Сервис для отправки уведомлений
"""
import asyncio
from typing import Set, Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .base_service import BaseService
from config import get_admin_ids
from utils.logger import get_logger


class NotificationService(BaseService):
    """Сервис для отправки уведомлений"""
    
    def __init__(self, pool, bot: Bot):
        """
        Инициализация сервиса уведомлений
        
        Args:
            pool: Пул соединений с БД
            bot: Экземпляр бота
        """
        super().__init__(pool)
        self.bot = bot
        self.logger = get_logger(__name__)
    
    async def notify_new_session(self, tgid: int, username: Optional[str], session_id: int) -> None:
        """
        Отправляет уведомление админам о новой сессии
        
        Args:
            tgid: Telegram ID пользователя
            username: Имя пользователя
            session_id: ID сессии
        """
        self.logger.info(f"Отправка уведомления админам о новой сессии {session_id} для пользователя {tgid}")
        
        # Формируем текст уведомления
        uline = f"@{username}" if username else "(без username)"
        text = f"Новая сессия\nКлиент: #{tgid} {uline}"
        self.logger.debug(f"Текст уведомления: {text}")

        # Создаем клавиатуру
        keyboard = self._create_session_keyboard(session_id)
        self.logger.debug(f"Создана клавиатура для сессии {session_id}")

        # Получаем список админов
        admins = get_admin_ids()
        self.logger.info(f"Отправка уведомления {len(admins)} админам: {admins}")

        # Отправляем уведомления параллельно
        await self._send_notifications_to_admins(admins, text, keyboard)
        
        self.logger.info(f"Уведомления о сессии {session_id} отправлены всем админам")
    
    def _create_session_keyboard(self, session_id: int) -> InlineKeyboardBuilder:
        """
        Создает клавиатуру для сессии
        
        Args:
            session_id: ID сессии
            
        Returns:
            InlineKeyboardBuilder с кнопками
        """
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(text="Открыть", callback_data=f"session:{session_id}"),
            InlineKeyboardButton(text="Взять чат", callback_data=f"take:{session_id}")
        )
        return kb
    
    async def _send_notifications_to_admins(self, admins: Set[int], text: str, keyboard: InlineKeyboardBuilder) -> None:
        """
        Отправляет уведомления всем админам
        
        Args:
            admins: Множество ID админов
            text: Текст уведомления
            keyboard: Клавиатура
        """
        tasks = []
        for admin_id in admins:
            task = self._send_single_notification(admin_id, text, keyboard.as_markup())
            tasks.append(task)
        
        # Выполняем все отправки параллельно
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_single_notification(self, admin_id: int, text: str, keyboard) -> None:
        """
        Отправляет уведомление одному админу
        
        Args:
            admin_id: ID админа
            text: Текст уведомления
            keyboard: Клавиатура
        """
        try:
            await self.bot.send_message(admin_id, text, reply_markup=keyboard)
            self.logger.info(f"Уведомление отправлено админу {admin_id}")
        except Exception as e:
            # Добавляем контекстную информацию об ошибке
            error_msg = str(e).lower()
            if "blocked" in error_msg or "bot was blocked" in error_msg:
                self.logger.warning(f"Админ {admin_id} заблокировал бота")
            elif "chat not found" in error_msg:
                self.logger.warning(f"Чат с админом {admin_id} не найден")
            elif "forbidden" in error_msg:
                self.logger.warning(f"Нет прав для отправки сообщения админу {admin_id}")
            elif "message too long" in error_msg:
                self.logger.error(f"Сообщение слишком длинное для админа {admin_id}")
            else:
                self.logger.exception(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    async def send_message_to_user(self, user_id: int, text: str, parse_mode: Optional[str] = None) -> None:
        """
        Отправляет сообщение пользователю
        
        Args:
            user_id: ID пользователя
            text: Текст сообщения
            parse_mode: Режим парсинга (HTML, Markdown и т.д.)
        """
        try:
            await self.bot.send_message(user_id, text, parse_mode=parse_mode)
            self.logger.info(f"Сообщение отправлено пользователю {user_id}")
        except Exception as e:
            # Добавляем контекстную информацию об ошибке
            error_msg = str(e).lower()
            if "blocked" in error_msg or "bot was blocked" in error_msg:
                self.logger.warning(f"Пользователь {user_id} заблокировал бота")
            elif "chat not found" in error_msg:
                self.logger.warning(f"Чат с пользователем {user_id} не найден")
            elif "forbidden" in error_msg:
                self.logger.warning(f"Нет прав для отправки сообщения пользователю {user_id}")
            elif "message too long" in error_msg:
                self.logger.error(f"Сообщение слишком длинное для пользователя {user_id}")
            else:
                self.logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
            raise
    
    async def send_photo_to_user(self, user_id: int, photo_file_id: str, caption: Optional[str] = None) -> None:
        """
        Отправляет фото пользователю
        
        Args:
            user_id: ID пользователя
            photo_file_id: ID фото файла
            caption: Подпись к фото
        """
        try:
            await self.bot.send_photo(user_id, photo_file_id, caption=caption)
            self.logger.info(f"Фото отправлено пользователю {user_id}")
        except Exception as e:
            self.logger.error(f"Ошибка отправки фото пользователю {user_id}: {e}")
            raise
    
    async def send_document_to_user(self, user_id: int, document_file_id: str, caption: Optional[str] = None) -> None:
        """
        Отправляет документ пользователю
        
        Args:
            user_id: ID пользователя
            document_file_id: ID документа
            caption: Подпись к документу
        """
        try:
            await self.bot.send_document(user_id, document_file_id, caption=caption)
            self.logger.info(f"Документ отправлен пользователю {user_id}")
        except Exception as e:
            self.logger.error(f"Ошибка отправки документа пользователю {user_id}: {e}")
            raise
