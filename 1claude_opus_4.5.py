"""
双色球预测程序claude_opus_4.5
================
分析原理：
1. 频率分析：统计历史开奖中各号码出现的频率
2. 遗漏分析：计算各号码距离上次出现的期数（遗漏值）
3. 冷热分析：根据近期出现频率划分冷热号
4. 奇偶分析：分析红球奇偶比例规律
5. 区间分析：分析红球在三个区间的分布规律
6. 和值分析：分析红球和值的分布范围

注意：彩票开奖是随机事件，任何预测方法都不能保证中奖，仅供娱乐参考！
"""

import logging
import argparse
import random
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ssq_predict.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from ssqcore.data import parse_lottery_data, fetch_latest_lottery_data
    from ssqcore.analysis import (
        frequency_analysis, missing_analysis, hot_cold_analysis,
        zone_analysis, odd_even_analysis, sum_analysis,
        consecutive_analysis, repeat_analysis
    )
    from ssqcore.strategy import random_strategy, hot_cold_strategy
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    print(f"错误：无法导入 ssqcore 模块 - {e}")
    sys.exit(1)

def predict_numbers(records):
    """综合预测下一期号码"""
    logger.info(f"开始分析，共 {len(records)} 期历史数据")
    
    print("=" * 60)
    print("双色球预测分析报告")
    print("=" * 60)
    print(f"分析数据：共 {len(records)} 期历史开奖记录")
    print(f"最新一期：{records[-1]['issue']} ({records[-1]['date']})")
    print(f"开奖号码：红球 {records[-1]['red']} 蓝球 {records[-1]['blue']}")
    print()
    
    # 1. 频率分析
    print("【一、频率分析】")
    red_freq, blue_freq = frequency_analysis(records)
    red_top10 = sorted(range(1, 34), key=lambda x: red_freq.get(x, 0), reverse=True)[:10]
    blue_top5 = sorted(range(1, 17), key=lambda x: blue_freq.get(x, 0), reverse=True)[:5]
    print(f"红球出现最多的10个号码：{red_top10}")
    print(f"蓝球出现最多的5个号码：{blue_top5}")
    print()
    
    # 2. 遗漏分析
    print("【二、遗漏分析】")
    red_missing, blue_missing = missing_analysis(records)
    red_high_missing = sorted(range(1, 34), key=lambda x: red_missing[x], reverse=True)[:10]
    blue_high_missing = sorted(range(1, 17), key=lambda x: blue_missing[x], reverse=True)[:5]
    print(f"红球遗漏值最高的10个号码：{red_high_missing}")
    print(f"  对应遗漏值：{[red_missing[n] for n in red_high_missing]}")
    print(f"蓝球遗漏值最高的5个号码：{blue_high_missing}")
    print(f"  对应遗漏值：{[blue_missing[n] for n in blue_high_missing]}")
    print()
    
    # 3. 冷热分析
    print("【三、冷热分析（近30期）】")
    hot_cold = hot_cold_analysis(records, 30)
    print(f"热号（出现频繁）：{sorted(hot_cold['hot_red'])}")
    print(f"温号（出现适中）：{sorted(hot_cold['warm_red'])}")
    print(f"冷号（出现较少）：{sorted(hot_cold['cold_red'])}")
    print(f"蓝球热号：{sorted(hot_cold['hot_blue'])}")
    print()
    
    # 4. 区间分析
    print("【四、区间分析（近50期）】")
    zone_ratio = zone_analysis(records, 50)
    print(f"一区(01-11)占比：{zone_ratio[0]:.1%}")
    print(f"二区(12-22)占比：{zone_ratio[1]:.1%}")
    print(f"三区(23-33)占比：{zone_ratio[2]:.1%}")
    print()
    
    # 5. 奇偶分析
    print("【五、奇偶分析（近50期）】")
    avg_odd = odd_even_analysis(records, 50)
    print(f"平均每期奇数个数：{avg_odd:.2f}")
    print(f"建议奇偶比：{round(avg_odd)}:{6-round(avg_odd)}")
    print()
    
    # 6. 和值分析
    print("【六、和值分析（近100期）】")
    avg_sum, min_sum, max_sum = sum_analysis(records, 100)
    print(f"平均和值：{avg_sum:.1f}")
    print(f"和值范围：{min_sum} - {max_sum}")
    print()
    
    # 7. 连号分析
    print("【七、连号分析（近30期）】")
    avg_consecutive = consecutive_analysis(records, 30)
    print(f"平均每期连号组数：{avg_consecutive:.2f}")
    print()
    
    # 8. 重复号码分析
    print("【八、重复号码分析（近10期）】")
    avg_repeat = repeat_analysis(records, 10)
    print(f"平均每期与上期重复号码数：{avg_repeat:.2f}")
    print()
    
    # 综合预测
    print("=" * 60)
    print("【综合预测结果】")
    print("=" * 60)
    
    predicted_red = generate_red_balls(records, red_freq, red_missing, hot_cold, zone_ratio, avg_odd, avg_sum)
    predicted_blue = generate_blue_ball(records, blue_freq, blue_missing, hot_cold)
    
    print(f"\n预测红球：{sorted(predicted_red)}")
    print(f"预测蓝球：{predicted_blue}")
    print()
    print("=" * 60)
    print("【免责声明】")
    print("彩票开奖为随机事件，本预测仅基于历史数据统计分析，")
    print("不能保证中奖，仅供娱乐参考，请理性购彩！")
    print("=" * 60)
    
    logger.info(f"预测完成：红球 {sorted(predicted_red)}，蓝球 {predicted_blue}")
    
    return sorted(predicted_red), predicted_blue

