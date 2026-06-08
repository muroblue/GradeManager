let gpaChart = null;
// シミュレーションテーブルを描画
function renderSimulateTable() {
  const tbody = document.getElementById('simulate-tbody');
  tbody.innerHTML = '';

  const CATEGORY_LABEL = { liberal: '教養', major: '専門' };

  allSubjects.forEach(s => {
    const tr = document.createElement('tr');
    if (!s.grade) tr.classList.add('unregistered');
    tr.innerHTML = `
      <td>${s.name}</td>
      <td>${s.credits}</td>
      <td>${CATEGORY_LABEL[s.category] || s.category}</td>
      <td>${s.grade || '未履修'}</td>
      <td>
        <select class="sim-grade" data-id="${s.id}">
          <option value="">変更なし</option>
          <option value="S">S</option>
          <option value="A">A</option>
          <option value="B">B</option>
          <option value="C">C</option>
          <option value="F">F</option>
          <option value="R">R</option>
        </select>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 試算実行
document.getElementById('simulate-btn').addEventListener('click', async () => {
  const overrides = {};
  document.querySelectorAll('.sim-grade').forEach(sel => {
    if (sel.value) overrides[sel.dataset.id] = sel.value;
  });

  const res = await fetch('/api/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ overrides })
  });
  const data = await res.json();

  document.getElementById('sim-gpa-overall').textContent = data.gpa.overall;
  document.getElementById('sim-gpa-liberal').textContent = data.gpa.liberal;
  document.getElementById('sim-gpa-major').textContent   = data.gpa.major;
  document.getElementById('simulate-result').style.display = 'block';
});
// 卒業要件を読み込んでフォームに反映
async function loadRequirements() {
  const res = await fetch('/api/requirements');
  const req = await res.json();
  document.getElementById('req-total').value    = req.total_credits    || '';
  document.getElementById('req-liberal').value  = req.liberal_credits  || '';
  document.getElementById('req-major').value    = req.major_credits    || '';
  document.getElementById('req-required').value = req.required_credits || '';
}

// 卒業判定を取得して描画
async function loadGraduation() {
  const res  = await fetch('/api/graduation');
  const data = await res.json();

  const banner = document.getElementById('judgment-banner');
  if (data.eligible) {
    banner.textContent = '🎓 卒業要件を満たしています';
    banner.className   = 'judgment-banner eligible';
  } else {
    banner.textContent = '⚠️ 卒業要件を満たしていません';
    banner.className   = 'judgment-banner not-eligible';
  }

  const tbody = document.getElementById('judgment-tbody');
  tbody.innerHTML = '';
  data.checks.forEach(c => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${c.label}</td>
      <td>${c.required}</td>
      <td>${c.earned}</td>
      <td>${c.shortage > 0 ? c.shortage : '-'}</td>
      <td class="${c.passed ? 'check-pass' : 'check-fail'}">
        ${c.passed ? '✅ OK' : '❌ 不足'}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 卒業要件保存
document.getElementById('req-save-btn').addEventListener('click', async () => {
  const body = {
    total_credits:    parseFloat(document.getElementById('req-total').value)    || 0,
    liberal_credits:  parseFloat(document.getElementById('req-liberal').value)  || 0,
    major_credits:    parseFloat(document.getElementById('req-major').value)    || 0,
    required_credits: parseFloat(document.getElementById('req-required').value) || 0,
  };
  await fetch('/api/requirements', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  loadGraduation();
});
// ダッシュボード更新
async function loadSummary() {
  const res = await fetch('/api/summary');
  const data = await res.json();

  // カード更新
  document.getElementById('gpa-overall').textContent   = data.gpa.overall;
  document.getElementById('gpa-liberal').textContent   = data.gpa.liberal;
  document.getElementById('gpa-major').textContent     = data.gpa.major;
  document.getElementById('earned-overall').textContent  = data.earned.overall;
  document.getElementById('earned-liberal').textContent  = data.earned.liberal;
  document.getElementById('earned-major').textContent    = data.earned.major;
  document.getElementById('earned-required').textContent = data.earned.required;
  document.getElementById('earned-elective').textContent = data.earned.elective;

  // GPAグラフ
  const ctx = document.getElementById('gpaChart').getContext('2d');
  if (gpaChart) gpaChart.destroy();
  gpaChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['総合GPA', '教養GPA', '専門GPA'],
      datasets: [{
        label: 'GPA',
        data: [data.gpa.overall, data.gpa.liberal, data.gpa.major],
        backgroundColor: ['#3949ab', '#1e88e5', '#43a047'],
        borderRadius: 6,
      }]
    },
    options: {
      scales: {
        y: {
          min: 0,
          max: 4,
          ticks: { stepSize: 1 }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}
let allSubjects = [];
let editingId = null;

const CATEGORY_LABEL = { liberal: '教養', major: '専門' };
const MANDATORY_LABEL = { required: '必修', elective: '選択' };
const SEMESTER_LABEL = { spring: '前期', fall: '後期' };

// 科目一覧を取得
async function loadSubjects() {
  const res = await fetch('/api/subjects');
  allSubjects = await res.json();
  applyFilter();
  renderSimulateTable();
}

// フィルタ適用して描画
function applyFilter() {
  const cat = document.getElementById('filter-category').value;
  const man = document.getElementById('filter-mandatory').value;
  const grd = document.getElementById('filter-grade').value;

  const filtered = allSubjects.filter(s => {
    if (cat && s.category !== cat) return false;
    if (man && s.mandatory !== man) return false;
    if (grd === 'unregistered' && s.grade !== null) return false;
    if (grd && grd !== 'unregistered' && s.grade !== grd) return false;
    return true;
  });

  renderTable(filtered);
}

// テーブル描画
function renderTable(subjects) {
  const tbody = document.getElementById('subject-tbody');
  const emptyMsg = document.getElementById('empty-msg');
  tbody.innerHTML = '';

  if (subjects.length === 0) {
    emptyMsg.style.display = 'block';
    return;
  }
  emptyMsg.style.display = 'none';

  subjects.forEach(s => {
    const gradeClass = s.grade ? `grade-${s.grade}` : 'grade-none';
    const gradeLabel = s.grade || '未履修';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${s.name}</td>
      <td>${s.credits}</td>
      <td>${CATEGORY_LABEL[s.category] || s.category}</td>
      <td>${MANDATORY_LABEL[s.mandatory] || s.mandatory}</td>
      <td><span class="grade-badge ${gradeClass}">${gradeLabel}</span></td>
      <td>${s.year || '-'}</td>
      <td>${SEMESTER_LABEL[s.semester] || '-'}</td>
      <td>
        <button class="edit-btn" onclick="startEdit(${s.id})">編集</button>
        <button class="delete-btn" onclick="deleteSubject(${s.id})">削除</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 科目登録・更新
document.getElementById('add-btn').addEventListener('click', async () => {
  const name     = document.getElementById('name').value.trim();
  const credits  = document.getElementById('credits').value;
  const category = document.getElementById('category').value;
  const mandatory = document.getElementById('mandatory').value;
  const grade    = document.getElementById('grade').value;
  const year     = document.getElementById('year').value;
  const semester = document.getElementById('semester').value;
  const errorMsg = document.getElementById('error-msg');

  if (!name || !credits || !category || !mandatory) {
    errorMsg.textContent = '科目名・単位数・区分・必修/選択は必須です';
    return;
  }
  errorMsg.textContent = '';

  const body = { name, credits: parseFloat(credits), category, mandatory, grade, year: parseInt(year) || null, semester };

  if (editingId !== null) {
    await fetch(`/api/subjects/${editingId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    editingId = null;
    document.getElementById('add-btn').textContent = '登録';
  } else {
    await fetch('/api/subjects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
  }

  clearForm();
  loadSubjects();
loadSummary();
loadGraduation();
});

// 編集開始
function startEdit(id) {
  const s = allSubjects.find(s => s.id === id);
  if (!s) return;
  document.getElementById('name').value     = s.name;
  document.getElementById('credits').value  = s.credits;
  document.getElementById('category').value = s.category;
  document.getElementById('mandatory').value = s.mandatory;
  document.getElementById('grade').value    = s.grade || '';
  document.getElementById('year').value     = s.year || '';
  document.getElementById('semester').value = s.semester || '';
  document.getElementById('add-btn').textContent = '更新';
  editingId = id;
  document.getElementById('subjects').scrollIntoView({ behavior: 'smooth' });
}

// 削除
async function deleteSubject(id) {
  if (!confirm('削除しますか？')) return;
  await fetch(`/api/subjects/${id}`, { method: 'DELETE' });
  loadSubjects();
loadSummary();
loadGraduation();
}

// フォームリセット
function clearForm() {
  ['name','credits','category','mandatory','grade','year','semester'].forEach(id => {
    document.getElementById(id).value = '';
  });
}

// フィルタ変更時
['filter-category','filter-mandatory','filter-grade'].forEach(id => {
  document.getElementById(id).addEventListener('change', applyFilter);
});

// 初回読み込み
loadSubjects();
loadSummary();
loadRequirements();
loadGraduation();