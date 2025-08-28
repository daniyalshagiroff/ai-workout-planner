BEGIN TRANSACTION;

PRAGMA foreign_keys = OFF;

-- Recreate exercise table with relaxed CHECK: allow is_global=1 with any owner_user_id (NULL or not),
-- still require owner_user_id NOT NULL when is_global=0

CREATE TABLE exercise_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_user_id INTEGER NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  muscle_group TEXT NOT NULL,
  equipment TEXT,
  is_global INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  CHECK ( (is_global = 0 AND owner_user_id IS NOT NULL) OR (is_global = 1) )
);

INSERT INTO exercise_new (id, owner_user_id, name, muscle_group, equipment, is_global, created_at, updated_at)
SELECT id, owner_user_id, name, muscle_group, equipment, is_global, created_at, updated_at
FROM exercise;

DROP TABLE exercise;
ALTER TABLE exercise_new RENAME TO exercise;

-- Recreate indexes
CREATE UNIQUE INDEX IF NOT EXISTS exercise_owner_name_uq
  ON exercise(owner_user_id, lower(name))
  WHERE owner_user_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS exercise_global_name_uq
  ON exercise(lower(name))
  WHERE owner_user_id IS NULL AND is_global = 1;

PRAGMA foreign_keys = ON;

COMMIT;


