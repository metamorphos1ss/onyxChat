"""
Централизованная система логгирования для проекта onyxChat
"""
import logging
import sys
from typing import Optional


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
        # Создаем форматтер
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Настраиваем root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Удаляем существующие обработчики
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Создаем консольный обработчик
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Добавляем обработчик
        root_logger.addHandler(console_handler)
        
        # Настраиваем логгеры для внешних библиотек
        logging.getLogger('aiogram').setLevel(logging.WARNING)
        logging.getLogger('aiomysql').setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Получить логгер для модуля"""
        return logging.getLogger(name)


# Глобальный экземпляр логгера
logger_manager = Logger()


def get_logger(name: str) -> logging.Logger:
    """Удобная функция для получения логгера"""
    return logger_manager.get_logger(name)
