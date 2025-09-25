openCreate_session = """
INSERT INTO sessions (tgid) VALUES (%s)
"""

find_open_session = """
SELECT id FROM sessions
WHERE tgid = %s AND status = 'open'
ORDER BY opened_at ASC
LIMIT 1
"""

close_session = """
UPDATE sessions
SET status = 'closed',
    closed_at = CURRENT_TIMESTAMP
WHERE id = %s AND status = 'open'
"""

assign_session = """
UPDATE sessions
SET assigned_agent = %s
WHERE id = %s AND status = 'open' AND (assigned_agent IS NULL or assigned_agent = %s) 
"""

get_session_view = """
SELECT s.id            AS session_id,
       s.tgid          AS tgid,
       u.username      AS username,
       s.assigned_agent AS assigned_agent
FROM sessions s
JOIN users u ON u.tgid = s.tgid
WHERE s.id = %s
"""

count_closed_all = """
SELECT COUNT(*) FROM sessions
WHERE status = 'closed'
"""

count_closed_mine = """
SELECT COUNT(*) FROM sessions
WHERE status='closed' AND assigned_agent=%s
"""

fetch_closed_all = """
SELECT s.id      AS session_id,
       s.tgid    AS tgid,
       u.username,
       s.closed_at
FROM sessions s
JOIN users u ON u.tgid = s.tgid
WHERE s.status='closed'
ORDER BY s.closed_at DESC, s.id DESC
LIMIT %s OFFSET %s
"""

fetch_closed_mine = """
SELECT s.id      AS session_id,
       s.tgid    AS tgid,
       u.username,
       s.closed_at
FROM sessions s
JOIN users u ON u.tgid = s.tgid
WHERE s.status='closed' AND s.assigned_agent=%s
ORDER BY s.closed_at DESC, s.id DESC
LIMIT %s OFFSET %s
"""

