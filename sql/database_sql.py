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

create_statistics_table = """
CREATE TABLE IF NOT EXISTS statistics (
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

