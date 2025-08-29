# handlers/callbacks/messages_handler
NONE_TO_SERVE = "Либо юзеров нет, либо каждый уже закреплён"
COUNT_TO_SERVE = "Ожидающих пользователей: {count}"

NO_ONE_ASSIGNED_TO_ADMIN = "За вами не закреплены юзеры"
MINE_ASSIGNED_1 = "За вами закреплён {count} клиент"
MINE_ASSIGNED_2_3_4 = "За вами закреплены {count} клиента"
MINE_ASSIGNED_OTHER = "За вами закреплены {count} клиентов"

NO_ONE_ASSGINED = "Сейчас никто ни за кем не закреплён"
OTHER_ASSIGNED_1 = "Сейчас закреплен за агентами {count}"
OTHER_ASSIGNED_2_3_4 = "Сейчас закреплены за агентами {count} клиента"
OTHER_ASSIGNED_OTHER = "Сейчас закреплены за агентами {count} клиентов"

# handlers/callbacks/users_handler.py
TAKEN_SESSION = "Эту сессию уже взяли"
SESSION_NOT_FOUND = "Сессия не найдена"
CHAT_ASSIGNED_TO_YOU = "Чат закреплён за вами ✅"
FAILED_TO_CLOSE_SESSION = "Не удалось закрыть сессию"
SESSION_CLOSED_SUCCESSFUL = "Сессия закрыта"
ATTACHMENT_NOT_FOUND = "Вложение не найдено"

# handlers/messages/admin_reply_handlers
CLIENT_NOT_FOUND = "Пользователь не найден"
FAILED_TO_SEND_MESSAGE = "Не удалось отправить сообщение: {exception}"

# handlers/messages/start
WELCOME_TEXT_ONYX = "Привет, папа!"
WELCOME_TEXT_ADMIN = "Приветствую, {first_name}"
WELCOME_TEXT_USER = "Привет! Напиши свой запрос. В скором времени один из операторов тебе ответит"

SESSION_WAS_OPENED = "Просто напиши свой запрос, в скором времени один из операторов ответит"

SESSION_NOT_FOUND = "Сессия не найдена"

TAKE_CLIENT = "Взять"
AGENT_OPEN_CHAT = "Открыть чат"


# keyboards/back
BACK_KB_TEXT = "Назад"

# keyboards/messages_page_keyboard
WAITING_KB_TEXT = "Ожидают внимания"
MY_CHATS_KB_TEXT = "Мои чаты"
PROCESSING_CHATS_KB_TEXT = "В обработке"
DONE_CHATS_KB_TEXT = "Завершенные"

# keyboards/admin_keyboard
STATS_KB_TEXT = "onyxStats"
MESSAGES_KB_TEXT = "Сообщения"

# keyboards/att_kb
CLOSE_ATTACHMENT = "Закрыть вложение"

# keyboards/messages_keyboard/session_view
CLOSE_SESSION = "Закрыть сессию"

# middlewares/log
TEXT_BEFORE_START = "Сначала используйте /start"