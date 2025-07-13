# habit.py

from datetime import date, timedelta
import json


class DailyLog:
    """
    1日分の記録を管理するクラス
    """
    def __init__(self, date_str, done=False, reason_for_miss=""):
        self.date_str = date_str  # 'YYYY-MM-DD' 形式の文字列
        self.done = done
        self.reason_for_miss = reason_for_miss

    def to_dict(self):
        return {
            "date": self.date_str,
            "done": self.done,
            "reason_for_miss": self.reason_for_miss
        }

    @staticmethod
    def from_dict(data):
        return DailyLog(
            date_str=data["date"],
            done=data["done"],
            reason_for_miss=data["reason_for_miss"]
        )


class Habit:
    """
    習慣（例：水を飲む、日記を書く）を管理するクラス
    """
    def __init__(self, name, reason=""):
        self.name = name
        self.reason = reason
        self.logs = {}  # key: date_str, value: DailyLog

    def check_today(self):
        today_str = date.today().isoformat()
        if today_str not in self.logs:
            self.logs[today_str] = DailyLog(today_str)
        self.logs[today_str].done = True

    def uncheck_today(self):
        today_str = date.today().isoformat()
        if today_str in self.logs:
            self.logs[today_str].done = False

    def set_miss_reason(self, reason_text):
        today_str = date.today().isoformat()

        # すでに達成済みなら、理由だけ記録し、done は変更しない
        if today_str in self.logs and self.logs[today_str].done:
            self.logs[today_str].reason_for_miss = reason_text
            return

        # 未記録 or 未達成 → 新たに記録する
        self.logs[today_str] = DailyLog(
            date_str=today_str,
            done=False,
            reason_for_miss=reason_text
        )


    def get_streak(self):
        """
        今日からさかのぼって連続達成日数をカウントする。
        未達成または記録なしでストリークは終了。
        """
        streak = 0
        current_date = date.today()

        while True:
            date_str = current_date.isoformat()

            if date_str in self.logs:
                log = self.logs[date_str]
                if log.done:
                    streak += 1
                else:
                    break  # 未達成 → 終了
            else:
                break  # 記録なし → 終了

            # 日付を 1日前に更新（正しく上書き）
            current_date = current_date - timedelta(days=1)

        return streak



    def get_total_completed(self):
        return sum(1 for log in self.logs.values() if log.done)

    def to_dict(self):
        return {
            "name": self.name,
            "reason": self.reason,
            "logs": {d: log.to_dict() for d, log in self.logs.items()}
        }
    


    @staticmethod
    def from_dict(data):
        habit = Habit(name=data["name"], reason=data.get("reason", ""))
        habit.logs = {
            d: DailyLog.from_dict(log_data)
            for d, log_data in data.get("logs", {}).items()
        }
        return habit
    
