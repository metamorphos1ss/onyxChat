add_user = """
INSERT IGNORE INTO users(tgid, username, last_message_at)
VALUES (%s, %s, CURRENT_TIMESTAMP)
"""

bind_current_session_to_user = """
UPDATE users
SET current_session_id = %s
WHERE tgid = %s
"""