def generate_red_balls(records, red_freq, red_missing, hot_cold, zone_ratio, avg_odd, avg_sum):
    """生成预测红球"""
    candidates = []
    
    for num in range(1, 34):
        score = 0
        
        freq_score = red_freq.get(num, 0) / max(red_freq.values()) * 30 if red_freq else 15
        score += freq_score
        
        missing_score = min(red_missing[num], 20) * 1.5
        score += missing_score
        
        if num in hot_cold['hot_red']:
            score += 15
        elif num in hot_cold['warm_red']:
            score += 10
        else:
            score += 5
        
        candidates.append((num, score))
    
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    selected = []
    zone_target = [round(zone_ratio[0] * 6), round(zone_ratio[1] * 6), round(zone_ratio[2] * 6)]
    
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
        
        if num <= 11:
            zone = 0
        elif num <= 22:
            zone = 1
        else:
            zone = 2
        
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

def generate_blue_ball(records, blue_freq, blue_missing, hot_cold):
    """生成预测蓝球"""
    candidates = []
    
    for num in range(1, 17):
        score = 0
        
        freq_score = blue_freq.get(num, 0) / max(blue_freq.values()) * 40 if blue_freq else 20
        score += freq_score
        
        missing_score = min(blue_missing[num], 15) * 2
        score += missing_score
        
        if num in hot_cold['hot_blue']:
            score += 20
        
        candidates.append((num, score))
    
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]

def plot_frequency(red_counter, blue_counter):
    """绘制红球和蓝球出现频率柱状图"""
    try:
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        plt.bar(list(red_counter.keys()), list(red_counter.values()), color='red')
        plt.title('红球出现频率')
        plt.xlabel('红球号码')
        plt.ylabel('出现次数')
        plt.xticks(range(1, 34, 3))
        
        plt.subplot(1, 2, 2)
        plt.bar(list(blue_counter.keys()), list(blue_counter.values()), color='blue')
        plt.title('蓝球出现频率')
        plt.xlabel('蓝球号码')
        plt.ylabel('出现次数')
        plt.xticks(range(1, 17))
        
        plt.tight_layout()
        plt.show()
    except ImportError as e:
        logger.warning(f"无法绘制图表：{e}")
        print("警告：无法绘制图表，可能缺少 matplotlib 库")

