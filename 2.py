# -*- coding: utf-8 -*-
"""
中国福利彩票双色球预测系统
=====================================

【免责声明】
本程序仅供学习和娱乐目的，彩票本质上是随机事件，
任何预测方法都无法保证中奖。请理性购彩，量力而行。

【双色球规则】
- 红球：从01-33中选6个（不重复）
- 蓝球：从01-16中选1个

【分析计划】
1. 数据加载与预处理
2. 频率统计分析
3. 遗漏值分析
4. 冷热号分析
5. 奇偶比分析
6. 区间分布分析
7. 和值分析
8. 连号分析
9. 综合预测

【分析原理】
虽然彩票是随机事件，但我们可以通过统计学方法分析历史数据的规律：
- 大数定律：长期来看，每个号码出现的频率应趋于相等
- 遗漏分析：长期未出现的号码可能"回补"
- 热号追踪：近期频繁出现的号码可能继续出现
- 组合特征：分析奇偶比、大小比、区间分布等特征

【数学公式】
1. 频率 = 出现次数 / 总期数
2. 遗漏值 = 当前期数 - 最后出现期数
3. 理论遗漏 = 总期数 / 出现次数
4. 遗漏比 = 当前遗漏 / 理论遗漏
5. 热度指数 = 近N期出现次数 / N × 权重系数
6. 综合得分 = α×频率得分 + β×遗漏得分 + γ×热度得分

Author: AI Assistant
Date: 2026-01-12
"""

import re
from collections import Counter, defaultdict
from datetime import datetime
import random
import math

