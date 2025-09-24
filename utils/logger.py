"""
Централизованная система логгирования для onyxChat
"""
import logging
import sys
import warnings
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для логов с эмодзи"""
    
    # ANSI цветовые коды и эмодзи
    LEVEL_CONFIG = {
        'DEBUG': {'color': '\033[36m', 'emoji': '🔍', 'name': 'DEBUG'},      # Cyan
        'INFO': {'color': '\033[32m', 'emoji': 'ℹ️', 'name': 'INFO'},        # Green
        'WARNING': {'color': '\033[33m', 'emoji': '⚠️', 'name': 'WARNING'},  # Yellow
        'ERROR': {'color': '\033[31m', 'emoji': '❌', 'name': 'ERROR'},      # Red
        'CRITICAL': {'color': '\033[35m', 'emoji': '🚨', 'name': 'CRITICAL'}, # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Получаем конфигурацию для уровня
        config = self.LEVEL_CONFIG.get(record.levelname, {'color': '', 'emoji': '', 'name': record.levelname})
        color = config['color']
        emoji = config['emoji']
        name = config['name']
        reset = self.RESET
        
        # Применяем цвет и эмодзи к уровню логирования
        record.levelname = f"{color}{emoji} {name}{reset}"
        
        # Применяем цвет к сообщению для важных уровней
        if record.levelname in ['ERROR', 'CRITICAL', 'WARNING']:
            record.msg = f"{color}{record.msg}{reset}"
        
        return super().format(record)


class Logger:
    """Централизованный логгер для всего проекта"""
    
    _instance: Optional['Logger'] = None
    _initialized = False
    
    def __new__(cls) -> 'Logger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            Logger._initialized = True
    
    def _setup_logging(self) -> None:
        """Настройка логгирования"""
        # Отключаем предупреждения MySQL
        warnings.filterwarnings('ignore', category=Warning, module='aiomysql')
        
        # Создаем цветной форматтер
        formatter = ColoredFormatter(
            fmt='%(asctime)s | %(name)-20s | %(levelname)-12s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Настраиваем root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Удаляем существующие обработчики
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Создаем консольный обработчик
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        console_handler.stream.reconfigure(encoding='utf-8')
        
        # Добавляем обработчик
        root_logger.addHandler(console_handler)
        
        # Настраиваем логгеры для внешних библиотек
        logging.getLogger('aiogram').setLevel(logging.WARNING)
        logging.getLogger('aiomysql').setLevel(logging.ERROR)  # Только ошибки
        logging.getLogger('aiomysql.cursors').setLevel(logging.ERROR)  # Отключаем предупреждения курсоров
        
        # Настраиваем специальные логгеры для наших модулей
        self._setup_module_loggers()
    
    def _setup_module_loggers(self) -> None:
        """Настройка логгеров для конкретных модулей"""
        # Основные модули приложения
        app_loggers = [
            'main',
            'services.user_service',
            'services.session_service', 
            'services.message_service',
            'services.notification_service',
            'services.database_service',
            'handlers.messages.start',
            'handlers.messages.admin_reply_handlers',
            'handlers.callbacks.messages_handler',
            'handlers.callbacks.users_handler',
            'middlewares.log',
            'middlewares.databaseAdd',
            'utils.refresh'
        ]
        
        for logger_name in app_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Получить логгер для модуля"""
        return logging.getLogger(name)


# Глобальный экземпляр логгера
logger_manager = Logger()


def get_logger(name: str) -> logging.Logger:
    """Удобная функция для получения логгера"""
    return logger_manager.get_logger(name)
