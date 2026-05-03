# -*- coding: utf-8 -*-
"""
中国福利彩票双色球智能预测系统 V3.0 (反作弊增强版)
=====================================

【免责声明】
本程序仅供学习和娱乐目的，彩票本质上是随机事件，
任何预测方法都无法保证中奖。请理性购彩，量力而行。

【双色球规则】
- 红球：从01-33中选6个（不重复）
- 蓝球：从01-16中选1个

【V3.0 新增功能 - 反作弊增强】
1. 冷门号码分析（基于购买行为心理学）
2. 反作弊预测策略（假设开冷门号码）
3. 冷门特征检测（检测历史异常）
4. 购买行为模拟分析
5. 号码"冷门度"评分系统

【作弊假设】
福利彩票部门在停止购买后，统计出最少人买的号码组合，
然后开出该号码以最小化赔付。

【冷门号码特征】（大众心理学）
1. 连续号码（如01,02,03,04,05,06）- 人们认为"不可能"
2. 全大号或全小号 - 人们偏好均匀分布
3. 全奇或全偶 - 人们偏好奇偶平衡
4. 同尾号过多 - 人们避免重复尾数
5. 边缘号码（01,02,32,33）- 人们偏好中间号码
6. 近期热门号码的反面 - 人们追热号
7. AC值极低的组合 - 看起来"不随机"

Author: AI Assistant
Date: 2026-01-15
Version: 3.0 Anti-Cheat Enhanced
"""

import re
import os
import csv
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from itertools import combinations


class LotteryDataLoader:
    """数据加载器 - 支持多种格式"""
    
    @staticmethod
    def load_txt(filepath: str) -> List[Tuple]:
        """加载TXT格式数据"""
        history = []
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) < 3:
                continue
            issue = parts[0]
            date = parts[1]
            numbers = parts[2]
            nums = numbers.split('+')
            if len(nums) == 7:
                red_balls = sorted([int(n) for n in nums[:6]])
                blue_ball = int(nums[6])
                history.append((issue, date, red_balls, blue_ball, None, None, None))
        return history
    
    @staticmethod
    def load_csv(filepath: str) -> List[Tuple]:
        """加载CSV格式数据（包含销售额、奖池等信息）"""
        history = []
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    issue = row['期号'].strip()
                    date = row['开奖日期'].strip()
                    red_balls = sorted([
                        int(row['红球1'].strip()), int(row['红球2'].strip()), int(row['红球3'].strip()),
                        int(row['红球4'].strip()), int(row['红球5'].strip()), int(row['红球6'].strip())
                    ])
                    blue_ball = int(row['蓝球'].strip())
                    sales_str = row.get('销售额(元)', '').strip()
                    pool_str = row.get('奖池金额(元)', '').strip()
                    prize_str = row.get('一等奖注数', '').strip()
                    sales = int(sales_str) if sales_str and sales_str.isdigit() else None
                    pool = int(pool_str) if pool_str and pool_str.isdigit() else None
                    first_prize_count = int(prize_str) if prize_str and prize_str.isdigit() else None
                    history.append((issue, date, red_balls, blue_ball, sales, pool, first_prize_count))
                except (KeyError, ValueError, AttributeError):
                    continue
        return history
    
    @staticmethod
    def auto_load(filepath: str) -> List[Tuple]:
        """自动检测格式并加载"""
        if filepath.endswith('.csv'):
            return LotteryDataLoader.load_csv(filepath)
        else:
            return LotteryDataLoader.load_txt(filepath)


