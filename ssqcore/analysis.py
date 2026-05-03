from collections import Counter

def frequency_analysis(records, recent_n=None):
    """频率分析：统计各号码出现次数"""
    data = records[-recent_n:] if recent_n else records
    red_counter = Counter()
    blue_counter = Counter()
    for record in data:
        red_counter.update(record['red'])
        blue_counter[record['blue']] += 1
    return red_counter, blue_counter

def missing_analysis(records):
    """遗漏分析：计算各号码距离上次出现的期数"""
    red_missing = {i: len(records) for i in range(1, 34)}
    blue_missing = {i: len(records) for i in range(1, 17)}
    for idx, record in enumerate(reversed(records)):
        for num in record['red']:
            if red_missing[num] == len(records):
                red_missing[num] = idx
        if blue_missing[record['blue']] == len(records):
            blue_missing[record['blue']] = idx
    return red_missing, blue_missing

def hot_cold_analysis(records, recent_n=30):
    """冷热分析：根据近期出现频率划分冷热号"""
    red_freq, blue_freq = frequency_analysis(records, recent_n)
    red_sorted = sorted(range(1, 34), key=lambda x: red_freq.get(x, 0), reverse=True)
    hot_red = red_sorted[:11]
    warm_red = red_sorted[11:22]
    cold_red = red_sorted[22:]
    blue_sorted = sorted(range(1, 17), key=lambda x: blue_freq.get(x, 0), reverse=True)
    hot_blue = blue_sorted[:5]
    cold_blue = blue_sorted[11:]
    return {
        'hot_red': hot_red, 'warm_red': warm_red, 'cold_red': cold_red,
        'hot_blue': hot_blue, 'cold_blue': cold_blue
    }

def zone_analysis(records, recent_n=50):
    """区间分析：分析红球在三个区间的分布规律"""
    data = records[-recent_n:] if recent_n else records
    total_red = 0
    zone_counts = [0, 0, 0]  # 三区：1-11, 12-22, 23-33
    
    for record in data:
        for num in record['red']:
            total_red += 1
            if num <= 11:
                zone_counts[0] += 1
            elif num <= 22:
                zone_counts[1] += 1
            else:
                zone_counts[2] += 1
    
    if total_red == 0:
        return [1/3, 1/3, 1/3]
    
    return [count / total_red for count in zone_counts]

def odd_even_analysis(records, recent_n=50):
    """奇偶分析：分析红球奇偶比例规律"""
    data = records[-recent_n:] if recent_n else records
    total_odd = 0
    total_count = 0
    
    for record in data:
        for num in record['red']:
            total_count += 1
            if num % 2 == 1:
                total_odd += 1
    
    if total_count == 0:
        return 3.0
    
    return total_odd / len(data) if data else 3.0

def sum_analysis(records, recent_n=100):
    """和值分析：分析红球和值的分布范围"""
    data = records[-recent_n:] if recent_n else records
    
    if not data:
        return 100.0, 21, 183
    
    sums = [sum(record['red']) for record in data]
    avg_sum = sum(sums) / len(sums)
    min_sum = min(sums)
    max_sum = max(sums)
    
    return avg_sum, min_sum, max_sum

def consecutive_analysis(records, recent_n=30):
    """连号分析：分析连号出现规律"""
    data = records[-recent_n:] if recent_n else records
    consecutive_counts = []
    
    for record in data:
        red = sorted(record['red'])
        consecutive = 0
        for i in range(1, 6):
            if red[i] == red[i-1] + 1:
                consecutive += 1
        consecutive_counts.append(consecutive)
    
    if not consecutive_counts:
        return 0.0
    
    return sum(consecutive_counts) / len(consecutive_counts)

def repeat_analysis(records, recent_n=10):
    """重复号码分析：分析与上期重复的号码数量"""
    if len(records) < 2:
        return 0.0
    
    data = records[-recent_n-1:] if recent_n else records
    repeat_counts = []
    
    for i in range(1, len(data)):
        prev_red = set(data[i-1]['red'])
        curr_red = set(data[i]['red'])
        repeats = len(prev_red & curr_red)
        repeat_counts.append(repeats)
    
    if not repeat_counts:
        return 0.0
    
    return sum(repeat_counts) / len(repeat_counts)