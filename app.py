from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import date, timedelta
import os
import json

app = Flask(__name__)
DATA_FILE = "habits.json"

# ------------------- データ読み書き関数 ------------------- #
def load_habits():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        for habit in data:
            habit.setdefault("logs", {})
        return data

def save_habits(habits):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(habits, f, ensure_ascii=False, indent=2)

# ------------------- ルーティング ------------------- #
@app.route("/")
def index():
    habits = load_habits()
    today = date.today().isoformat()
    today_obj = date.today()

    total_completed = 0
    total_possible = 0
    top_habit_name = None
    top_habit_count = -1

    for habit in habits:
        habit["total_days"] = sum(1 for log in habit["logs"].values() if log["done"])

        continuous_days = 0
        for i in range(0, 100):
            d = today_obj - timedelta(days=i)
            log = habit["logs"].get(d.isoformat())
            if log and log["done"]:
                continuous_days += 1
            else:
                break
        habit["continuous_days"] = continuous_days

        weekly_count = 0
        for i in range(0, 7):
            d = today_obj - timedelta(days=i)
            log = habit["logs"].get(d.isoformat())
            total_possible += 1
            if log and log["done"]:
                total_completed += 1
                weekly_count += 1

        if weekly_count > top_habit_count:
            top_habit_count = weekly_count
            top_habit_name = habit["name"]

    return render_template("index.html", habits=habits, today=today,
                           completed_count=total_completed,
                           total_count=total_possible,
                           top_habit_name=top_habit_name,
                           top_habit_count=top_habit_count)

@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name")
    reason = request.form.get("reason", "")
    color = request.form.get("color", "#4CAF50")
    if not name:
        return redirect(url_for("index"))
    habits = load_habits()
    habits.append({
        "name": name,
        "reason": reason,
        "color": color,
        "logs": {}
    })
    save_habits(habits)
    return redirect(url_for("index"))

@app.route("/check/<int:index>", methods=["POST"])
def check(index):
    habits = load_habits()
    today = date.today().isoformat()
    habits[index]["logs"][today] = {
        "done": True,
        "reason_for_miss": ""
    }
    save_habits(habits)
    return redirect(url_for("index"))

@app.route("/miss/<int:index>", methods=["POST"])
def miss(index):
    reason = request.form.get("reason", "")
    habits = load_habits()
    today = date.today().isoformat()
    habits[index]["logs"][today] = {
        "done": False,
        "reason_for_miss": reason
    }
    save_habits(habits)
    return redirect(url_for("index"))

@app.route("/delete/<int:index>", methods=["POST"])
def delete(index):
    habits = load_habits()
    habits.pop(index)
    save_habits(habits)
    return redirect(url_for("index"))

@app.route("/detail/<int:index>")
def detail(index):
    habits = load_habits()
    habit = habits[index]
    today = date.today()

    status_list = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        log = habit["logs"].get(d.isoformat())
        mark = "✔" if log and log["done"] else "✘"
        status_list.append(mark)
    status_str = " ".join(status_list)

    recent_miss_reason = ""
    for i in range(0, 7):
        d = today - timedelta(days=i)
        log = habit["logs"].get(d.isoformat())
        if log and not log["done"] and log.get("reason_for_miss"):
            recent_miss_reason = log["reason_for_miss"]
            break

    total_days = sum(1 for log in habit["logs"].values() if log["done"])
    continuous_days = 0
    for i in range(0, 100):
        d = today - timedelta(days=i)
        log = habit["logs"].get(d.isoformat())
        if log and log["done"]:
            continuous_days += 1
        else:
            break

    return render_template("detail.html",
                           habit=habit,
                           status_str=status_str,
                           recent_miss_reason=recent_miss_reason,
                           total_days=total_days,
                           continuous_days=continuous_days)

@app.route("/graph/<int:index>")
def graph(index):
    from calendar import monthrange
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    today = date.today()

    habits = load_habits()
    habit = habits[index]

    if not year or not month:
        year = today.year
        month = today.month

    _, last_day = monthrange(year, month)
    calendar_data = []
    for day in range(1, last_day + 1):
        d = date(year, month, day)
        log = habit["logs"].get(d.isoformat())
        if log:
            status = "done" if log["done"] else "missed"
        else:
            status = "empty"
        calendar_data.append({"day": day, "status": status})

    prev_month = 12 if month == 1 else month - 1
    prev_year = year - 1 if month == 1 else year
    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year

    return render_template("graph.html",
                           habit=habit,
                           index=index,
                           year=year,
                           month=month,
                           calendar_data=calendar_data,
                           prev_year=prev_year,
                           prev_month=prev_month,
                           next_year=next_year,
                           next_month=next_month)

@app.route("/reorder", methods=["POST"])
def reorder():
    order = request.get_json().get("order", [])
    habits = load_habits()
    reordered = [habits[int(i)] for i in order if i.isdigit() and int(i) < len(habits)]
    save_habits(reordered)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
