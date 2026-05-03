#!/usr/bin/env python3
"""
双色球预测程序 - GUI图形界面
基于tkinter构建
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import os
from datetime import datetime
from collections import Counter

try:
    from ssqcore.data import parse_lottery_data, fetch_latest_lottery_data
    from ssqcore.analysis import (
        frequency_analysis, missing_analysis, hot_cold_analysis,
        zone_analysis, odd_even_analysis, sum_analysis,
        consecutive_analysis, repeat_analysis
    )
    from ssqcore.strategy import random_strategy, hot_cold_strategy
except ImportError as e:
    messagebox.showerror("导入错误", f"无法导入 ssqcore 模块：{e}")
    raise

class SSQGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("双色球智能分析与预测 V4.5")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        self.records = []
        self.prediction_history = []
        self.data_file = "2013-2026.txt"

        self._setup_styles()
        self._create_menu()
        self._create_main_layout()
        self._load_data()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Title.TLabel", font=("Microsoft YaHei", 14, "bold"))
        style.configure("Header.TLabel", font=("Microsoft YaHei", 11, "bold"))
        style.configure("Red.TLabel", foreground="#D32F2F", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Blue.TLabel", foreground="#1565C0", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Prediction.TLabel", font=("Microsoft YaHei", 12, "bold"))

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="加载数据文件", command=self._load_data_file)
        file_menu.add_command(label="保存预测结果", command=self._save_prediction)
        file_menu.add_command(label="查看历史记录", command=self._view_history)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="数据", menu=data_menu)
        data_menu.add_command(label="在线更新数据", command=self._update_data_online)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)

    def _create_main_layout(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.N, tk.S), padx=(0, 10))

        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        self._create_control_panel(left_frame)
        self._create_prediction_display(left_frame)
        self._create_analysis_display(right_frame)

        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X)

    def _create_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(control_frame, text="数据文件：").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.data_file_var = tk.StringVar(value=self.data_file)
        ttk.Entry(control_frame, textvariable=self.data_file_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="加载", command=self._load_data).grid(row=0, column=2, pady=5)

        ttk.Separator(control_frame, orient=tk.HORIZONTAL).grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(control_frame, text="选择策略：").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.strategy_var = tk.StringVar(value="default")
        strategy_frame = ttk.Frame(control_frame)
        strategy_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Radiobutton(strategy_frame, text="智能策略", variable=self.strategy_var, value="default").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(strategy_frame, text="随机策略", variable=self.strategy_var, value="random").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(strategy_frame, text="冷热策略", variable=self.strategy_var, value="hotcold").pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="开始预测", command=self._start_prediction, style="Accent.TButton").grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        ttk.Separator(control_frame, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        history_frame = ttk.Frame(control_frame)
        history_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(history_frame, text="历史回测(5期)", command=lambda: self._start_prediction(backtest=5)).pack(side=tk.LEFT, padx=2)
        ttk.Button(history_frame, text="批量预测(3期)", command=lambda: self._start_prediction(batch=3)).pack(side=tk.LEFT, padx=2)

        info_frame = ttk.Frame(control_frame)
        info_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.info_var = tk.StringVar(value="未加载数据")
        ttk.Label(info_frame, textvariable=self.info_var).pack()

    def _create_prediction_display(self, parent):
        pred_frame = ttk.LabelFrame(parent, text="预测结果", padding="10")
        pred_frame.pack(fill=tk.BOTH, expand=True)

        red_frame = ttk.Frame(pred_frame)
        red_frame.pack(fill=tk.X, pady=5)
        ttk.Label(red_frame, text="红球：", style="Red.TLabel").pack(side=tk.LEFT)
        self.red_labels = []
        for i in range(6):
            label = ttk.Label(red_frame, text="--", width=4, font=("Microsoft YaHei", 12, "bold"), foreground="#D32F2F")
            label.pack(side=tk.LEFT, padx=2)
            self.red_labels.append(label)

        blue_frame = ttk.Frame(pred_frame)
        blue_frame.pack(fill=tk.X, pady=5)
        ttk.Label(blue_frame, text="蓝球：", style="Blue.TLabel").pack(side=tk.LEFT)
        self.blue_label = ttk.Label(blue_frame, text="--", width=4, font=("Microsoft YaHei", 12, "bold"), foreground="#1565C0")
        self.blue_label.pack(side=tk.LEFT, padx=2)

        ttk.Separator(pred_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        button_frame = ttk.Frame(pred_frame)
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="保存结果", command=self._save_prediction).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="查看历史", command=self._view_history).pack(side=tk.LEFT, padx=2)

        disclaimer = ttk.Label(pred_frame, text="彩票开奖为随机事件，本预测仅供娱乐参考，请理性购彩！",
                             foreground="gray", font=("Microsoft YaHei", 8))
        disclaimer.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

    def _create_analysis_display(self, parent):
        self.analysis_text = scrolledtext.ScrolledText(parent, height=30, width=60,
                                                        font=("Consolas", 10), wrap=tk.WORD)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)

    def _load_data(self):
        try:
            if not os.path.exists(self.data_file):
                self.data_file = filedialog.askopenfilename(title="选择数据文件",
                                                              filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")])
                if not self.data_file:
                    return
                self.data_file_var.set(self.data_file)

            self.records = parse_lottery_data(self.data_file)
            if self.records:
                self.info_var.set(f"已加载 {len(self.records)} 期数据 ({self.records[0]['issue']} - {self.records[-1]['issue']})")
                self.status_var.set(f"数据加载成功：{len(self.records)} 期")
            else:
                messagebox.showwarning("警告", "未能解析到有效数据")
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败：{e}")

    def _load_data_file(self):
        file_path = filedialog.askopenfilename(title="选择数据文件",
                                               filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")])
        if file_path:
            self.data_file = file_path
            self.data_file_var.set(file_path)
            self._load_data()

    def _start_prediction(self, backtest=0, batch=0):
        if not self.records:
            messagebox.showwarning("警告", "请先加载数据")
            return

        def run_prediction():
            try:
                strategy = self.strategy_var.get()
                self.status_var.set("正在预测...")

                if backtest > 0:
                    result = self._run_backtest(backtest)
                elif batch > 0:
                    result = self._run_batch(batch)
                else:
                    result = self._single_prediction(strategy)

                self._update_display(result)
                self.status_var.set("预测完成")
            except Exception as e:
                self.status_var.set(f"预测失败：{e}")
                messagebox.showerror("错误", f"预测失败：{e}")

        thread = threading.Thread(target=run_prediction)
        thread.daemon = True
        thread.start()

    def _single_prediction(self, strategy):
        if strategy == 'random':
            red, blue = random_strategy()
            analysis = "【随机策略】纯概率选号\n"
        elif strategy == 'hotcold':
            red, blue = hot_cold_strategy(self.records)
            analysis = "【冷热号策略】热号+冷号混合\n"
        else:
            red, blue = self._predict_with_analysis()
            analysis = self._generate_analysis_report()

        prediction = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'strategy': strategy,
            'red': red,
            'blue': blue,
            'analysis': analysis
        }
        self.prediction_history.append(prediction)
        return prediction

    def _predict_with_analysis(self):
        red_freq, blue_freq = frequency_analysis(self.records)
        red_missing, blue_missing = missing_analysis(self.records)
        hot_cold = hot_cold_analysis(self.records, 30)
        zone_ratio = zone_analysis(self.records, 50)
        avg_odd = odd_even_analysis(self.records, 50)
        avg_sum, _, _ = sum_analysis(self.records, 100)

        red = self._generate_red_balls(red_freq, red_missing, hot_cold, zone_ratio, avg_odd, avg_sum)
        blue = self._generate_blue_ball(blue_freq, blue_missing, hot_cold)
        return red, blue

    def _generate_red_balls(self, red_freq, red_missing, hot_cold, zone_ratio, avg_odd, avg_sum):
        candidates = []
        max_freq = max(red_freq.values()) if red_freq else 1

        for num in range(1, 34):
            score = (red_freq.get(num, 0) / max_freq * 30 +
                    min(red_missing[num], 20) * 1.5 +
                    (15 if num in hot_cold['hot_red'] else 10 if num in hot_cold['warm_red'] else 5))
            candidates.append((num, score))

        candidates.sort(key=lambda x: x[1], reverse=True)

        selected = []
        zone_target = [round(zone_ratio[i] * 6) for i in range(3)]
        while sum(zone_target) != 6:
            if sum(zone_target) < 6:
                zone_target[zone_ratio.index(max(zone_ratio))] += 1
            else:
                zone_target[zone_ratio.index(min(zone_ratio))] -= 1

        zone_count = [0, 0, 0]
        odd_count = 0
        target_odd = round(avg_odd)

        for num, score in candidates:
            if len(selected) >= 6:
                break
            zone = 0 if num <= 11 else 1 if num <= 22 else 2
            if zone_count[zone] >= zone_target[zone]:
                continue
            is_odd = num % 2 == 1
            if is_odd and odd_count >= target_odd:
                continue
            if not is_odd and (len(selected) - odd_count) >= (6 - target_odd):
                continue
            selected.append(num)
            zone_count[zone] += 1
            if is_odd:
                odd_count += 1

        for num, score in candidates:
            if len(selected) >= 6:
                break
            if num not in selected:
                selected.append(num)

        return selected[:6]

    def _generate_blue_ball(self, blue_freq, blue_missing, hot_cold):
        candidates = []
        max_freq = max(blue_freq.values()) if blue_freq else 1

        for num in range(1, 17):
            score = (blue_freq.get(num, 0) / max_freq * 40 +
                    min(blue_missing[num], 15) * 2 +
                    (20 if num in hot_cold['hot_blue'] else 0))
            candidates.append((num, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _generate_analysis_report(self):
        report = []
        report.append("=" * 50)
        report.append("双色球预测分析报告")
        report.append("=" * 50)
        report.append(f"分析数据：共 {len(self.records)} 期历史开奖记录")
        report.append(f"最新一期：{self.records[-1]['issue']} ({self.records[-1]['date']})")
        report.append(f"开奖号码：红球 {self.records[-1]['red']} 蓝球 {self.records[-1]['blue']}")
        report.append("")

        red_freq, blue_freq = frequency_analysis(self.records)
        red_top10 = sorted(range(1, 34), key=lambda x: red_freq.get(x, 0), reverse=True)[:10]
        blue_top5 = sorted(range(1, 17), key=lambda x: blue_freq.get(x, 0), reverse=True)[:5]
        report.append("【一、频率分析】")
        report.append(f"红球出现最多的10个号码：{red_top10}")
        report.append(f"蓝球出现最多的5个号码：{blue_top5}")
        report.append("")

        red_missing, blue_missing = missing_analysis(self.records)
        red_high_missing = sorted(range(1, 34), key=lambda x: red_missing[x], reverse=True)[:10]
        blue_high_missing = sorted(range(1, 17), key=lambda x: blue_missing[x], reverse=True)[:5]
        report.append("【二、遗漏分析】")
        report.append(f"红球遗漏值最高的10个号码：{red_high_missing}")
        report.append(f"  对应遗漏值：{[red_missing[n] for n in red_high_missing]}")
        report.append(f"蓝球遗漏值最高的5个号码：{blue_high_missing}")
        report.append("")

        hot_cold = hot_cold_analysis(self.records, 30)
        report.append("【三、冷热分析（近30期）】")
        report.append(f"热号：{sorted(hot_cold['hot_red'])}")
        report.append(f"温号：{sorted(hot_cold['warm_red'])}")
        report.append(f"冷号：{sorted(hot_cold['cold_red'])}")
        report.append("")

        zone_ratio = zone_analysis(self.records, 50)
        report.append("【四、区间分析（近50期）】")
        report.append(f"一区(01-11)占比：{zone_ratio[0]:.1%}")
        report.append(f"二区(12-22)占比：{zone_ratio[1]:.1%}")
        report.append(f"三区(23-33)占比：{zone_ratio[2]:.1%}")
        report.append("")

        avg_odd = odd_even_analysis(self.records, 50)
        report.append("【五、奇偶分析（近50期）】")
        report.append(f"平均每期奇数个数：{avg_odd:.2f}")
        report.append(f"建议奇偶比：{round(avg_odd)}:{6-round(avg_odd)}")
        report.append("")

        avg_sum, min_sum, max_sum = sum_analysis(self.records, 100)
        report.append("【六、和值分析（近100期）】")
        report.append(f"平均和值：{avg_sum:.1f}")
        report.append(f"和值范围：{min_sum} - {max_sum}")
        report.append("")

        avg_consecutive = consecutive_analysis(self.records, 30)
        report.append("【七、连号分析（近30期）】")
        report.append(f"平均每期连号组数：{avg_consecutive:.2f}")
        report.append("")

        avg_repeat = repeat_analysis(self.records, 10)
        report.append("【八、重复号码分析（近10期）】")
        report.append(f"平均每期与上期重复号码数：{avg_repeat:.2f}")
        report.append("=" * 50)

        return "\n".join(report)

    def _run_backtest(self, count):
        if len(self.records) < count + 1:
            messagebox.showwarning("警告", "数据量不足，无法回测")
            return None

        results = []
        report = ["=" * 50, f"历史回测 - 最近 {count} 期", "=" * 50]

        for i in range(count):
            train_data = self.records[:-(count - i)]
            actual = self.records[-(count - i)]

            if not train_data:
                continue

            red, blue = self._predict_with_analysis()
            red_match = len(set(red) & set(actual['red']))
            blue_match = 1 if blue == actual['blue'] else 0

            results.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'strategy': 'backtest',
                'red': red,
                'blue': blue,
                'actual': actual
            })

            report.append(f"期号 {actual['issue']}: 预测红球{red}蓝球{blue}")
            report.append(f"  实际：红球{actual['red']}蓝球{actual['blue']} | 命中红球{red_match}个，蓝球{blue_match}个")

        avg_red = sum(len(set(r['red']) & set(self.records[-count:]['red'])) for r in results) / count
        avg_blue = sum(1 if r['blue'] == self.records[-count:]['blue'] else 0 for r in results) / count
        report.append("=" * 50)
        report.append(f"回测结果：平均命中红球 {avg_red:.2f} 个，蓝球 {avg_blue:.2f} 个")

        self.prediction_history.extend(results)
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'strategy': 'backtest',
            'red': results[-1]['red'] if results else [],
            'blue': results[-1]['blue'] if results else 0,
            'analysis': "\n".join(report)
        }

    def _run_batch(self, count):
        results = []
        report = ["=" * 50, f"批量预测 - 共 {count} 期", "=" * 50]

        for i in range(count):
            red, blue = self._predict_with_analysis()
            results.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'strategy': 'batch',
                'red': red,
                'blue': blue
            })
            report.append(f"第 {i + 1} 期：红球 {red} 蓝球 {blue}")

        self.prediction_history.extend(results)
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'strategy': 'batch',
            'red': results[-1]['red'] if results else [],
            'blue': results[-1]['blue'] if results else 0,
            'analysis': "\n".join(report)
        }

    def _update_display(self, result):
        if not result:
            return

        for i, num in enumerate(result['red'][:6]):
            self.red_labels[i].config(text=f"{num:02d}")
        self.blue_label.config(text=f"{result['blue']:02d}")

        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, result.get('analysis', ''))

    def _save_prediction(self):
        if not self.prediction_history:
            messagebox.showwarning("警告", "没有可保存的预测记录")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存预测结果",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.prediction_history, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"预测结果已保存到：\n{file_path}")
                self.status_var.set(f"已保存到 {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{e}")

    def _view_history(self):
        if not self.prediction_history:
            messagebox.showinfo("提示", "暂无预测历史记录")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("预测历史记录")
        history_window.geometry("600x400")

        text = scrolledtext.ScrolledText(history_window, font=("Consolas", 9), wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for i, pred in enumerate(self.prediction_history[-20:], 1):
            text.insert(tk.END, f"{i}. [{pred['timestamp']}] [{pred['strategy']}]\n")
            text.insert(tk.END, f"   红球：{pred['red']}  蓝球：{pred['blue']}\n\n")

        btn_frame = ttk.Frame(history_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="导出历史", command=lambda: self._export_history(history_window)).pack(side=tk.RIGHT)

    def _export_history(self, window):
        if not self.prediction_history:
            return
        file_path = filedialog.asksaveasfilename(title="导出历史记录",
                                                  defaultextension=".json",
                                                  filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.prediction_history, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"历史记录已导出到：\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{e}")

    def _update_data_online(self):
        def fetch_data():
            try:
                self.status_var.set("正在下载最新数据...")
                success = fetch_latest_lottery_data()
                if success:
                    self.data_file = 'lottery_data.csv'
                    self.data_file_var.set(self.data_file)
                    self._load_data()
                    messagebox.showinfo("成功", "数据更新成功！")
                else:
                    messagebox.showwarning("警告", "数据更新失败，请检查网络连接")
                    self.status_var.set("数据更新失败")
            except Exception as e:
                messagebox.showerror("错误", f"更新失败：{e}")

        thread = threading.Thread(target=fetch_data)
        thread.daemon = True
        thread.start()

    def _show_help(self):
        help_text = """
双色球智能分析与预测 - 使用说明

【功能特性】
1. 智能策略：基于频率、遗漏、冷热、区间、奇偶、和值等分析方法综合预测
2. 随机策略：纯概率随机选号
3. 冷热策略：热号与冷号混合搭配

【使用步骤】
1. 点击"加载"按钮加载历史数据文件
2. 选择预测策略
3. 点击"开始预测"获取预测结果
4. 可选择"历史回测"或"批量预测"

【数据保存】
- 点击"保存结果"可保存当前预测到文件
- 点击"查看历史"可查看所有预测记录
- 预测历史会自动记录，可随时导出

【其他功能】
- 文件菜单：加载数据文件、保存预测结果
- 数据菜单：在线更新最新数据
        """
        messagebox.showinfo("使用说明", help_text)

    def _show_about(self):
        messagebox.showinfo("关于",
                           "双色球智能分析与预测 V4.5\n\n"
                           "基于历史数据统计分析的预测工具\n"
                           "仅供娱乐参考，请理性购彩！\n\n"
                           "2026")

def main():
    root = tk.Tk()
    app = SSQGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()