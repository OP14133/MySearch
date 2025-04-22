import random
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
from qdata.baidu_index import get_search_index, PROVINCE_CODE

BAIDU_COOKIES = [
    'BDUSS=U4yLUthcjZvTTZ0TFBQYWgyVXFPWWlPekJTenlTZTVycFV4Y2hWZTdiMWVxb1ptRVFBQUFBJCQAAAAAAQAAAAEAAAAzcE0GR1EyNjkxAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAF4dX2ZeHV9mc'
]

PROVINCE_NAME_MAP = {
    '北京': '北京市',
    '天津': '天津市',
    '上海': '上海市',
    '重庆': '重庆市',
    '内蒙古': '内蒙古自治区',
    '广西': '广西壮族自治区',
    '西藏': '西藏自治区',
    '宁夏': '宁夏回族自治区',
    '新疆': '新疆维吾尔自治区',
    '香港': '香港特别行政区',
    '澳门': '澳门特别行政区'
}


def validate_time_range(time_range: str) -> datetime:
    valid_ranges = ['7', '30', '90', '180', 'all']
    if time_range not in valid_ranges:
        raise ValueError(f"无效的时间范围参数，有效值为: {', '.join(valid_ranges)}")
    return valid_ranges


def validate_area(area: str) -> str:
    if area and area not in PROVINCE_CODE.values():
        raise ValueError("无效的地区代码")
    return area


def get_index_data(keyword: str, start_date: str, end_date: str, area: str) -> pd.DataFrame:
    """ 获取百度指数数据 """
    try:
        cookie = random.choice(BAIDU_COOKIES)
        data_list = list(get_search_index(
            keywords_list=[[keyword]],
            start_date=start_date,
            end_date=end_date,
            cookies=cookie,
            area=area
        ))
        df = pd.DataFrame(data_list)
        if df.empty:
            raise ValueError("未找到数据")
        return df
    except Exception as e:
        logging.error(f"获取百度指数数据失败: {str(e)}")
        raise


def get_province_data(province_item, keywords_list, start_date, end_date):
    """获取单个省份的百度指数数据"""
    province_name, province_code = province_item
    logging.info(f'正在获取{province_name}的数据...')

    cookie = random.choice(BAIDU_COOKIES)
    time.sleep(random.uniform(0.5, 2.0))  # 添加随机短延时

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            baidu_list = list(get_search_index(
                keywords_list=keywords_list,
                start_date=start_date,
                end_date=end_date,
                cookies=cookie,
                area=int(province_code)
            ))

            data = pd.DataFrame(baidu_list)
            if data.empty:
                return None

            province_name_formatted = PROVINCE_NAME_MAP.get(province_name, province_name + '省')
            data['province'] = province_name_formatted
            data['keyword'] = data['keyword'].apply(lambda x: x[0])
            data['index'] = data['index'].astype('int')
            data['year'] = data.date.apply(lambda x: x.split('-')[0])

            # 统计数据
            data_stats = data.groupby(
                ['province', 'keyword', 'year', 'type'],
                as_index=False
            )['index'].agg({
                'mean': 'mean',
                'max': 'max',
                'sum': 'sum'
            })

            return data_stats

        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"获取{province_name}数据时出错(尝试 {attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(retry_delay * (2 ** attempt))  # 增加重试间隔
                if len(BAIDU_COOKIES) > 1:
                    cookie = random.choice([c for c in BAIDU_COOKIES if c != cookie])
            else:
                logging.error(f"获取{province_name}数据失败，已达到最大重试次数: {str(e)}")
                return None
