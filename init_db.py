import sqlite3

def init_db():
    conn = sqlite3.connect('grademanager.db')
    c = conn.cursor()

    # 科目テーブル
    c.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            credits   INTEGER NOT NULL,
            category  TEXT    NOT NULL,
            mandatory TEXT    NOT NULL,
            grade     TEXT,
            year      INTEGER,
            semester  TEXT
        )
    ''')

    # 卒業要件テーブル（1行のみ）
    c.execute('''
        CREATE TABLE IF NOT EXISTS requirements (
            id               INTEGER PRIMARY KEY,
            total_credits    INTEGER DEFAULT 0,
            liberal_credits  INTEGER DEFAULT 0,
            major_credits    INTEGER DEFAULT 0,
            required_credits INTEGER DEFAULT 0
        )
    ''')

    # 卒業要件の初期レコードを挿入
    c.execute('''
        INSERT OR IGNORE INTO requirements (id) VALUES (1)
    ''')

    conn.commit()
    conn.close()
    print("DB初期化完了")

if __name__ == '__main__':
    init_db()