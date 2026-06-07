from gpa_config import GRADE_POINTS, GPA_EXCLUDED, PASSED_GRADES

def calc_summary(subjects):
    """
    科目リスト（dictのリスト）を受け取り、集計結果を返す
    """
    def gpa(target):
        total_points  = 0.0
        total_credits = 0
        for s in target:
            if s['grade'] is None:
                continue
            if s['grade'] in GPA_EXCLUDED:
                continue
            credits = s['credits']
            total_points  += GRADE_POINTS[s['grade']] * credits
            total_credits += credits
        return round(total_points / total_credits, 2) if total_credits > 0 else 0.0

    def earned_credits(target):
        """単位取得済みの単位数（R含む）"""
        return sum(s['credits'] for s in target if s['grade'] in PASSED_GRADES)

    def total_credits(target):
        """登録済み科目の総単位数（未履修含む）"""
        return sum(s['credits'] for s in target)

    # 区分別に分類
    liberal  = [s for s in subjects if s['category'] == 'liberal']
    major    = [s for s in subjects if s['category'] == 'major']
    required = [s for s in subjects if s['mandatory'] == 'required']
    elective = [s for s in subjects if s['mandatory'] == 'elective']

    return {
        'gpa': {
            'overall': gpa(subjects),
            'liberal': gpa(liberal),
            'major':   gpa(major),
        },
        'earned': {
            'overall':  earned_credits(subjects),
            'liberal':  earned_credits(liberal),
            'major':    earned_credits(major),
            'required': earned_credits(required),
            'elective': earned_credits(elective),
        },
        'registered': {
            'overall':  total_credits(subjects),
            'liberal':  total_credits(liberal),
            'major':    total_credits(major),
            'required': total_credits(required),
            'elective': total_credits(elective),
        }
    }