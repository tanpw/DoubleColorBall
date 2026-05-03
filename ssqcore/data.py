import requests
import csv
import re
from datetime import datetime, timedelta

def smart_parse_numbers(numbers_str):
    """智能解析开奖号码字符串

    双色球规则：6个红球(1-33) + 1个蓝球(1-16)
    号码可能是1位或2位数字连续排列
    """
    def try_parse(s, balls, is_blue=False):
        if is_blue:
            if len(s) == 0:
                return None
            for length in [2, 1]:
                if len(s) >= length:
                    num = int(s[:length])
                    if 1 <= num <= 16:
                        return balls, num
            return None

        if len(balls) == 6:
            return try_parse(s, balls, is_blue=True)

        if len(s) == 0:
            return None

        for length in [2, 1]:
            if len(s) >= length:
                num = int(s[:length])
                if 1 <= num <= 33 and num not in balls:
                    result = try_parse(s[length:], balls + [num], False)
                    if result:
                        return result

        return None

    result = try_parse(numbers_str, [])
    if result:
        red_balls, blue_ball = result
        if red_balls == sorted(red_balls):
            return red_balls, blue_ball

    return None

def parse_txt_format(lines):
    """解析txt格式数据"""
    records = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        patterns = [
            r'(\d{7})\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}[^\d]*?)+(\d{1,2})',
            r'(\d{7})\s+(\d{4}/\d{2}/\d{2})\s+(\d{1,2}[^\d]*?)+(\d{1,2})',
            r'(\d{7}).*?(\d{4}-\d{2}-\d{2}).*?([\d+]+)',
            r'(\d{7}).*?(\d{4}-\d{2}-\d{2}).*?(\d{12})(\d{2})',
        ]

        matched = False
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                issue = match.group(1)
                date_str = match.group(2).replace('/', '-')
                numbers_part = match.group(3)

                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
                except:
                    continue

                if len(numbers_part) >= 12:
                    parsed = smart_parse_numbers(numbers_part.replace('+', '').replace(' ', ''))
                    if parsed:
                        red, blue = parsed
                        records.append({
                            'issue': issue,
                            'date': date,
                            'red': red,
                            'blue': blue
                        })
                        matched = True
                        break

        if not matched:
            parts = re.split(r'\s+', line)
            if len(parts) >= 3:
                issue = parts[0]
                date_str = parts[1]
                numbers = ''.join(parts[2:]).replace('+', '').replace('-', '')

                try:
                    date = datetime.strptime(date_str.replace('/', '-'), '%Y-%m-%d').strftime('%Y-%m-%d')
                except:
                    continue

                parsed = smart_parse_numbers(numbers)
                if parsed:
                    red, blue = parsed
                    records.append({
                        'issue': issue,
                        'date': date,
                        'red': red,
                        'blue': blue
                    })

    return records

def parse_csv_format(lines):
    """解析csv格式数据"""
    records = []
    reader = csv.reader(lines)
    header_skipped = False

    for row in reader:
        if not header_skipped:
            header_skipped = True
            continue

        if len(row) < 4:
            continue

        issue = row[0].strip()
        date_str = row[1].strip()
        red_str = row[2].strip()
        blue_str = row[3].strip()

        try:
            date = datetime.strptime(date_str.replace('/', '-'), '%Y-%m-%d').strftime('%Y-%m-%d')
        except:
            continue

        try:
            red = sorted([int(x.strip()) for x in red_str.split('+') if x.strip()])
        except:
            red = []

        try:
            blue = int(blue_str)
        except:
            continue

        if len(red) == 6 and all(1 <= x <= 33 for x in red) and 1 <= blue <= 16:
            records.append({
                'issue': issue,
                'date': date,
                'red': red,
                'blue': blue
            })

    return records

def parse_lottery_data(filename):
    """
    解析双色球历史数据，支持多种格式（txt/csv）
    """
    records = []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        if filename.lower().endswith('.csv'):
            records = parse_csv_format(lines)
        else:
            records = parse_txt_format(lines)

        if not records:
            print(f"警告：未能从 {filename} 解析到有效数据，尝试其他格式...")
            records = parse_csv_format(lines)

    except FileNotFoundError:
        print(f"错误：文件 {filename} 不存在")
    except Exception as e:
        print(f"解析文件时发生错误：{e}")

    return sorted(records, key=lambda x: x['issue'])

API_LIST = [
    {
        'name': '彩票之家',
        'type': 'huiniao',
        'url': 'http://api.huiniao.top/interface/home/lotteryHistory?type=ssq&page={page}&limit=20',
        'has_page': True
    },
    {
        'name': '中国福利彩票官网',
        'type': 'cwl',
        'url': 'https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo=01&provinceId=0&pageSize=100&pageNo={page}',
        'has_page': True
    }
]

