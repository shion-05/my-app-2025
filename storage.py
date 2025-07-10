# storage.py

import json
import os
from habit import Habit


DATA_FILE = "habits.json"  # 保存するファイル名


def save_habits(habit_list):
    """
    習慣のリストをJSON形式で保存する
    """
    data = [habit.to_dict() for habit in habit_list]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_habits():
    """
    JSONファイルから習慣のリストを読み込む
    """
    if not os.path.exists(DATA_FILE):
        return []
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [Habit.from_dict(h) for h in data]