def batch_predict(records, count=5):
    """多期批量预测"""
    print(f"\n【多期批量预测 - 共 {count} 期】")
    print("=" * 60)
    
    predictions = []
    for i in range(count):
        red, blue = predict_numbers(records)
        predictions.append((i + 1, red, blue))
        print(f"第 {i + 1} 期预测：红球 {red} 蓝球 {blue}")
    
    return predictions

def backtest(records, test_count=10):
    """历史回测"""
    if len(records) < test_count + 1:
        print("错误：数据量不足，无法进行回测")
        return
    
    print(f"\n【历史回测 - 最近 {test_count} 期】")
    print("=" * 60)
    
    total_matches = 0
    total_red_matches = 0
    total_blue_matches = 0
    
    for i in range(test_count):
        train_data = records[:-(test_count - i)]
        actual = records[-(test_count - i)]
        
        if not train_data:
            continue
        
        predicted_red, predicted_blue = predict_numbers(train_data)
        
        red_match = len(set(predicted_red) & set(actual['red']))
        blue_match = 1 if predicted_blue == actual['blue'] else 0
        
        total_red_matches += red_match
        total_blue_matches += blue_match
        total_matches += red_match + blue_match
        
        print(f"期号 {actual['issue']}: 预测红球{predicted_red}蓝球{predicted_blue} | "
              f"实际红球{actual['red']}蓝球{actual['blue']} | "
              f"命中红球{red_match}个，蓝球{blue_match}个")
    
    print("=" * 60)
    print(f"回测结果：共测试 {test_count} 期")
    print(f"平均每期命中红球：{total_red_matches / test_count:.2f} 个")
    print(f"平均每期命中蓝球：{total_blue_matches / test_count:.2f} 个")
    print(f"总命中率：{(total_matches / (test_count * 7)) * 100:.1f}%")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='双色球智能分析与预测')
    parser.add_argument('--plot', action='store_true', help='显示频率分析图表')
    parser.add_argument('--data', type=str, default='2013-2026.txt', help='历史数据文件')
    parser.add_argument('--strategy', type=str, default='default', 
                        choices=['default', 'random', 'hotcold'], help='预测策略')
    parser.add_argument('--batch', type=int, default=0, help='多期批量预测期数')
    parser.add_argument('--backtest', type=int, default=0, help='历史回测期数')
    parser.add_argument('--update', action='store_true', help='自动更新最新开奖数据')
    
    args = parser.parse_args()
    
    logger.info(f"程序启动，参数：{args}")
    
    if args.update:
        print("正在尝试自动下载最新开奖数据...")
        success = fetch_latest_lottery_data()
        if success:
            args.data = 'lottery_data.csv'
        else:
            print("自动更新失败，使用本地数据文件")
    
    if not os.path.exists(args.data):
        print(f"错误：数据文件 {args.data} 不存在")
        logger.error(f"数据文件不存在：{args.data}")
        return
    
    print('\n正在加载历史数据...')
    records = parse_lottery_data(args.data)
    
    if not records:
        print('错误：未能解析到有效的开奖数据！')
        logger.error("未能解析到有效的开奖数据")
        return
    
    print(f'成功加载 {len(records)} 期开奖记录')
    print(f'数据范围：{records[0]["issue"]} 至 {records[-1]["issue"]}')
    print()
    
    if args.backtest > 0:
        backtest(records, args.backtest)
        return
    
    if args.batch > 0:
        batch_predict(records, args.batch)
        return
    
    if args.strategy == 'random':
        red_balls, blue_ball = random_strategy()
        print('【随机策略】')
    elif args.strategy == 'hotcold':
        red_balls, blue_ball = hot_cold_strategy(records)
        print('【冷热号策略】')
    else:
        red_balls, blue_ball = predict_numbers(records)
        print('【默认智能策略】')
    
    print(f'预测红球：{red_balls}')
    print(f'预测蓝球：{blue_ball}')
    
    if args.plot:
        red_counter, blue_counter = frequency_analysis(records)
        plot_frequency(red_counter, blue_counter)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception("程序运行异常")
        print(f"程序运行异常：{e}")
        sys.exit(1)