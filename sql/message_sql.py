log_message = """
INSERT INTO messages (tgid, current_session_id, direction, text, file_id)
VALUES (%s, %s, %s, %s, %s)
"""

fetch_session_messages = """
SELECT id, direction, text, file_id, created_at
FROM messages
WHERE tgid = %s
  AND current_session_id = %s
ORDER BY created_at ASC
"""

get_message_file = """
SELECT file_id, current_session_id FROM messages
WHERE id = %s
"""

