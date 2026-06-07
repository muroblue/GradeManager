import sqlite3
from flask import Flask, render_template, request, jsonify
from gpa_config import GRADE_POINTS, GPA_EXCLUDED, PASSED_GRADES

app = Flask(__name__)
DB = 'grademanager.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ページ表示
@app.route('/')
def index():
    return render_template('index.html')

# 科目一覧取得
@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    conn = get_db()
    subjects = conn.execute(
        'SELECT * FROM subjects ORDER BY year ASC, semester ASC, name ASC'
    ).fetchall()
    conn.close()
    return jsonify([dict(s) for s in subjects])

# 科目登録
@app.route('/api/subjects', methods=['POST'])
def add_subject():
    data = request.get_json()
    name     = data.get('name')
    credits  = data.get('credits')
    category = data.get('category')
    mandatory = data.get('mandatory')
    grade    = data.get('grade') or None
    year     = data.get('year') or None
    semester = data.get('semester') or None

    if not name or not credits or not category or not mandatory:
        return jsonify({'error': '必須項目が不足しています'}), 400

    conn = get_db()
    conn.execute(
        'INSERT INTO subjects (name, credits, category, mandatory, grade, year, semester) VALUES (?,?,?,?,?,?,?)',
        (name, credits, category, mandatory, grade, year, semester)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': '登録しました'}), 201

# 科目更新
@app.route('/api/subjects/<int:subject_id>', methods=['PUT'])
def update_subject(subject_id):
    data = request.get_json()
    conn = get_db()
    conn.execute('''
        UPDATE subjects
        SET name=?, credits=?, category=?, mandatory=?, grade=?, year=?, semester=?
        WHERE id=?
    ''', (
        data.get('name'),
        data.get('credits'),
        data.get('category'),
        data.get('mandatory'),
        data.get('grade') or None,
        data.get('year') or None,
        data.get('semester') or None,
        subject_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'message': '更新しました'})

# 科目削除
@app.route('/api/subjects/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    conn = get_db()
    conn.execute('DELETE FROM subjects WHERE id=?', (subject_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': '削除しました'})

if __name__ == '__main__':
    app.run(debug=True)