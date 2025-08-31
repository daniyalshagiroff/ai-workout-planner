BEGIN TRANSACTION;

-- Create user_program table for tracking user's selected programs
CREATE TABLE user_program (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  program_id INTEGER NOT NULL REFERENCES program(id) ON DELETE CASCADE,
  started_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  is_active INTEGER NOT NULL DEFAULT 1, -- 0/1 boolean
  current_week INTEGER NOT NULL DEFAULT 1,
  current_day INTEGER NOT NULL DEFAULT 1,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  UNIQUE(user_id, program_id)
);

CREATE INDEX IF NOT EXISTS user_program_user_idx ON user_program(user_id);
CREATE INDEX IF NOT EXISTS user_program_program_idx ON user_program(program_id);
CREATE INDEX IF NOT EXISTS user_program_active_idx ON user_program(user_id, is_active);

-- Trigger for updated_at
CREATE TRIGGER IF NOT EXISTS trg_user_program_updated_at
AFTER UPDATE ON user_program FOR EACH ROW
BEGIN
  UPDATE user_program SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

COMMIT;
