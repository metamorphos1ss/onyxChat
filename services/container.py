"""
Контейнер сервисов для управления зависимостями
"""
import aiomysql
from aiogram import Bot
from .user_service import UserService
from .session_service import SessionService
from .message_service import MessageService
from .notification_service import NotificationService
from .database_service import DatabaseService
from utils.logger import get_logger

logger = get_logger(__name__)


class ServiceContainer:
    """Контейнер для управления сервисами"""
    
    def __init__(self, pool: aiomysql.Pool, bot: Bot):
        """
        Инициализация контейнера сервисов
        
        Args:
            pool: Пул соединений с БД
            bot: Экземпляр бота
        """
        self.pool = pool
        self.bot = bot
        
        # Инициализируем сервисы
        self._user_service = None
        self._session_service = None
        self._message_service = None
        self._notification_service = None
        self._database_service = None
        
        logger.info("Контейнер сервисов инициализирован")
    
    @property
    def user_service(self) -> UserService:
        """Получить сервис пользователей"""
        if self._user_service is None:
            self._user_service = UserService(self.pool)
            logger.debug("UserService создан")
        return self._user_service
    
    @property
    def session_service(self) -> SessionService:
        """Получить сервис сессий"""
        if self._session_service is None:
            self._session_service = SessionService(self.pool)
            logger.debug("SessionService создан")
        return self._session_service
    
    @property
    def message_service(self) -> MessageService:
        """Получить сервис сообщений"""
        if self._message_service is None:
            self._message_service = MessageService(self.pool)
            logger.debug("MessageService создан")
        return self._message_service
    
    @property
    def notification_service(self) -> NotificationService:
        """Получить сервис уведомлений"""
        if self._notification_service is None:
            self._notification_service = NotificationService(self.pool, self.bot)
            logger.debug("NotificationService создан")
        return self._notification_service
    
    @property
    def database_service(self) -> DatabaseService:
        """Получить сервис базы данных"""
        if self._database_service is None:
            self._database_service = DatabaseService(self.pool)
            logger.debug("DatabaseService создан")
        return self._database_service
    
    def get_all_services(self) -> dict:
        """
        Получить все сервисы в виде словаря
        
        Returns:
            Словарь со всеми сервисами
        """
        return {
            'user_service': self.user_service,
            'session_service': self.session_service,
            'message_service': self.message_service,
            'notification_service': self.notification_service,
            'database_service': self.database_service
        }