class ColdNumberAnalyzer:
    """冷门号码分析器 - V3.0核心新增模块
    
    基于购买行为心理学分析哪些号码组合最少人买
    """
    
    def __init__(self, history: List[Tuple]):
        self.history = history
        self.red_range = range(1, 34)
        self.blue_range = range(1, 17)
    
    def calculate_coldness_score(self, reds: List[int], blue: int) -> Tuple[float, Dict]:
        """
        计算号码组合的"冷门度"得分
        
        得分越高，表示越少人会购买这个组合
        
        返回：(总冷门度得分, 各项得分明细)
        """
        scores = {}
        reds = sorted(reds)
        
        # 1. 连号惩罚（连号越多，越冷门）
        consecutive_count = sum(1 for i in range(5) if reds[i+1] - reds[i] == 1)
        scores['consecutive'] = consecutive_count * 15  # 每组连号+15分
        
        # 2. 全大/全小惩罚
        small_count = sum(1 for r in reds if r <= 16)
        large_count = 6 - small_count
        if small_count == 6 or large_count == 6:
            scores['size_extreme'] = 30
        elif small_count <= 1 or large_count <= 1:
            scores['size_extreme'] = 15
        else:
            scores['size_extreme'] = 0
        
        # 3. 全奇/全偶惩罚
        odd_count = sum(1 for r in reds if r % 2 == 1)
        even_count = 6 - odd_count
        if odd_count == 6 or even_count == 6:
            scores['odd_even_extreme'] = 25
        elif odd_count <= 1 or even_count <= 1:
            scores['odd_even_extreme'] = 12
        else:
            scores['odd_even_extreme'] = 0
        
        # 4. 同尾号惩罚
        tails = [r % 10 for r in reds]
        tail_counter = Counter(tails)
        max_same_tail = max(tail_counter.values())
        scores['same_tail'] = (max_same_tail - 1) * 10  # 2个同尾+10，3个+20...
        
        # 5. 边缘号码奖励（边缘号码冷门）
        edge_numbers = {1, 2, 3, 32, 33}
        edge_count = sum(1 for r in reds if r in edge_numbers)
        scores['edge_bonus'] = edge_count * 8
        
        # 6. AC值惩罚（AC值低=看起来不随机=冷门）
        differences = set()
        for i in range(len(reds)):
            for j in range(i + 1, len(reds)):
                differences.add(abs(reds[i] - reds[j]))
        ac_value = len(differences) - 5
        if ac_value <= 3:
            scores['low_ac'] = 20
        elif ac_value <= 5:
            scores['low_ac'] = 10
        else:
            scores['low_ac'] = 0
        
        # 7. 区间集中惩罚
        z1 = sum(1 for r in reds if 1 <= r <= 11)
        z2 = sum(1 for r in reds if 12 <= r <= 22)
        z3 = sum(1 for r in reds if 23 <= r <= 33)
        if z1 == 0 or z2 == 0 or z3 == 0:
            scores['zone_empty'] = 15
        elif max(z1, z2, z3) >= 4:
            scores['zone_empty'] = 8
        else:
            scores['zone_empty'] = 0
        
        # 8. 跨度异常惩罚
        span = max(reds) - min(reds)
        if span <= 15:
            scores['span_small'] = 20
        elif span >= 30:
            scores['span_large'] = 10
        else:
            scores['span_small'] = 0
            scores['span_large'] = 0
        
        # 9. 蓝球冷门度（边缘蓝球更冷门）
        if blue in [1, 16]:
            scores['blue_edge'] = 10
        elif blue in [2, 15]:
            scores['blue_edge'] = 5
        else:
            scores['blue_edge'] = 0
        
        # 10. 和值异常
        total_sum = sum(reds)
        if total_sum < 60 or total_sum > 140:
            scores['sum_extreme'] = 15
        elif total_sum < 80 or total_sum > 120:
            scores['sum_extreme'] = 5
        else:
            scores['sum_extreme'] = 0
        
        total_coldness = sum(scores.values())
        return total_coldness, scores

    def analyze_historical_coldness(self) -> Dict:
        """分析历史开奖号码的冷门度分布"""
        print("\n" + "=" * 60)
        print("【反作弊分析1】历史开奖号码冷门度分析")
        print("=" * 60)
        
        coldness_scores = []
        high_coldness_draws = []
        
        for item in self.history:
            reds = item[2]
            blue = item[3]
            coldness, details = self.calculate_coldness_score(reds, blue)
            coldness_scores.append(coldness)
            
            if coldness >= 50:  # 高冷门度阈值
                high_coldness_draws.append((item[0], item[1], reds, blue, coldness, details))
        
        avg_coldness = sum(coldness_scores) / len(coldness_scores)
        max_coldness = max(coldness_scores)
        min_coldness = min(coldness_scores)
        
        # 统计冷门度分布
        coldness_dist = Counter()
        for c in coldness_scores:
            bucket = (c // 20) * 20
            coldness_dist[bucket] += 1
        
        print(f"历史开奖冷门度统计（共{len(self.history)}期）：")
        print(f"  平均冷门度：{avg_coldness:.1f}")
        print(f"  最高冷门度：{max_coldness}")
        print(f"  最低冷门度：{min_coldness}")
        
        print("\n冷门度分布：")
        for bucket in sorted(coldness_dist.keys()):
            count = coldness_dist[bucket]
            pct = count / len(self.history) * 100
            bar = '█' * int(pct)
            print(f"  {bucket:3d}-{bucket+19:3d}: {count:4d}次 ({pct:5.1f}%) {bar}")
        
        print(f"\n高冷门度开奖（≥50分）：{len(high_coldness_draws)}次 ({len(high_coldness_draws)/len(self.history)*100:.1f}%)")
        
        if high_coldness_draws:
            print("\n最近5次高冷门度开奖：")
            for item in high_coldness_draws[-5:]:
                issue, date, reds, blue, coldness, details = item
                red_str = '+'.join(f'{r:02d}' for r in reds)
                print(f"  {issue} ({date}): {red_str}+{blue:02d} 冷门度={coldness}")
                # 显示主要冷门因素
                main_factors = sorted(details.items(), key=lambda x: x[1], reverse=True)[:3]
                factors_str = ', '.join(f"{k}:{v}" for k, v in main_factors if v > 0)
                print(f"    主要因素: {factors_str}")
        
        return {
            'avg_coldness': avg_coldness,
            'max_coldness': max_coldness,
            'min_coldness': min_coldness,
            'distribution': dict(coldness_dist),
            'high_coldness_count': len(high_coldness_draws)
        }
    
    def detect_coldness_anomaly(self) -> Dict:
        """检测冷门号码中奖异常"""
        print("\n" + "=" * 60)
        print("【反作弊分析2】冷门号码中奖率异常检测")
        print("=" * 60)
        
        # 分析一等奖注数与冷门度的关系
        prize_coldness_data = []
        for item in self.history:
            if len(item) > 6 and item[6] is not None:
                reds = item[2]
                blue = item[3]
                coldness, _ = self.calculate_coldness_score(reds, blue)
                first_prize_count = item[6]
                prize_coldness_data.append((coldness, first_prize_count))
        
        if len(prize_coldness_data) < 50:
            print("一等奖数据不足，跳过此检测")
            return {}
        
        # 按冷门度分组统计平均一等奖注数
        low_coldness = [p for c, p in prize_coldness_data if c < 30]
        mid_coldness = [p for c, p in prize_coldness_data if 30 <= c < 60]
        high_coldness = [p for c, p in prize_coldness_data if c >= 60]
        
        avg_low = sum(low_coldness) / len(low_coldness) if low_coldness else 0
        avg_mid = sum(mid_coldness) / len(mid_coldness) if mid_coldness else 0
        avg_high = sum(high_coldness) / len(high_coldness) if high_coldness else 0
        
        print("冷门度与一等奖注数关系：")
        print(f"  低冷门度(<30): 平均{avg_low:.1f}注/期 ({len(low_coldness)}期)")
        print(f"  中冷门度(30-60): 平均{avg_mid:.1f}注/期 ({len(mid_coldness)}期)")
        print(f"  高冷门度(≥60): 平均{avg_high:.1f}注/期 ({len(high_coldness)}期)")
        
        # 检测异常
        if avg_high < avg_low * 0.5 and len(high_coldness) >= 10:
            print("\n⚠️ 异常检测：高冷门度开奖的一等奖注数显著偏低")
            print("   这可能支持'开冷门号码减少赔付'的假设")
            anomaly = True
        else:
            print("\n✓ 未发现明显异常")
            anomaly = False
        
        return {
            'avg_low': avg_low,
            'avg_mid': avg_mid,
            'avg_high': avg_high,
            'anomaly_detected': anomaly
        }
    
    def generate_cold_predictions(self, n: int = 5) -> List[Tuple]:
        """生成冷门号码预测（反作弊策略）"""
        print("\n" + "=" * 60)
        print("【反作弊预测】冷门号码组合生成")
        print("=" * 60)
        
        print("【策略原理】")
        print("假设彩票中心会选择最少人买的号码开奖")
        print("我们生成具有'冷门特征'但仍合理的号码组合")
        print()
        
        predictions = []
        attempts = 0
        max_attempts = 5000
        
        while len(predictions) < n and attempts < max_attempts:
            attempts += 1
            
            # 策略1：包含连号
            if len(predictions) < 2:
                start = random.randint(1, 28)
                consecutive = [start, start+1]
                remaining = [r for r in self.red_range if r not in consecutive]
                others = random.sample(remaining, 4)
                reds = sorted(consecutive + others)
            
            # 策略2：偏向边缘号码
            elif len(predictions) < 3:
                edge = random.sample([1, 2, 3, 32, 33], 2)
                remaining = [r for r in self.red_range if r not in edge]
                others = random.sample(remaining, 4)
                reds = sorted(edge + others)
            
            # 策略3：偏向同尾号
            elif len(predictions) < 4:
                tail = random.randint(0, 9)
                same_tail = [r for r in self.red_range if r % 10 == tail]
                if len(same_tail) >= 2:
                    selected_tail = random.sample(same_tail, 2)
                    remaining = [r for r in self.red_range if r not in selected_tail]
                    others = random.sample(remaining, 4)
                    reds = sorted(selected_tail + others)
                else:
                    continue
            
            # 策略4：区间不均匀
            else:
                zone = random.choice([1, 2, 3])
                if zone == 1:
                    zone_nums = [r for r in range(1, 12)]
                elif zone == 2:
                    zone_nums = [r for r in range(12, 23)]
                else:
                    zone_nums = [r for r in range(23, 34)]
                
                from_zone = random.sample(zone_nums, 3)
                remaining = [r for r in self.red_range if r not in from_zone]
                others = random.sample(remaining, 3)
                reds = sorted(from_zone + others)
            
            # 选择边缘蓝球
            blue = random.choice([1, 2, 15, 16])
            
            # 计算冷门度
            coldness, details = self.calculate_coldness_score(reds, blue)
            
            # 只接受冷门度适中的组合（太极端也不好）
            if 40 <= coldness <= 80 and (reds, blue) not in [(p[0], p[1]) for p in predictions]:
                predictions.append((reds, blue, coldness, details))
        
        print("【冷门预测结果】")
        for i, (reds, blue, coldness, details) in enumerate(predictions, 1):
            red_str = '+'.join(f'{r:02d}' for r in reds)
            main_factors = sorted(details.items(), key=lambda x: x[1], reverse=True)[:3]
            factors_str = ', '.join(f"{k}" for k, v in main_factors if v > 0)
            print(f"  第{i}组：红球 {red_str} | 蓝球 {blue:02d} | 冷门度={coldness}")
            print(f"         冷门因素: {factors_str}")
        
        return [(reds, blue) for reds, blue, _, _ in predictions]


class StatisticalTests:
    """统计检验模块 - 用于作弊检测"""
    
    @staticmethod
    def chi_square_test(observed: Dict[int, int], expected_freq: float, total: int) -> Tuple[float, bool]:
        """卡方检验 - 检测号码分布是否符合随机"""
        chi_square = 0
        expected = expected_freq * total
        
        for num, count in observed.items():
            chi_square += (count - expected) ** 2 / expected
        
        df = len(observed) - 1
        critical_value = df + 2 * math.sqrt(2 * df)
        is_random = chi_square < critical_value
        return chi_square, is_random
    
    @staticmethod
    def runs_test(sequence: List[int], median: float) -> Tuple[int, float, bool]:
        """游程检验 - 检测序列是否独立随机"""
        binary = [1 if x > median else 0 for x in sequence]
        
        runs = 1
        for i in range(1, len(binary)):
            if binary[i] != binary[i-1]:
                runs += 1
        
        n1 = sum(binary)
        n2 = len(binary) - n1
        
        if n1 == 0 or n2 == 0:
            return runs, 0, True
        
        expected_runs = (2 * n1 * n2) / (n1 + n2) + 1
        variance = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / ((n1 + n2) ** 2 * (n1 + n2 - 1))
        
        if variance <= 0:
            return runs, 0, True
        
        z = (runs - expected_runs) / math.sqrt(variance)
        is_random = abs(z) < 1.96
        return runs, z, is_random
    
    @staticmethod
    def correlation_test(x: List[float], y: List[float]) -> float:
        """相关性检验"""
        if len(x) != len(y) or len(x) < 2:
            return 0
        
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        denominator_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
        
        if denominator_x == 0 or denominator_y == 0:
            return 0
        
        return numerator / (denominator_x * denominator_y)


class CheatDetector:
    """作弊检测器（增强版）"""
    
    def __init__(self, history: List[Tuple]):
        self.history = history
        self.anomalies = []
        self.cold_analyzer = ColdNumberAnalyzer(history)
    
    def detect_frequency_anomaly(self) -> Dict:
        """检测频率异常"""
        print("\n" + "=" * 60)
        print("【作弊检测1】频率异常检测（卡方检验）")
        print("=" * 60)
        
        red_counter = Counter()
        blue_counter = Counter()
        
        for item in self.history:
            red_counter.update(item[2])
            blue_counter.update([item[3]])
        
        total_draws = len(self.history)
        
        red_expected = 6 / 33
        red_chi2, red_random = StatisticalTests.chi_square_test(
            dict(red_counter), red_expected, total_draws * 6
        )
        
        blue_expected = 1 / 16
        blue_chi2, blue_random = StatisticalTests.chi_square_test(
            dict(blue_counter), blue_expected, total_draws
        )
        
        print(f"红球卡方值：{red_chi2:.2f}")
        print(f"红球随机性：{'✓ 通过' if red_random else '✗ 异常'}")
        print(f"蓝球卡方值：{blue_chi2:.2f}")
        print(f"蓝球随机性：{'✓ 通过' if blue_random else '✗ 异常'}")
        
        red_theory = total_draws * 6 / 33
        red_deviations = {n: abs(c - red_theory) / red_theory for n, c in red_counter.items()}
        top_deviations = sorted(red_deviations.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print("\n红球偏离度TOP5：")
        for num, dev in top_deviations:
            actual = red_counter[num]
            print(f"  {num:02d}: 实际{actual}次, 理论{red_theory:.0f}次, 偏离{dev*100:.1f}%")
        
        if not red_random or not blue_random:
            self.anomalies.append("频率分布异常")
        
        return {'red_chi2': red_chi2, 'red_random': red_random, 'blue_chi2': blue_chi2, 'blue_random': blue_random}
    
    def detect_sequence_anomaly(self) -> Dict:
        """检测序列异常（游程检验）"""
        print("\n" + "=" * 60)
        print("【作弊检测2】序列随机性检测（游程检验）")
        print("=" * 60)
        
        sums = [sum(item[2]) for item in self.history]
        median_sum = sorted(sums)[len(sums) // 2]
        
        runs, z, is_random = StatisticalTests.runs_test(sums, median_sum)
        
        print(f"红球和值序列游程数：{runs}")
        print(f"Z统计量：{z:.3f}")
        print(f"序列独立性：{'✓ 通过' if is_random else '✗ 异常'}")
        
        if not is_random:
            if z > 0:
                print("  → 游程过多，可能存在人为交替模式")
            else:
                print("  → 游程过少，可能存在人为聚集模式")
            self.anomalies.append("序列随机性异常")
        
        return {'runs': runs, 'z': z, 'is_random': is_random}
    
    def detect_pool_correlation(self) -> Dict:
        """检测奖池与开奖号码的相关性"""
        print("\n" + "=" * 60)
        print("【作弊检测3】奖池相关性检测")
        print("=" * 60)
        
        pools = [item[5] for item in self.history if len(item) > 5 and item[5]]
        if len(pools) < 10:
            print("奖池数据不足，跳过此检测")
            return {'correlation': None}
        
        red_last_seen = {n: -1 for n in range(1, 34)}
        coldness = []
        
        for i, item in enumerate(self.history):
            if len(item) > 5 and item[5]:
                total_missing = 0
                for num in item[2]:
                    if red_last_seen[num] >= 0:
                        total_missing += i - red_last_seen[num]
                    else:
                        total_missing += i
                coldness.append(total_missing / 6)
            
            for num in item[2]:
                red_last_seen[num] = i
        
        pools_aligned = pools[:len(coldness)]
        coldness_aligned = coldness[:len(pools)]
        
        if len(pools_aligned) < 10:
            print("数据不足，跳过此检测")
            return {'correlation': None}
        
        correlation = StatisticalTests.correlation_test(pools_aligned, coldness_aligned)
        
        print(f"奖池金额与号码冷门度相关系数：{correlation:.4f}")
        
        if abs(correlation) > 0.3:
            print(f"  → {'正' if correlation > 0 else '负'}相关性较强，可能存在异常")
            self.anomalies.append("奖池相关性异常")
        else:
            print("  → 相关性较弱，符合随机预期")
        
        return {'correlation': correlation}
    
    def detect_coldness_pattern(self) -> Dict:
        """检测冷门号码开奖模式（V3.0新增）"""
        print("\n" + "=" * 60)
        print("【作弊检测4】冷门号码开奖模式检测")
        print("=" * 60)
        
        result1 = self.cold_analyzer.analyze_historical_coldness()
        result2 = self.cold_analyzer.detect_coldness_anomaly()
        
        if result2.get('anomaly_detected'):
            self.anomalies.append("冷门号码中奖率异常")
        
        return {**result1, **result2}
    
    def generate_report(self) -> str:
        """生成作弊检测报告"""
        print("\n" + "★" * 60)
        print("       作弊检测综合报告")
        print("★" * 60)
        
        self.detect_frequency_anomaly()
        self.detect_sequence_anomaly()
        self.detect_pool_correlation()
        self.detect_coldness_pattern()
        
        print("\n" + "=" * 60)
        print("【检测结论】")
        print("=" * 60)
        
        if not self.anomalies:
            print("✓ 未发现明显异常，数据符合随机分布特征")
            conclusion = "正常"
        else:
            print(f"✗ 发现 {len(self.anomalies)} 项异常：")
            for anomaly in self.anomalies:
                print(f"  - {anomaly}")
            conclusion = "存疑"
        
        print("\n【重要说明】")
        print("1. 统计异常不等于作弊，可能是正常的随机波动")
        print("2. 彩票中心有严格的监管和公证流程")
        print("3. 本检测仅供参考，不构成任何指控")
        
        return conclusion


class AdvancedAnalyzer:
    """高级分析模块"""
    
    def __init__(self, history: List[Tuple]):
        self.history = history
        self.red_range = range(1, 34)
        self.blue_range = range(1, 17)
    
    def calculate_ac_value(self, numbers: List[int]) -> int:
        """计算AC值（号码复杂度）"""
        if len(numbers) < 2:
            return 0
        
        differences = set()
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                differences.add(abs(numbers[i] - numbers[j]))
        
        return len(differences) - (len(numbers) - 1)
    
    def analyze_ac_distribution(self) -> Dict:
        """分析AC值分布"""
        print("\n" + "=" * 60)
        print("【高级分析1】AC值（号码复杂度）分析")
        print("=" * 60)
        
        ac_dist = Counter()
        for item in self.history:
            ac = self.calculate_ac_value(item[2])
            ac_dist[ac] += 1
        
        total = len(self.history)
        print("AC值分布：")
        for ac in sorted(ac_dist.keys()):
            count = ac_dist[ac]
            bar = '█' * int(count / total * 50)
            print(f"  AC={ac:2d}: {count:4d}次 ({count/total*100:5.1f}%) {bar}")
        
        avg_ac = sum(ac * count for ac, count in ac_dist.items()) / total
        print(f"\n平均AC值：{avg_ac:.2f}")
        
        self.ac_distribution = ac_dist
        self.avg_ac = avg_ac
        return dict(ac_dist)
    
    def analyze_same_tail(self) -> Dict:
        """同尾号分析"""
        print("\n" + "=" * 60)
        print("【高级分析2】同尾号分析")
        print("=" * 60)
        
        tail_dist = Counter()
        tail_freq = Counter()
        
        for item in self.history:
            tails = [r % 10 for r in item[2]]
            tail_counter = Counter(tails)
            max_same = max(tail_counter.values())
            tail_dist[max_same] += 1
            tail_freq.update(tails)
        
        total = len(self.history)
        print("同尾号个数分布：")
        for n in sorted(tail_dist.keys()):
            count = tail_dist[n]
            print(f"  {n}个同尾: {count}次 ({count/total*100:.1f}%)")
        
        self.tail_distribution = tail_dist
        return {'tail_dist': dict(tail_dist), 'tail_freq': dict(tail_freq)}
    
    def analyze_repeat_numbers(self) -> Dict:
        """重号分析"""
        print("\n" + "=" * 60)
        print("【高级分析3】重号分析")
        print("=" * 60)
        
        repeat_dist = Counter()
        
        for i in range(1, len(self.history)):
            prev_reds = set(self.history[i-1][2])
            curr_reds = set(self.history[i][2])
            repeat_count = len(prev_reds & curr_reds)
            repeat_dist[repeat_count] += 1
        
        total = len(self.history) - 1
        print("重号个数分布：")
        for n in sorted(repeat_dist.keys()):
            count = repeat_dist[n]
            print(f"  {n}个重号: {count}次 ({count/total*100:.1f}%)")
        
        self.repeat_distribution = repeat_dist
        return dict(repeat_dist)
    
    def analyze_span(self) -> Dict:
        """跨度分析"""
        print("\n" + "=" * 60)
        print("【高级分析4】跨度分析")
        print("=" * 60)
        
        spans = []
        for item in self.history:
            reds = item[2]
            span = max(reds) - min(reds)
            spans.append(span)
        
        avg_span = sum(spans) / len(spans)
        
        span_ranges = [(15, 20), (21, 25), (26, 30), (31, 32)]
        print("跨度分布：")
        for low, high in span_ranges:
            count = sum(1 for s in spans if low <= s <= high)
            print(f"  {low}-{high}: {count}次 ({count/len(spans)*100:.1f}%)")
        
        print(f"\n平均跨度：{avg_span:.1f}")
        
        self.avg_span = avg_span
        return {'avg': avg_span, 'min': min(spans), 'max': max(spans)}
    
    def build_markov_chain(self) -> Dict:
        """构建马尔可夫链转移矩阵"""
        print("\n" + "=" * 60)
        print("【高级分析5】马尔可夫链分析")
        print("=" * 60)
        
        def get_zone(n):
            if n <= 11:
                return 'S'
            elif n <= 22:
                return 'M'
            else:
                return 'L'
        
        transitions = defaultdict(Counter)
        
        for i in range(1, len(self.history)):
            prev_zones = [get_zone(n) for n in self.history[i-1][2]]
            curr_zones = [get_zone(n) for n in self.history[i][2]]
            
            for pz in prev_zones:
                for cz in curr_zones:
                    transitions[pz][cz] += 1
        
        print("区间转移概率矩阵：")
        print("        → 小区  → 中区  → 大区")
        for from_zone in ['S', 'M', 'L']:
            total = sum(transitions[from_zone].values())
            if total == 0:
                continue
            probs = {z: transitions[from_zone][z] / total for z in ['S', 'M', 'L']}
            zone_name = {'S': '小区', 'M': '中区', 'L': '大区'}[from_zone]
            print(f"  {zone_name}: {probs['S']:.3f}   {probs['M']:.3f}   {probs['L']:.3f}")
        
        self.markov_transitions = dict(transitions)
        return dict(transitions)
    
    def bayesian_update(self, prior: Dict[int, float], recent_n: int = 30) -> Dict[int, float]:
        """贝叶斯概率更新"""
        print("\n" + "=" * 60)
        print(f"【高级分析6】贝叶斯概率更新（近{recent_n}期）")
        print("=" * 60)
        
        recent_data = self.history[-recent_n:]
        
        red_counts = Counter()
        for item in recent_data:
            red_counts.update(item[2])
        
        posterior = {}
        total_likelihood = 0
        
        for num in self.red_range:
            likelihood = (red_counts[num] + 1) / (recent_n * 6 + 33)
            posterior[num] = prior.get(num, 1/33) * likelihood
            total_likelihood += posterior[num]
        
        for num in posterior:
            posterior[num] /= total_likelihood
        
        changes = [(num, posterior[num] - prior.get(num, 1/33)) for num in self.red_range]
        changes.sort(key=lambda x: abs(x[1]), reverse=True)
        
        print("概率变化最大的号码：")
        for num, change in changes[:10]:
            direction = "↑" if change > 0 else "↓"
            print(f"  {num:02d}: {direction} {abs(change)*100:.2f}%")
        
        return posterior


class LotteryPredictor:
    """双色球预测器（V3.0 反作弊增强版）"""
    
    def __init__(self, data_file: str = '双色球数据_20260115.csv'):
        self.data_file = data_file
        self.history = []
        self.red_range = range(1, 34)
        self.blue_range = range(1, 17)
        self.cheat_detector = None
        self.advanced_analyzer = None
        self.cold_analyzer = None
        
    def load_data(self):
        """加载历史数据"""
        print("=" * 60)
        print("【步骤1】加载历史开奖数据")
        print("=" * 60)
        
        self.history = LotteryDataLoader.auto_load(self.data_file)
        self.history.sort(key=lambda x: x[0])
        
        if len(self.history) == 0:
            print("✗ 未能加载任何数据，请检查数据文件格式")
            return
        
        print(f"✓ 成功加载 {len(self.history)} 期历史数据")
        print(f"✓ 数据范围：{self.history[0][0]} ~ {self.history[-1][0]}")
        print(f"✓ 最新一期：{self.history[-1][0]}")
        print(f"  红球：{self.history[-1][2]}")
        print(f"  蓝球：{self.history[-1][3]}")
        
        self.cheat_detector = CheatDetector(self.history)
        self.advanced_analyzer = AdvancedAnalyzer(self.history)
        self.cold_analyzer = ColdNumberAnalyzer(self.history)
        print()
        
    def analyze_frequency(self):
        """频率统计分析"""
        print("=" * 60)
        print("【步骤2】频率统计分析")
        print("=" * 60)
        
        red_counter = Counter()
        blue_counter = Counter()
        
        for item in self.history:
            red_counter.update(item[2])
            blue_counter.update([item[3]])
        
        total = len(self.history)
        
        self.red_freq = {n: red_counter[n] / (total * 6) for n in self.red_range}
        self.blue_freq = {n: blue_counter[n] / total for n in self.blue_range}
        
        red_sorted = sorted(self.red_freq.items(), key=lambda x: x[1], reverse=True)
        blue_sorted = sorted(self.blue_freq.items(), key=lambda x: x[1], reverse=True)
        
        print("红球出现频率TOP10：")
        for num, freq in red_sorted[:10]:
            print(f"  {num:02d}: {freq:.4f} ({red_counter[num]}次)")
        
        print("\n蓝球出现频率TOP5：")
        for num, freq in blue_sorted[:5]:
            print(f"  {num:02d}: {freq:.4f} ({blue_counter[num]}次)")
        print()
        
        self.red_counter = red_counter
        self.blue_counter = blue_counter
        return red_counter, blue_counter
    
    def analyze_missing(self):
        """遗漏值分析"""
        print("=" * 60)
        print("【步骤3】遗漏值分析")
        print("=" * 60)
        
        self.red_missing = {}
        self.blue_missing = {}
        
        total = len(self.history)
        
        for num in self.red_range:
            for i in range(total - 1, -1, -1):
                if num in self.history[i][2]:
                    self.red_missing[num] = total - 1 - i
                    break
            else:
                self.red_missing[num] = total
        
        for num in self.blue_range:
            for i in range(total - 1, -1, -1):
                if num == self.history[i][3]:
                    self.blue_missing[num] = total - 1 - i
                    break
            else:
                self.blue_missing[num] = total
        
        red_missing_sorted = sorted(self.red_missing.items(), key=lambda x: x[1], reverse=True)
        
        print("红球遗漏值TOP10：")
        for num, miss in red_missing_sorted[:10]:
            theory_miss = total / max(self.red_counter[num], 1)
            ratio = miss / theory_miss
            status = "⚠️ 欠出" if ratio > 1.5 else ""
            print(f"  {num:02d}: 遗漏{miss}期 (比值{ratio:.1f}) {status}")
        print()
        
        return self.red_missing, self.blue_missing
    
    def analyze_hot_cold(self, recent_n: int = 30):
        """冷热号分析"""
        print("=" * 60)
        print(f"【步骤4】冷热号分析（近{recent_n}期）")
        print("=" * 60)
        
        recent_data = self.history[-recent_n:]
        
        red_hot = Counter()
        blue_hot = Counter()
        
        for item in recent_data:
            red_hot.update(item[2])
            blue_hot.update([item[3]])
        
        self.red_hot = {n: red_hot.get(n, 0) for n in self.red_range}
        self.blue_hot = {n: blue_hot.get(n, 0) for n in self.blue_range}
        
        red_hot_sorted = sorted(self.red_hot.items(), key=lambda x: x[1], reverse=True)
        
        print(f"红球热号TOP10：")
        for num, count in red_hot_sorted[:10]:
            bar = '█' * count
            print(f"  {num:02d}: {count}次 {bar}")
        print()
        
        return self.red_hot, self.blue_hot

    def analyze_odd_even(self):
        """奇偶比分析"""
        print("=" * 60)
        print("【步骤5】奇偶比分析")
        print("=" * 60)
        
        odd_even_dist = Counter()
        
        for item in self.history:
            odd_count = sum(1 for r in item[2] if r % 2 == 1)
            even_count = 6 - odd_count
            odd_even_dist[(odd_count, even_count)] += 1
        
        total = len(self.history)
        print("红球奇偶比分布：")
        for (odd, even), count in sorted(odd_even_dist.items(), key=lambda x: x[1], reverse=True):
            bar = '█' * int(count / total * 30)
            print(f"  {odd}奇{even}偶: {count:4d}次 ({count/total*100:5.1f}%) {bar}")
        
        self.common_odd_even = sorted(odd_even_dist.items(), key=lambda x: x[1], reverse=True)[:3]
        print()
        
        return odd_even_dist
    
    def analyze_zones(self):
        """区间分布分析"""
        print("=" * 60)
        print("【步骤6】区间分布分析")
        print("=" * 60)
        
        zone_dist = Counter()
        
        for item in self.history:
            z1 = sum(1 for r in item[2] if 1 <= r <= 11)
            z2 = sum(1 for r in item[2] if 12 <= r <= 22)
            z3 = sum(1 for r in item[2] if 23 <= r <= 33)
            zone_dist[(z1, z2, z3)] += 1
        
        total = len(self.history)
        print("红球区间分布TOP10：")
        zone_sorted = sorted(zone_dist.items(), key=lambda x: x[1], reverse=True)[:10]
        for (z1, z2, z3), count in zone_sorted:
            bar = '█' * int(count / total * 30)
            print(f"  {z1}:{z2}:{z3} - {count:4d}次 ({count/total*100:5.1f}%) {bar}")
        
        self.common_zones = zone_sorted[:3]
        print()
        
        return zone_dist
    
    def analyze_sum(self):
        """和值分析"""
        print("=" * 60)
        print("【步骤7】和值分析")
        print("=" * 60)
        
        sums = [sum(item[2]) for item in self.history]
        
        avg_sum = sum(sums) / len(sums)
        variance = sum((s - avg_sum) ** 2 for s in sums) / len(sums)
        std_dev = math.sqrt(variance)
        
        print(f"红球和值统计：")
        print(f"  平均和值：{avg_sum:.1f}")
        print(f"  标准差：{std_dev:.1f}")
        print(f"  建议范围：{int(avg_sum - std_dev)} ~ {int(avg_sum + std_dev)}")
        
        self.sum_range = (int(avg_sum - std_dev), int(avg_sum + std_dev))
        self.avg_sum = avg_sum
        print()
        
        return avg_sum, std_dev
    
    def analyze_consecutive(self):
        """连号分析"""
        print("=" * 60)
        print("【步骤8】连号分析")
        print("=" * 60)
        
        consecutive_dist = Counter()
        
        for item in self.history:
            sorted_reds = sorted(item[2])
            consecutive = sum(1 for i in range(5) if sorted_reds[i+1] - sorted_reds[i] == 1)
            consecutive_dist[consecutive] += 1
        
        total = len(self.history)
        print("连号组数分布：")
        for cons in sorted(consecutive_dist.keys()):
            count = consecutive_dist[cons]
            bar = '█' * int(count / total * 30)
            print(f"  {cons}组连号: {count:4d}次 ({count/total*100:5.1f}%) {bar}")
        
        self.common_consecutive = sorted(consecutive_dist.items(), key=lambda x: x[1], reverse=True)[0][0]
        print()
        
        return consecutive_dist

    def calculate_scores(self):
        """计算综合得分"""
        print("=" * 60)
        print("【步骤9】计算综合得分")
        print("=" * 60)
        
        alpha = 0.20
        beta = 0.30
        gamma = 0.35
        delta = 0.15
        
        print(f"权重：频率{alpha} + 遗漏{beta} + 热度{gamma} + 贝叶斯{delta}")
        print()
        
        prior = {n: 1/33 for n in self.red_range}
        posterior = self.advanced_analyzer.bayesian_update(prior, recent_n=30)
        
        self.red_scores = {}
        max_freq = max(self.red_freq.values())
        max_missing = max(self.red_missing.values())
        max_hot = max(self.red_hot.values()) if max(self.red_hot.values()) > 0 else 1
        max_posterior = max(posterior.values())
        
        for num in self.red_range:
            freq_score = self.red_freq[num] / max_freq
            missing_score = self.red_missing[num] / max_missing
            hot_score = self.red_hot[num] / max_hot
            bayes_score = posterior[num] / max_posterior
            
            total_score = alpha * freq_score + beta * missing_score + gamma * hot_score + delta * bayes_score
            self.red_scores[num] = total_score
        
        self.blue_scores = {}
        max_freq = max(self.blue_freq.values())
        max_missing = max(self.blue_missing.values())
        max_hot = max(self.blue_hot.values()) if max(self.blue_hot.values()) > 0 else 1
        
        for num in self.blue_range:
            freq_score = self.blue_freq[num] / max_freq
            missing_score = self.blue_missing[num] / max_missing
            hot_score = self.blue_hot[num] / max_hot
            
            total_score = alpha * freq_score + beta * missing_score + gamma * hot_score
            self.blue_scores[num] = total_score
        
        red_sorted = sorted(self.red_scores.items(), key=lambda x: x[1], reverse=True)
        
        print("红球综合得分TOP15：")
        for num, score in red_sorted[:15]:
            bar = '█' * int(score * 20)
            print(f"  {num:02d}: {score:.4f} {bar}")
        print()
        
        return self.red_scores, self.blue_scores

    def validate_combination(self, reds: List[int], blue: int) -> Tuple[bool, List[str]]:
        """验证号码组合的合理性"""
        issues = []
        
        total = sum(reds)
        if not (self.sum_range[0] <= total <= self.sum_range[1]):
            issues.append(f"和值{total}超出建议范围")
        
        odd_count = sum(1 for r in reds if r % 2 == 1)
        if odd_count < 2 or odd_count > 4:
            issues.append(f"奇偶比不合理")
        
        z1 = sum(1 for r in reds if 1 <= r <= 11)
        z2 = sum(1 for r in reds if 12 <= r <= 22)
        z3 = sum(1 for r in reds if 23 <= r <= 33)
        if z1 == 0 or z2 == 0 or z3 == 0:
            issues.append(f"区间有空区")
        
        ac = self.advanced_analyzer.calculate_ac_value(reds)
        if ac < 5:
            issues.append(f"AC值过低")
        
        span = max(reds) - min(reds)
        if span < 18 or span > 30:
            issues.append(f"跨度不合理")
        
        return len(issues) == 0, issues
    
    def predict_normal(self) -> List[Tuple]:
        """正常预测方案"""
        print("=" * 60)
        print("【预测方案A】智能统计预测")
        print("=" * 60)
        
        red_sorted = sorted(self.red_scores.items(), key=lambda x: x[1], reverse=True)
        candidates = [num for num, _ in red_sorted[:20]]
        
        predictions = []
        attempts = 0
        
        while len(predictions) < 5 and attempts < 1000:
            attempts += 1
            selected = []
            pool = candidates.copy()
            
            target_zones = self.common_zones[len(predictions) % len(self.common_zones)][0]
            z1_target, z2_target, z3_target = target_zones
            
            z1_pool = [n for n in pool if 1 <= n <= 11]
            z2_pool = [n for n in pool if 12 <= n <= 22]
            z3_pool = [n for n in pool if 23 <= n <= 33]
            
            random.shuffle(z1_pool)
            random.shuffle(z2_pool)
            random.shuffle(z3_pool)
            
            selected.extend(z1_pool[:min(z1_target, len(z1_pool))])
            selected.extend(z2_pool[:min(z2_target, len(z2_pool))])
            selected.extend(z3_pool[:min(z3_target, len(z3_pool))])
            
            remaining = [n for n in pool if n not in selected]
            random.shuffle(remaining)
            while len(selected) < 6 and remaining:
                selected.append(remaining.pop())
            
            while len(selected) < 6:
                all_remaining = [n for n in self.red_range if n not in selected]
                selected.append(random.choice(all_remaining))
            
            selected = sorted(selected[:6])
            
            blue_sorted = sorted(self.blue_scores.items(), key=lambda x: x[1], reverse=True)
            blue = blue_sorted[len(predictions) % 3][0]
            
            is_valid, _ = self.validate_combination(selected, blue)
            if is_valid and (selected, blue) not in predictions:
                predictions.append((selected, blue))
        
        print("【预测结果】")
        for i, (reds, blue) in enumerate(predictions, 1):
            red_str = '+'.join(f'{r:02d}' for r in reds)
            ac = self.advanced_analyzer.calculate_ac_value(reds)
            print(f"  第{i}组：红球 {red_str} | 蓝球 {blue:02d} | AC值={ac}")
        
        self.normal_predictions = predictions
        print()
        return predictions
    
    def predict_anti_cheat(self) -> List[Tuple]:
        """反作弊预测方案（V3.0核心新增）"""
        print("=" * 60)
        print("【预测方案B】反作弊策略（冷门号码）")
        print("=" * 60)
        
        print("【核心假设】")
        print("彩票中心在停止销售后，统计最少人买的号码组合开奖")
        print("因此我们选择具有'冷门特征'的号码组合")
        print()
        
        predictions = self.cold_analyzer.generate_cold_predictions(5)
        self.anti_cheat_predictions = predictions
        return predictions
    
    def predict_random_enhanced(self) -> List[Tuple]:
        """增强随机预测"""
        print("=" * 60)
        print("【预测方案C】增强随机策略")
        print("=" * 60)
        
        predictions = []
        
        while len(predictions) < 5:
            reds = sorted(random.sample(list(self.red_range), 6))
            blue = random.choice(list(self.blue_range))
            
            is_valid, _ = self.validate_combination(reds, blue)
            if is_valid and (reds, blue) not in predictions:
                predictions.append((reds, blue))
        
        print("【预测结果】")
        for i, (reds, blue) in enumerate(predictions, 1):
            red_str = '+'.join(f'{r:02d}' for r in reds)
            ac = self.advanced_analyzer.calculate_ac_value(reds)
            print(f"  第{i}组：红球 {red_str} | 蓝球 {blue:02d} | AC值={ac}")
        
        self.random_predictions = predictions
        print()
        return predictions
    
    def predict_cold_rebound(self) -> List[Tuple]:
        """冷号回补策略"""
        print("=" * 60)
        print("【预测方案D】冷号回补策略")
        print("=" * 60)
        
        cold_reds = []
        total = len(self.history)
        for num in self.red_range:
            theory_miss = total / max(self.red_counter[num], 1)
            actual_miss = self.red_missing[num]
            if actual_miss > theory_miss:
                cold_reds.append((num, actual_miss / theory_miss))
        
        cold_reds.sort(key=lambda x: x[1], reverse=True)
        cold_candidates = [num for num, _ in cold_reds[:15]]
        
        predictions = []
        attempts = 0
        
        while len(predictions) < 5 and attempts < 500:
            attempts += 1
            
            n_cold = random.randint(4, 5)
            selected = random.sample(cold_candidates, min(n_cold, len(cold_candidates)))
            
            hot_sorted = sorted(self.red_hot.items(), key=lambda x: x[1], reverse=True)
            hot_candidates = [num for num, _ in hot_sorted[:10] if num not in selected]
            
            while len(selected) < 6 and hot_candidates:
                selected.append(hot_candidates.pop(0))
            
            while len(selected) < 6:
                remaining = [n for n in self.red_range if n not in selected]
                selected.append(random.choice(remaining))
            
            selected = sorted(selected[:6])
            
            blue_missing_sorted = sorted(self.blue_missing.items(), key=lambda x: x[1], reverse=True)
            blue = blue_missing_sorted[len(predictions) % 3][0]
            
            is_valid, _ = self.validate_combination(selected, blue)
            if is_valid and (selected, blue) not in predictions:
                predictions.append((selected, blue))
        
        print("【预测结果】")
        for i, (reds, blue) in enumerate(predictions, 1):
            red_str = '+'.join(f'{r:02d}' for r in reds)
            ac = self.advanced_analyzer.calculate_ac_value(reds)
            print(f"  第{i}组：红球 {red_str} | 蓝球 {blue:02d} | AC值={ac}")
        
        self.cold_predictions = predictions
        print()
        return predictions

    def run_full_analysis(self):
        """运行完整分析流程"""
        print("\n" + "★" * 60)
        print("   中国福利彩票双色球智能预测系统 V3.0")
        print("   （反作弊增强版）")
        print("★" * 60)
        print()
        
        # 1. 加载数据
        self.load_data()
        
        # 2. 基础分析
        self.analyze_frequency()
        self.analyze_missing()
        self.analyze_hot_cold()
        self.analyze_odd_even()
        self.analyze_zones()
        self.analyze_sum()
        self.analyze_consecutive()
        
        # 3. 高级分析
        print("\n" + "★" * 60)
        print("       高级统计分析")
        print("★" * 60)
        
        self.advanced_analyzer.analyze_ac_distribution()
        self.advanced_analyzer.analyze_same_tail()
        self.advanced_analyzer.analyze_repeat_numbers()
        self.advanced_analyzer.analyze_span()
        self.advanced_analyzer.build_markov_chain()
        
        # 4. 作弊检测（含冷门号码分析）
        print("\n" + "★" * 60)
        print("       作弊检测分析（V3.0增强）")
        print("★" * 60)
        
        cheat_conclusion = self.cheat_detector.generate_report()
        
        # 5. 计算综合得分
        self.calculate_scores()
        
        # 6. 生成预测
        print("\n" + "★" * 60)
        print("       预测结果汇总")
        print("★" * 60)
        print()
        
        self.predict_normal()
        self.predict_anti_cheat()  # V3.0新增
        self.predict_random_enhanced()
        self.predict_cold_rebound()
        
        # 7. 最终推荐
        self.print_final_recommendation(cheat_conclusion)
    
    def print_final_recommendation(self, cheat_conclusion: str):
        """打印最终推荐"""
        print("=" * 60)
        print("【最终推荐】下一期预测号码")
        print("=" * 60)
        
        print("\n★ 主推方案（智能统计）：")
        reds, blue = self.normal_predictions[0]
        red_str = '+'.join(f'{r:02d}' for r in reds)
        ac = self.advanced_analyzer.calculate_ac_value(reds)
        coldness, _ = self.cold_analyzer.calculate_coldness_score(reds, blue)
        print(f"   红球：{red_str}")
        print(f"   蓝球：{blue:02d}")
        print(f"   AC值：{ac} | 冷门度：{coldness}")
        
        print("\n★ 反作弊方案（冷门号码）【V3.0新增】：")
        reds, blue = self.anti_cheat_predictions[0]
        red_str = '+'.join(f'{r:02d}' for r in reds)
        ac = self.advanced_analyzer.calculate_ac_value(reds)
        coldness, details = self.cold_analyzer.calculate_coldness_score(reds, blue)
        print(f"   红球：{red_str}")
        print(f"   蓝球：{blue:02d}")
        print(f"   AC值：{ac} | 冷门度：{coldness}")
        main_factors = sorted(details.items(), key=lambda x: x[1], reverse=True)[:3]
        factors_str = ', '.join(f"{k}" for k, v in main_factors if v > 0)
        print(f"   冷门因素：{factors_str}")
        
        print("\n★ 冷号回补方案：")
        reds, blue = self.cold_predictions[0]
        red_str = '+'.join(f'{r:02d}' for r in reds)
        ac = self.advanced_analyzer.calculate_ac_value(reds)
        coldness, _ = self.cold_analyzer.calculate_coldness_score(reds, blue)
        print(f"   红球：{red_str}")
        print(f"   蓝球：{blue:02d}")
        print(f"   AC值：{ac} | 冷门度：{coldness}")
        
        print("\n★ 随机方案：")
        reds, blue = self.random_predictions[0]
        red_str = '+'.join(f'{r:02d}' for r in reds)
        ac = self.advanced_analyzer.calculate_ac_value(reds)
        coldness, _ = self.cold_analyzer.calculate_coldness_score(reds, blue)
        print(f"   红球：{red_str}")
        print(f"   蓝球：{blue:02d}")
        print(f"   AC值：{ac} | 冷门度：{coldness}")
        
        print("\n" + "=" * 60)
        print("【作弊检测结论】")
        print("=" * 60)
        if cheat_conclusion == "正常":
            print("✓ 历史数据未发现明显异常")
        else:
            print("⚠️ 历史数据存在部分统计异常，建议参考反作弊方案")
        
        print("\n" + "=" * 60)
        print("【V3.0 反作弊策略说明】")
        print("=" * 60)
        print("""
基于假设：彩票中心在停止销售后统计最少人买的号码开奖

冷门号码特征（大众心理学）：
1. 连续号码 - 人们认为"不可能连号"
2. 全大/全小 - 人们偏好均匀分布
3. 全奇/全偶 - 人们偏好奇偶平衡
4. 同尾号多 - 人们避免重复尾数
5. 边缘号码 - 人们偏好中间号码
6. AC值低 - 看起来"不随机"

反作弊策略：选择具有上述特征的号码组合
""")
        
        print("\n" + "=" * 60)
        print("【重要提示】")
        print("=" * 60)
        print("""
1. 彩票是随机事件，任何预测方法都无法保证中奖
2. 本程序仅供学习和娱乐，请理性购彩
3. 切勿沉迷赌博，量力而行
4. 中奖概率极低，请勿投入过多资金

【双色球中奖概率】
- 一等奖：1/17,721,088 ≈ 0.0000056%
- 期望收益：投注2元约亏损0.5元（负期望）
""")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("【数学公式与原理说明】")
    print("=" * 60)
    print("""
【冷门度计算公式】（V3.0新增）
冷门度 = 连号分×15 + 大小极端分 + 奇偶极端分 + 同尾分×10 
       + 边缘号分×8 + 低AC分 + 空区分 + 跨度异常分 + 蓝球边缘分

【综合得分公式】
Score = 0.20×频率 + 0.30×遗漏 + 0.35×热度 + 0.15×贝叶斯

【组合概率】
总组合数 = C(33,6) × 16 = 17,721,088
一等奖概率 = 1/17,721,088
""")
    
    data_files = ['双色球数据_20260115.csv', '1.txt']
    data_file = None
    
    for f in data_files:
        if os.path.exists(f):
            data_file = f
            break
    
    if data_file is None:
        print("错误：未找到数据文件")
        return
    
    print(f"使用数据文件：{data_file}")
    
    predictor = LotteryPredictor(data_file)
    predictor.run_full_analysis()


if __name__ == '__main__':
    main()
