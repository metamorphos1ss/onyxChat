"""
Константы для проекта onyxChat
"""

# Настройки базы данных
DB_PORT = 3306
DB_MIN_POOL_SIZE = 5
DB_MAX_POOL_SIZE = 10

# Настройки пагинации
CLOSED_PER_PAGE = 10

# Типы сессий
SESSION_TYPES = {
    "TO_SERVE": "toServe",
    "PROCESSING_MINE": "processing_mine", 
    "PROCESSING": "processing"
}

# Направления сообщений
MESSAGE_DIRECTIONS = {
    "FROM_USER": "fromUser",
    "FROM_AGENT": "fromAgent"
}

# Статусы сессий
SESSION_STATUS = {
    "OPEN": "open",
    "CLOSED": "closed"
}