class LotteryPredictor:
    """双色球预测器"""
    
    def __init__(self, data_file='1.txt'):
        self.data_file = data_file
        self.history = []  # [(期号, 日期, [红球], 蓝球), ...]
        self.red_range = range(1, 34)  # 红球1-33
        self.blue_range = range(1, 17)  # 蓝球1-16
        
    def load_data(self):
        """加载历史数据"""
        print("=" * 60)
        print("【步骤1】加载历史开奖数据")
        print("=" * 60)
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines[1:]:  # 跳过标题行
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) < 3:
                continue
                
            issue = parts[0]
            date = parts[1]
            numbers = parts[2]
            
            # 解析号码：格式如 06+08+14+15+24+25+06
            nums = numbers.split('+')
            if len(nums) == 7:
                red_balls = sorted([int(n) for n in nums[:6]])
                blue_ball = int(nums[6])
                self.history.append((issue, date, red_balls, blue_ball))
        
        print(f"✓ 成功加载 {len(self.history)} 期历史数据")
        print(f"✓ 数据范围：{self.history[0][0]} ~ {self.history[-1][0]}")
        print(f"✓ 最新一期：{self.history[-1][0]} - 红球:{self.history[-1][2]} 蓝球:{self.history[-1][3]}")
        print()
        
    def analyze_frequency(self):
        """频率统计分析"""
        print("=" * 60)
        print("【步骤2】频率统计分析")
        print("=" * 60)
        
        red_counter = Counter()
        blue_counter = Counter()
        
        for _, _, reds, blue in self.history:
            red_counter.update(reds)
            blue_counter.update([blue])
        
        total = len(self.history)
        
        # 红球频率
        self.red_freq = {n: red_counter[n] / total for n in self.red_range}
        # 蓝球频率
        self.blue_freq = {n: blue_counter[n] / total for n in self.blue_range}
        
        # 理论频率
        red_theory = 6 / 33  # 每期选6个红球，共33个
        blue_theory = 1 / 16  # 每期选1个蓝球，共16个
        
        print(f"红球理论频率：{red_theory:.4f} (每期6/33)")
        print(f"蓝球理论频率：{blue_theory:.4f} (每期1/16)")
        print()
        
        # 找出高频和低频号码
        red_sorted = sorted(self.red_freq.items(), key=lambda x: x[1], reverse=True)
        blue_sorted = sorted(self.blue_freq.items(), key=lambda x: x[1], reverse=True)
        
        print("红球出现频率TOP10：")
        for num, freq in red_sorted[:10]:
            print(f"  {num:02d}: {freq:.4f} ({red_counter[num]}次)")
        
        print("\n蓝球出现频率TOP5：")
        for num, freq in blue_sorted[:5]:
            print(f"  {num:02d}: {freq:.4f} ({blue_counter[num]}次)")
        print()
        
        return red_counter, blue_counter
    
    def analyze_missing(self):
        """遗漏值分析"""
        print("=" * 60)
        print("【步骤3】遗漏值分析")
        print("=" * 60)
        
        # 计算每个号码的当前遗漏值
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
        
        # 找出遗漏值最大的号码
        red_missing_sorted = sorted(self.red_missing.items(), key=lambda x: x[1], reverse=True)
        blue_missing_sorted = sorted(self.blue_missing.items(), key=lambda x: x[1], reverse=True)
        
        print("红球遗漏值TOP10（长期未出现）：")
        for num, miss in red_missing_sorted[:10]:
            print(f"  {num:02d}: 遗漏{miss}期")
        
        print("\n蓝球遗漏值TOP5：")
        for num, miss in blue_missing_sorted[:5]:
            print(f"  {num:02d}: 遗漏{miss}期")
        print()
        
        return self.red_missing, self.blue_missing
    
    def analyze_hot_cold(self, recent_n=30):
        """冷热号分析（近N期）"""
        print("=" * 60)
        print(f"【步骤4】冷热号分析（近{recent_n}期）")
        print("=" * 60)
        
        recent_data = self.history[-recent_n:]
        
        red_hot = Counter()
        blue_hot = Counter()
        
        for _, _, reds, blue in recent_data:
            red_hot.update(reds)
            blue_hot.update([blue])
        
        self.red_hot = dict(red_hot)
        self.blue_hot = dict(blue_hot)
        
        # 补充未出现的号码
        for n in self.red_range:
            if n not in self.red_hot:
                self.red_hot[n] = 0
        for n in self.blue_range:
            if n not in self.blue_hot:
                self.blue_hot[n] = 0
        
        red_hot_sorted = sorted(self.red_hot.items(), key=lambda x: x[1], reverse=True)
        blue_hot_sorted = sorted(self.blue_hot.items(), key=lambda x: x[1], reverse=True)
        
        print(f"红球热号TOP10（近{recent_n}期出现次数）：")
        for num, count in red_hot_sorted[:10]:
            print(f"  {num:02d}: {count}次")
        
        print(f"\n红球冷号TOP5（近{recent_n}期出现次数）：")
        for num, count in red_hot_sorted[-5:]:
            print(f"  {num:02d}: {count}次")
        
        print(f"\n蓝球热号TOP5：")
        for num, count in blue_hot_sorted[:5]:
            print(f"  {num:02d}: {count}次")
        print()
        
        return self.red_hot, self.blue_hot

    def analyze_odd_even(self):
        """奇偶比分析"""
        print("=" * 60)
        print("【步骤5】奇偶比分析")
        print("=" * 60)
        
        odd_even_dist = Counter()
        
        for _, _, reds, _ in self.history:
            odd_count = sum(1 for r in reds if r % 2 == 1)
            even_count = 6 - odd_count
            odd_even_dist[(odd_count, even_count)] += 1
        
        total = len(self.history)
        print("红球奇偶比分布：")
        for (odd, even), count in sorted(odd_even_dist.items(), key=lambda x: x[1], reverse=True):
            print(f"  {odd}奇{even}偶: {count}次 ({count/total*100:.1f}%)")
        
        # 最常见的奇偶比
        self.common_odd_even = sorted(odd_even_dist.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"\n最常见奇偶比：{self.common_odd_even[0][0]}")
        print()
        
        return odd_even_dist
    
    def analyze_zones(self):
        """区间分布分析"""
        print("=" * 60)
        print("【步骤6】区间分布分析")
        print("=" * 60)
        
        # 将红球分为三个区间：1-11, 12-22, 23-33
        zone_dist = Counter()
        
        for _, _, reds, _ in self.history:
            z1 = sum(1 for r in reds if 1 <= r <= 11)
            z2 = sum(1 for r in reds if 12 <= r <= 22)
            z3 = sum(1 for r in reds if 23 <= r <= 33)
            zone_dist[(z1, z2, z3)] += 1
        
        total = len(self.history)
        print("红球区间分布（一区1-11，二区12-22，三区23-33）：")
        zone_sorted = sorted(zone_dist.items(), key=lambda x: x[1], reverse=True)[:10]
        for (z1, z2, z3), count in zone_sorted:
            print(f"  {z1}:{z2}:{z3} - {count}次 ({count/total*100:.1f}%)")
        
        self.common_zones = zone_sorted[:3]
        print(f"\n最常见区间比：{self.common_zones[0][0]}")
        print()
        
        return zone_dist
    
    def analyze_sum(self):
        """和值分析"""
        print("=" * 60)
        print("【步骤7】和值分析")
        print("=" * 60)
        
        sums = []
        for _, _, reds, _ in self.history:
            sums.append(sum(reds))
        
        avg_sum = sum(sums) / len(sums)
        min_sum = min(sums)
        max_sum = max(sums)
        
        # 计算标准差
        variance = sum((s - avg_sum) ** 2 for s in sums) / len(sums)
        std_dev = math.sqrt(variance)
        
        print(f"红球和值统计：")
        print(f"  平均和值：{avg_sum:.1f}")
        print(f"  最小和值：{min_sum}")
        print(f"  最大和值：{max_sum}")
        print(f"  标准差：{std_dev:.1f}")
        print(f"  建议和值范围：{int(avg_sum - std_dev)} ~ {int(avg_sum + std_dev)}")
        
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
        
        for _, _, reds, _ in self.history:
            sorted_reds = sorted(reds)
            consecutive = 0
            for i in range(len(sorted_reds) - 1):
                if sorted_reds[i+1] - sorted_reds[i] == 1:
                    consecutive += 1
            consecutive_dist[consecutive] += 1
        
        total = len(self.history)
        print("连号组数分布：")
        for cons, count in sorted(consecutive_dist.items()):
            print(f"  {cons}组连号: {count}次 ({count/total*100:.1f}%)")
        
        self.common_consecutive = sorted(consecutive_dist.items(), key=lambda x: x[1], reverse=True)[0][0]
        print(f"\n最常见连号组数：{self.common_consecutive}")
        print()
        
        return consecutive_dist
    
    def calculate_scores(self):
        """计算综合得分"""
        print("=" * 60)
        print("【步骤9】计算综合得分")
        print("=" * 60)
        
        # 权重设置
        alpha = 0.25  # 频率权重
        beta = 0.35   # 遗漏权重
        gamma = 0.40  # 热度权重
        
        print(f"权重设置：频率{alpha} + 遗漏{beta} + 热度{gamma}")
        print()
        
        # 红球得分
        self.red_scores = {}
        max_freq = max(self.red_freq.values())
        max_missing = max(self.red_missing.values())
        max_hot = max(self.red_hot.values()) if max(self.red_hot.values()) > 0 else 1
        
        for num in self.red_range:
            freq_score = self.red_freq[num] / max_freq
            missing_score = self.red_missing[num] / max_missing
            hot_score = self.red_hot[num] / max_hot
            
            # 综合得分
            total_score = alpha * freq_score + beta * missing_score + gamma * hot_score
            self.red_scores[num] = total_score
        
        # 蓝球得分
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
        
        # 显示得分排名
        red_sorted = sorted(self.red_scores.items(), key=lambda x: x[1], reverse=True)
        blue_sorted = sorted(self.blue_scores.items(), key=lambda x: x[1], reverse=True)
        
        print("红球综合得分TOP15：")
        for num, score in red_sorted[:15]:
            print(f"  {num:02d}: {score:.4f}")
        
        print("\n蓝球综合得分TOP5：")
        for num, score in blue_sorted[:5]:
            print(f"  {num:02d}: {score:.4f}")
        print()
        
        return self.red_scores, self.blue_scores

    def predict_normal(self):
        """正常预测方案"""
        print("=" * 60)
        print("【预测方案A】正常统计预测")
        print("=" * 60)
        
        # 按得分排序选择红球
        red_sorted = sorted(self.red_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 选择得分最高的号码，但要考虑组合特征
        candidates = [num for num, _ in red_sorted[:18]]  # 候选池
        
        # 生成多组预测
        predictions = []
        
        for i in range(5):
            selected = []
            pool = candidates.copy()
            
            # 确保区间分布合理（2:2:2 或 2:3:1 等常见分布）
            target_zones = self.common_zones[i % len(self.common_zones)][0]
            z1_target, z2_target, z3_target = target_zones
            
            z1_pool = [n for n in pool if 1 <= n <= 11]
            z2_pool = [n for n in pool if 12 <= n <= 22]
            z3_pool = [n for n in pool if 23 <= n <= 33]
            
            # 按区间选择
            random.shuffle(z1_pool)
            random.shuffle(z2_pool)
            random.shuffle(z3_pool)
            
            selected.extend(z1_pool[:min(z1_target, len(z1_pool))])
            selected.extend(z2_pool[:min(z2_target, len(z2_pool))])
            selected.extend(z3_pool[:min(z3_target, len(z3_pool))])
            
            # 如果不够6个，从剩余候选中补充
            remaining = [n for n in pool if n not in selected]
            random.shuffle(remaining)
            while len(selected) < 6:
                if remaining:
                    selected.append(remaining.pop())
                else:
                    # 从全部号码中随机选
                    all_remaining = [n for n in self.red_range if n not in selected]
                    selected.append(random.choice(all_remaining))
            
            selected = sorted(selected[:6])
            
            # 选择蓝球
            blue_sorted = sorted(self.blue_scores.items(), key=lambda x: x[1], reverse=True)
            blue = blue_sorted[i % 3][0]  # 轮流选择前3个高分蓝球
            
            predictions.append((selected, blue))
        
        print("【预测原理】")
        print("基于历史数据的统计分析，综合考虑：")
        print("1. 号码出现频率（大数定律）")
        print("2. 遗漏值（回补理论）")
        print("3. 近期热度（趋势延续）")
        print("4. 区间分布（均衡原则）")
        print()
        
        print("【预测结果】")
        for i, (reds, blue) in enumerate(predictions, 1):
            red_str = '+'.join(f'{r:02d}' for r in reds)
            print(f"  第{i}组：红球 {red_str} | 蓝球 {blue:02d}")
        
        self.normal_predictions = predictions
        print()
        return predictions
    
    def predict_anti_manipulation(self):
        """反操控预测方案（如果彩票中心出诡计）"""
        print("=" * 60)
        print("【预测方案B】反操控策略")
        print("=" * 60)
        
        print("【假设前提】")
        print("如果彩票中心存在操控行为，可能的策略包括：")
        print("1. 避开热门号码组合（减少大奖分配）")
        print("2. 选择冷门号码（降低中奖概率）")
        print("3. 避开常见的号码模式")
        print("4. 人为制造'巧合'（如连号、同尾号等）")
        print()
        
        print("【反制策略】")
        print("1. 选择中等热度号码（不冷不热）")
        print("2. 避开极端组合（全大/全小/全奇/全偶）")
        print("3. 选择非常规区间分布")
        print("4. 加入随机因素打破规律")
        print()
        
        predictions = []
        
        # 策略1：选择中等得分的号码
        red_sorted = sorted(self.red_scores.items(), key=lambda x: x[1], reverse=True)
        mid_start = len(red_sorted) // 4
        mid_end = len(red_sorted) * 3 // 4
        mid_candidates = [num for num, _ in red_sorted[mid_start:mid_end]]
        
        # 策略2：选择遗漏值适中的号码
        missing_sorted = sorted(self.red_missing.items(), key=lambda x: x[1])
        mid_missing = [num for num, _ in missing_sorted[8:25]]
        
        # 策略3：混合选择
        combined = list(set(mid_candidates) & set(mid_missing))
        if len(combined) < 10:
            combined = mid_candidates
        
        for i in range(5):
            random.shuffle(combined)
            selected = []
            
            # 确保奇偶平衡
            odds = [n for n in combined if n % 2 == 1]
            evens = [n for n in combined if n % 2 == 0]
            
            # 3奇3偶 或 4奇2偶
            if i % 2 == 0:
                selected.extend(odds[:3])
                selected.extend(evens[:3])
            else:
                selected.extend(odds[:4])
                selected.extend(evens[:2])
            
            # 补充不足
            while len(selected) < 6:
                remaining = [n for n in self.red_range if n not in selected]
                selected.append(random.choice(remaining))
            
            selected = sorted(selected[:6])
            
            # 蓝球：选择中等热度
            blue_sorted = sorted(self.blue_scores.items(), key=lambda x: x[1])
            mid_blue = [num for num, _ in blue_sorted[5:11]]
            blue = random.choice(mid_blue)
            
            predictions.append((selected, blue))
        
        print("【预测结果】")
        for i, (reds, blue) in enumerate(predictions, 1):
            red_str = '+'.join(f'{r:02d}' for r in reds)
            print(f"  第{i}组：红球 {red_str} | 蓝球 {blue:02d}")
        
        self.anti_predictions = predictions
        print()
        return predictions
    
    def predict_random_enhanced(self):
        """增强随机预测（纯概率方案）"""
        print("=" * 60)
        print("【预测方案C】增强随机策略")
        print("=" * 60)
        
        print("【原理说明】")
        print("既然彩票本质是随机事件，那么任何号码组合的中奖概率相同。")
        print("此方案在随机基础上加入基本约束，确保组合合理性。")
        print()
        
        predictions = []
        
        for i in range(5):
            while True:
                # 随机选择6个红球
                reds = sorted(random.sample(list(self.red_range), 6))
                
                # 检查和值是否在合理范围
                total = sum(reds)
                if not (self.sum_range[0] <= total <= self.sum_range[1]):
                    continue
                
                # 检查奇偶比
                odd_count = sum(1 for r in reds if r % 2 == 1)
                if odd_count < 2 or odd_count > 4:
                    continue
                
                # 检查区间分布
                z1 = sum(1 for r in reds if 1 <= r <= 11)
                z2 = sum(1 for r in reds if 12 <= r <= 22)
                z3 = sum(1 for r in reds if 23 <= r <= 33)
                if z1 == 0 or z2 == 0 or z3 == 0:
                    continue
                
                break
            
            blue = random.choice(list(self.blue_range))
            predictions.append((reds, blue))
        
        print("【预测结果】")
        for i, (reds, blue) in enumerate(predictions, 1):
            red_str = '+'.join(f'{r:02d}' for r in reds)
            print(f"  第{i}组：红球 {red_str} | 蓝球 {blue:02d}")
        
        self.random_predictions = predictions
        print()
        return predictions

    def run_full_analysis(self):
        """运行完整分析流程"""
        print("\n" + "★" * 60)
        print("       中国福利彩票双色球智能预测系统")
        print("★" * 60)
        print()
        
        # 1. 加载数据
        self.load_data()
        
        # 2. 频率分析
        self.analyze_frequency()
        
        # 3. 遗漏分析
        self.analyze_missing()
        
        # 4. 冷热分析
        self.analyze_hot_cold()
        
        # 5. 奇偶分析
        self.analyze_odd_even()
        
        # 6. 区间分析
        self.analyze_zones()
        
        # 7. 和值分析
        self.analyze_sum()
        
        # 8. 连号分析
        self.analyze_consecutive()
        
        # 9. 计算综合得分
        self.calculate_scores()
        
        # 10. 生成预测
        print("\n" + "★" * 60)
        print("       预测结果汇总")
        print("★" * 60)
        print()
        
        self.predict_normal()
        self.predict_anti_manipulation()
        self.predict_random_enhanced()
        
        # 最终推荐
        self.print_final_recommendation()
    
    def print_final_recommendation(self):
        """打印最终推荐"""
        print("=" * 60)
        print("【最终推荐】下一期预测号码")
        print("=" * 60)
        
        # 从三种方案中各选一组作为推荐
        print("\n★ 主推方案（统计分析）：")
        reds, blue = self.normal_predictions[0]
        red_str = '+'.join(f'{r:02d}' for r in reds)
        print(f"   红球：{red_str}")
        print(f"   蓝球：{blue:02d}")
        
        print("\n★ 备选方案（反操控）：")
        reds, blue = self.anti_predictions[0]
        red_str = '+'.join(f'{r:02d}' for r in reds)
        print(f"   红球：{red_str}")
        print(f"   蓝球：{blue:02d}")
        
        print("\n★ 随机方案（纯概率）：")
        reds, blue = self.random_predictions[0]
        red_str = '+'.join(f'{r:02d}' for r in reds)
        print(f"   红球：{red_str}")
        print(f"   蓝球：{blue:02d}")
        
        print("\n" + "=" * 60)
        print("【重要提示】")
        print("=" * 60)
        print("""
1. 彩票是随机事件，任何预测方法都无法保证中奖
2. 本程序仅供学习和娱乐，请理性购彩
3. 切勿沉迷赌博，量力而行
4. 中奖概率极低，请勿投入过多资金

【双色球中奖概率】
- 一等奖（6红+1蓝）：1/17,721,088
- 二等奖（6红+0蓝）：1/1,107,568
- 三等奖（5红+1蓝）：1/52,360
- 四等奖（5红+0蓝/4红+1蓝）：1/2,618
- 五等奖（4红+0蓝/3红+1蓝）：1/131
- 六等奖（2红+1蓝/1红+1蓝/0红+1蓝）：1/15
""")


def print_mathematical_formulas():
    """打印数学公式说明"""
    print("\n" + "=" * 60)
    print("【数学公式与原理说明】")
    print("=" * 60)
    print("""
【1. 频率计算】
   频率 P(n) = 号码n出现次数 / 总期数
   
   例：如果号码07在1000期中出现了200次
   P(07) = 200/1000 = 0.20

【2. 遗漏值计算】
   遗漏值 M(n) = 当前期数 - 号码n最后出现的期数
   
   理论遗漏 T(n) = 总期数 / 号码n出现次数
   
   遗漏比 R(n) = M(n) / T(n)
   当R(n) > 1时，该号码"欠出"

【3. 热度指数】
   热度 H(n) = 近N期出现次数 / N
   
   加权热度 WH(n) = Σ(出现权重 × 时间衰减因子)
   时间衰减因子 = e^(-λ×距今期数)

【4. 综合得分公式】
   Score(n) = α×Freq_score + β×Missing_score + γ×Hot_score
   
   其中：
   - α = 0.25 (频率权重)
   - β = 0.35 (遗漏权重)  
   - γ = 0.40 (热度权重)
   
   各分项归一化：score = value / max_value

【5. 组合概率】
   红球组合数 C(33,6) = 33!/(6!×27!) = 1,107,568
   蓝球选择数 = 16
   总组合数 = 1,107,568 × 16 = 17,721,088
   
   一等奖概率 = 1/17,721,088 ≈ 0.0000000564

【6. 期望值计算】
   E(收益) = Σ(中奖概率 × 奖金) - 投注金额
   
   以2元投注为例：
   E ≈ (1/17721088×500万 + 1/1107568×20万 + ...) - 2
   E ≈ -0.5元（负期望）

【7. 大数定律应用】
   当样本量n→∞时，样本频率→理论概率
   
   对于双色球红球：
   理论频率 = 6/33 ≈ 0.182
   
   偏离度 D(n) = |实际频率 - 理论频率|
   偏离度大的号码可能存在"回归"趋势
""")


def main():
    """主函数"""
    # 打印数学公式说明
    print_mathematical_formulas()
    
    # 创建预测器并运行
    predictor = LotteryPredictor('1.txt')
    predictor.run_full_analysis()


if __name__ == '__main__':
    main()
