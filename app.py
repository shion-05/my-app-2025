from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import json
import os
from datetime import datetime, timedelta, date

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# === ユーザーデータの読み書き ===
def load_users():
    if not os.path.exists('users.json'):
        return {}
    with open('users.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# === 習慣データの読み書き ===
def load_data(username):
    path = f'data/{username}_habits.json'
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(username, data):
    os.makedirs('data', exist_ok=True)
    path = f'data/{username}_habits.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === ログイン関連 ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect('/')
        return render_template('login.html', error='ログイン失敗')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# === メイン画面 ===
@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/login')
    username = session['username']
    data = load_data(username)

    today = datetime.today().date()
    week_ago = today - timedelta(days=7)

    completed_count = sum(
        1 for h in data
        for d in h.get('dates', [])
        if week_ago <= datetime.strptime(d, "%Y-%m-%d").date() <= today
    )
    total_count = len(data) * 7

    top_habit_name = ''
    top_habit_count = 0
    for h in data:
        count = sum(
            1 for d in h.get('dates', [])
            if week_ago <= datetime.strptime(d, "%Y-%m-%d").date() <= today
        )
        if count > top_habit_count:
            top_habit_count = count
            top_habit_name = h['name']

    return render_template('index.html', habits=data, completed_count=completed_count, total_count=total_count,
                           top_habit_name=top_habit_name, top_habit_count=top_habit_count)

@app.route('/add', methods=['POST'])
def add():
    if 'username' not in session:
        return redirect('/login')
    username = session['username']
    data = load_data(username)
    name = request.form['name']
    reason = request.form.get('reason', '')
    color = request.form.get('color', '#4CAF50')
    memo = request.form.get('memo', '')
    data.insert(0, {
        'name': name,
        'reason': reason,
        'memo': memo,
        'dates': [],
        'misses': [],
        'color': color,
        'continuous_days': 0,
        'total_days': 0
    })
    save_data(username, data)
    return redirect('/')

@app.route('/check/<int:index>', methods=['POST'])
def check(index):
    username = session['username']
    data = load_data(username)
    today = datetime.today().date().isoformat()
    if today not in data[index]['dates']:
        data[index]['dates'].append(today)
        # もし未達成からの切り替えなら削除
        data[index]['misses'] = [m for m in data[index]['misses'] if m['date'] != today]
        data[index]['continuous_days'] += 1
        data[index]['total_days'] += 1
    save_data(username, data)
    return redirect('/')

@app.route('/miss/<int:index>', methods=['POST'])
def miss(index):
    username = session['username']
    data = load_data(username)
    today = datetime.today().date().isoformat()
    # 既に達成していれば取り消す
    if today in data[index]['dates']:
        data[index]['dates'].remove(today)
        data[index]['total_days'] -= 1
    reason = request.form['reason']
    # 重複しないようにmiss更新
    data[index]['misses'] = [m for m in data[index]['misses'] if m['date'] != today]
    data[index]['misses'].append({'date': today, 'reason': reason})
    data[index]['continuous_days'] = 0
    save_data(username, data)
    return redirect('/')

@app.route('/delete/<int:index>', methods=['POST'])
def delete(index):
    username = session['username']
    data = load_data(username)
    del data[index]
    save_data(username, data)
    return redirect('/')

@app.route('/detail/<int:index>')
def detail(index):
    username = session['username']
    data = load_data(username)
    habit = data[index]

    today = datetime.today().date()
    week_ago = today - timedelta(days=6)

    status_str = ''.join(
        '✔' if (week_ago + timedelta(days=i)).isoformat() in habit['dates'] else '✘'
        for i in range(7)
    )

    recent_miss_reason = habit['misses'][-1]['reason'] if habit['misses'] else ''

    return render_template('detail.html', habit=habit, status_str=status_str,
                           recent_miss_reason=recent_miss_reason,
                           continuous_days=habit['continuous_days'], total_days=habit['total_days'])

@app.route('/graph/<int:index>')
def graph(index):
    username = session['username']
    data = load_data(username)
    habit = data[index]

    today = datetime.today()
    year = int(request.args.get('year', today.year))
    month = int(request.args.get('month', today.month))

    import calendar
    _, last_day = calendar.monthrange(year, month)

    dates_done = set(habit.get('dates', []))
    dates_missed = set(m['date'] for m in habit.get('misses', []))

    calendar_data = []
    for day in range(1, last_day + 1):
        d_str = date(year, month, day).isoformat()
        if d_str in dates_done:
            status = 'done'
        elif d_str in dates_missed:
            status = 'missed'
        else:
            status = 'empty'
        calendar_data.append({'day': day, 'status': status})

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render_template('graph.html', habit=habit, index=index, year=year, month=month,
                           calendar_data=calendar_data, prev_year=prev_year, prev_month=prev_month,
                           next_year=next_year, next_month=next_month)

@app.route('/reorder', methods=['POST'])
def reorder():
    username = session['username']
    order = request.json['order']
    data = load_data(username)
    new_data = [data[int(i)] for i in order if int(i) < len(data)]
    save_data(username, new_data)
    return jsonify({'status': 'ok'})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