def fetch_latest_lottery_data(api_url=None, save_path='lottery_data.csv'):
    """
    自动下载最新双色球开奖数据，保存为csv文件。
    """
    print("正在尝试在线更新数据...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    if api_url:
        success = _fetch_from_url(api_url, save_path, headers)
        if success:
            return True

    for api in API_LIST:
        print(f"尝试API: {api['name']}")
        url = api['url'].format(page=1)

        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()

                if api['type'] == 'huiniao':
                    if _parse_huiniao_data(data, save_path):
                        print(f"数据更新成功！已保存到 {save_path}")
                        return True

                elif api['type'] == 'cwl':
                    if _parse_cwl_data(data, save_path):
                        print(f"数据更新成功！已保存到 {save_path}")
                        return True

        except requests.exceptions.RequestException as e:
            print(f"  请求失败: {e}")
        except Exception as e:
            print(f"  解析失败: {e}")

        if api.get('has_page'):
            for page in range(2, 6):
                url = api['url'].format(page=page)
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        if api['type'] == 'huiniao':
                            if _parse_huiniao_data(data, save_path):
                                print(f"数据更新成功！已保存到 {save_path}")
                                return True
                        elif api['type'] == 'cwl':
                            if _parse_cwl_data(data, save_path):
                                print(f"数据更新成功！已保存到 {save_path}")
                                return True
                except:
                    break

    print("\n在线API暂时不可用，建议手动下载数据")
    print("可从以下网站下载:")
    print("  - https://www.cwl.gov.cn/ssq/")
    print("  - https://caipiao.163.com/order/ssq/")
    print("保存为 .txt 或 .csv 格式后使用'加载数据'功能导入")
    return False

def _fetch_from_url(url, save_path, headers):
    """从指定URL获取数据"""
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()

            if 'value' in data and 'list' in data['value']:
                return _parse_cwl_data(data, save_path)
            elif 'data' in data:
                return _parse_huiniao_data(data, save_path)

    except Exception as e:
        print(f"请求失败: {e}")

    return False

def _parse_huiniao_data(data, save_path):
    """解析彩票之家API数据"""
    try:
        if data.get('code') != 1:
            return False

        records = []
        all_data = data.get('data', {})

        last_data = all_data.get('last', {})
        if last_data:
            records.append({
                'issue': last_data.get('code', ''),
                'date': last_data.get('day', ''),
                'red': [int(last_data.get('one', 0)), int(last_data.get('two', 0)),
                        int(last_data.get('three', 0)), int(last_data.get('four', 0)),
                        int(last_data.get('five', 0)), int(last_data.get('six', 0))],
                'blue': int(last_data.get('seven', 0))
            })

        list_data = all_data.get('data', {}).get('list', [])
        for item in list_data:
            records.append({
                'issue': item.get('code', ''),
                'date': item.get('day', ''),
                'red': [int(item.get('one', 0)), int(item.get('two', 0)),
                        int(item.get('three', 0)), int(item.get('four', 0)),
                        int(item.get('five', 0)), int(item.get('six', 0))],
                'blue': int(item.get('seven', 0))
            })

        if not records:
            return False

        with open(save_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['issue', 'date', 'red', 'blue'])
            for record in records:
                writer.writerow([
                    record['issue'],
                    record['date'],
                    '+'.join(f"{n:02d}" for n in sorted(record['red'])),
                    f"{record['blue']:02d}"
                ])

        return True

    except Exception as e:
        print(f"解析失败: {e}")
        return False

def _parse_cwl_data(data, save_path):
    """解析体彩网API数据"""
    try:
        if data.get('success') is False:
            return False

        if 'value' not in data or 'list' not in data['value']:
            return False

        records = []
        for item in data['value']['list']:
            red_balls = item.get('red', '').split(',')
            blue_ball = item.get('blue', '')
            records.append({
                'issue': item.get('issue', ''),
                'date': item.get('date', ''),
                'red': '+'.join(red_balls),
                'blue': blue_ball
            })

        if not records:
            return False

        with open(save_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['issue', 'date', 'red', 'blue'])
            for record in records:
                writer.writerow([
                    record['issue'],
                    record['date'],
                    record['red'],
                    record['blue']
                ])

        return True

    except Exception as e:
        print(f"解析失败: {e}")
        return False

def generate_sample_data(count=50, save_path='2013-2026.txt'):
    """生成示例数据（用于测试）"""
    import random

    records = []
    base_issue = 2025001
    base_date = datetime(2025, 1, 1)

    for i in range(count):
        red = sorted(random.sample(range(1, 34), 6))
        blue = random.randint(1, 16)

        issue = f"{base_issue + i:07d}"
        date = (base_date + timedelta(days=i * 7)).strftime('%Y-%m-%d')

        records.append(f"{issue} {date} " + " ".join(f"{n:02d}" for n in red) + f" {blue:02d}")

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(records))

    print(f"已生成 {count} 条示例数据到 {save_path}")
    return True