import random
from .analysis import hot_cold_analysis

def random_strategy():
    """随机策略：纯概率选号"""
    red = sorted(random.sample(range(1, 34), 6))
    blue = random.randint(1, 16)
    return red, blue

def hot_cold_strategy(records):
    """冷热号策略：选热号+冷号混合"""
    hot_cold = hot_cold_analysis(records, 30)
    hot = random.sample(hot_cold['hot_red'], 3)
    cold = random.sample(hot_cold['cold_red'], 3)
    red = sorted(hot + cold)
    blue = random.choice(hot_cold['hot_blue'] + hot_cold['cold_blue'])
    return red, blue
