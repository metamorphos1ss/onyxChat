add_user = """
INSERT IGNORE INTO users(tgid, username, last_message_at)
VALUES (%s, %s, CURRENT_TIMESTAMP)
"""

create_messages_table = """
CREATE TABLE IF NOT EXISTS messages (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tgid BIGINT UNSIGNED NOT NULL,
  current_session_id BIGINT UNSIGNED NULL,
  direction ENUM('fromUser','fromAgent') NOT NULL,
  text TEXT NULL,
  file_id VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user (tgid),
  INDEX idx_created (created_at)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
"""

create_users_table = """
CREATE TABLE IF NOT EXISTS users (
  tgid BIGINT UNSIGNED NOT NULL,
  username VARCHAR(32) NULL,
  current_session_id BIGINT UNSIGNED NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  last_message_at DATETIME NULL,
  priority ENUM('low','normal','high') NOT NULL DEFAULT 'normal',
  notes TEXT NULL,
  is_blocked TINYINT(1) NOT NULL DEFAULT 0,
  CONSTRAINT users_tgid_pk PRIMARY KEY (tgid),
  INDEX idx_users_username (username),
  INDEX idx_users_current_session (current_session_id),
  INDEX idx_users_priority (priority),
  INDEX idx_users_last_message (last_message_at)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
"""

create_sessions_table = """
CREATE TABLE IF NOT EXISTS sessions (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tgid BIGINT UNSIGNED NOT NULL,
  status ENUM('open','closed') NOT NULL DEFAULT 'open',
  assigned_agent BIGINT UNSIGNED NULL,
  opened_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  closed_at DATETIME NULL,
  INDEX idx_sessions_user (tgid),
  INDEX idx_sessions_status (status),
  INDEX idx_sessions_opened (opened_at)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
"""

create_orders_table = """
CREATE TABLE IF NOT EXISTS orders (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  account_type ENUM('personal','ours') NOT NULL DEFAULT 'personal',
  commission_percent DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  total_order_sum DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  payment_method VARCHAR(64) NULL,
  delivery_service VARCHAR(64) NULL,
  profit DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
"""

log_message = """
INSERT INTO messages (tgid, current_session_id, direction, text, file_id)
VALUES (%s, %s, %s, %s, %s)
"""

openCreate_session = """
INSERT INTO sessions (tgid) VALUES (%s)
"""

bind_current_session_to_user = """
UPDATE users
SET current_session_id = %s
WHERE tgid = %s
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
