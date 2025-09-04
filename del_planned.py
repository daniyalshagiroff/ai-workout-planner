import sqlite3
p = r'database/workout.db'
conn = sqlite3.connect(p)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT COUNT(*) AS c FROM planned_set WHERE id >= 17')
print('to_delete:', cur.fetchone()['c'])
cur.execute('DELETE FROM planned_set WHERE id >= 17')
conn.commit()
cur.execute('VACUUM')
conn.close()
print('done')
