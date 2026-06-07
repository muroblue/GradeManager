import sqlite3
from flask import Flask, render_template, request, jsonify
from gpa_config import GRADE_POINTS, GPA_EXCLUDED, PASSED_GRADES
from calculator import calc_summary

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

from calculator import calc_summary

# 集計API
@app.route('/api/summary', methods=['GET'])
def get_summary():
    conn = get_db()
    subjects = conn.execute('SELECT * FROM subjects').fetchall()
    conn.close()
    return jsonify(calc_summary([dict(s) for s in subjects]))

# 卒業要件取得
@app.route('/api/requirements', methods=['GET'])
def get_requirements():
    conn = get_db()
    req = conn.execute('SELECT * FROM requirements WHERE id = 1').fetchone()
    conn.close()
    return jsonify(dict(req))

# 卒業要件更新
@app.route('/api/requirements', methods=['PUT'])
def update_requirements():
    data = request.get_json()
    conn = get_db()
    conn.execute('''
        UPDATE requirements
        SET total_credits=?, liberal_credits=?, major_credits=?, required_credits=?
        WHERE id=1
    ''', (
        data.get('total_credits', 0),
        data.get('liberal_credits', 0),
        data.get('major_credits', 0),
        data.get('required_credits', 0),
    ))
    conn.commit()
    conn.close()
    return jsonify({'message': '更新しました'})

# 卒業判定
@app.route('/api/graduation', methods=['GET'])
def get_graduation():
    conn = get_db()
    subjects = conn.execute('SELECT * FROM subjects').fetchall()
    req      = conn.execute('SELECT * FROM requirements WHERE id=1').fetchone()
    conn.close()

    summary = calc_summary([dict(s) for s in subjects])
    req     = dict(req)

    earned  = summary['earned']

    checks = [
        {
            'label':    '総単位数',
            'required': req['total_credits'],
            'earned':   earned['overall'],
        },
        {
            'label':    '教養単位数',
            'required': req['liberal_credits'],
            'earned':   earned['liberal'],
        },
        {
            'label':    '専門単位数',
            'required': req['major_credits'],
            'earned':   earned['major'],
        },
        {
            'label':    '必修単位数',
            'required': req['required_credits'],
            'earned':   earned['required'],
        },
    ]

    for c in checks:
        c['shortage'] = max(0, c['required'] - c['earned'])
        c['passed']   = c['shortage'] == 0

    all_passed = all(c['passed'] for c in checks)

    return jsonify({
        'eligible': all_passed,
        'checks':   checks,
    })
if __name__ == '__main__':
    app.run(debug=True)