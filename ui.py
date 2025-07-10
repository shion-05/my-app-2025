# ui.py

import tkinter as tk
from tkinter import messagebox, simpledialog
from habit import Habit
import storage


class HabitTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("習慣トラッカー")
        self.habits = storage.load_habits()

        self.listbox = tk.Listbox(root, width=40, height=10)
        self.listbox.pack(pady=10)

        self.update_listbox()

        # ボタンエリア
        button_frame = tk.Frame(root)
        button_frame.pack()

        tk.Button(button_frame, text="追加", command=self.add_habit).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="達成", command=self.check_habit).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="削除", command=self.delete_habit).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="理由を見る", command=self.show_reason).grid(row=0, column=3, padx=5)
        tk.Button(button_frame, text="未達成理由", command=self.set_miss_reason).grid(row=0, column=4, padx=5)


        # 終了時に保存
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for habit in self.habits:
            streak = habit.get_streak()
            total = habit.get_total_completed()
            self.listbox.insert(tk.END, f"{habit.name}（連続{streak}日 / 合計{total}日）")

    def add_habit(self):
        name = simpledialog.askstring("習慣を追加", "習慣の名前を入力してください：")
        if name:
            reason = simpledialog.askstring("理由", "この習慣を続けたい理由（任意）：")
            self.habits.append(Habit(name=name, reason=reason or ""))
            self.update_listbox()

    def check_habit(self):
        index = self.listbox.curselection()
        if not index:
            messagebox.showwarning("選択してください", "達成する習慣を選んでください。")
            return
        self.habits[index[0]].check_today()
        self.update_listbox()

    def delete_habit(self):
        index = self.listbox.curselection()
        if not index:
            messagebox.showwarning("選択してください", "削除する習慣を選んでください。")
            return
        habit = self.habits.pop(index[0])
        messagebox.showinfo("削除", f"『{habit.name}』を削除しました。")
        self.update_listbox()

    def on_close(self):
        storage.save_habits(self.habits)
        self.root.destroy()

    def show_reason(self):
        index = self.listbox.curselection()
        if not index:
            messagebox.showwarning("選択してください", "理由を確認したい習慣を選んでください。")
            return
        habit = self.habits[index[0]]
        reason = habit.reason.strip()
        if reason:
            messagebox.showinfo(f"『{habit.name}』のやる理由", reason)
        else:
            messagebox.showinfo(f"『{habit.name}』のやる理由", "理由は登録されていません。")

    def set_miss_reason(self):
        index = self.listbox.curselection()
        if not index:
            messagebox.showwarning("選択してください", "未達成の習慣を選んでください。")
            return
        reason = simpledialog.askstring("未達成の理由", "今日はなぜ実行できなかったのですか？")
        if reason is None or reason.strip() == "":
            messagebox.showinfo("未入力", "理由が入力されなかったため記録されませんでした。")
            return
        self.habits[index[0]].set_miss_reason(reason)
        messagebox.showinfo("記録完了", "未達成の理由を記録しました。")
        self.update_listbox()



def run_gui():
    root = tk.Tk()
    app = HabitTrackerApp(root)
    root.mainloop()
