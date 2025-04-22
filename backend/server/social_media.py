from typing import Optional, List

import requests
import json
import time
from datetime import datetime, timedelta


def fetch_news(
    keyword: str,
    page: int = 1,
    size: int = 10,
    sources: list[str] = None,
    sentiments: list[str] = None,
    start_time: str = None,
    end_time: str = None
):
    url = "https://dowding-gwa.istarshine.com/api/v3/consult/search"

    # 默认时间范围：近七天
    if not start_time or not end_time:
        now = datetime.now()
        start_dt = now - timedelta(days=3)
        end_dt = now
        if (end_dt - start_dt).days > 6:
            return {"error": "时间跨度不能超过 6 天"}
        start_time = start_dt.strftime("%Y-%m-%d 00:00:00")
        end_time = end_dt.strftime("%Y-%m-%d 23:59:59")

    # 转时间戳
    t1 = int(time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S")))
    t2 = int(time.mktime(time.strptime(end_time, "%Y-%m-%d %H:%M:%S")))

    payload = {
        "source": [
            "app", "blog", "forum", "insvideo", "news",
            "pingmei", "video", "weibo", "weixin"
        ],
        "time": [t1, t2],
        "time_filter": "ctime",
        "sort_of": ["ctime", "desc"],
        "keyword": keyword,
        "match_fields": [
            "content",
            "title",
            "retweeted.content",
            "retweeted.title"
        ],
        "size": size,
        "page": page,
        "filters": [
            {
                "field": "gather.site_name",
                "type": "input",
                "logic": "+",
                "values": sources or [
                    "新浪微博", "微信", "抖音", "西瓜", "快手", "今日头条", "小红书"
                ]
            },
            {
                "field": "analysis.sentiment",
                "logic": "+",
                "type": "input",
                "values": sentiments or ["-2","-5","-6"]  # 负面为主，包含攻击性、中性偏负等
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwOi8va3VhaXNlYXJjaC1kb3dkaW5nLmlzdGFyc2hpbmUubmV0LmNuL2FwaSIsImlhdCI6MTY5OTU4NjE2MSwibmJmIjoxNjk5NTg2MTYxLCJleHAiOjI2NDU2NjYxNjEsImRkX2FpZCI6OTAyMTUwNiwiZGRfY2lkIjoyNjY5LCJkZF9sb2UiOiIxNjYwMTI2NzE2NCIsImtzX2FpZCI6OTAyMTUwNiwiZG93ZGluZ19kZXZpY2UiOiJhcGkiLCJsb2dpbl9pZCI6ImxvZ2luX2lkX2ZFN3BnMyIsImp1bXBfYWNjb3VudF9pZCI6MCwia2V5IjoiZG93ZGluZ19wcm9kX2FpZF85MDIxNTA2In0.c5bVmFLnpAYc94HT55Q4ty_3kd8uaqx9zVs63ECfWr8'  # 注意替换真实token
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()


def fetch_data_from_api(keyword: str, sources: Optional[List[str]], sentiments: Optional[List[str]], start_time: Optional[str],
                        end_time: Optional[str]) -> dict:
    # 将时间转换为时间戳
    start_timestamp = int(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp()) if start_time else None
    end_timestamp = int(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").timestamp()) if end_time else None
    print("time", start_timestamp,end_timestamp)
    # 构造请求的 payload
    payload = {
        "source": [
            "app", "blog", "forum", "insvideo", "news", "pingmei", "video", "weibo", "weixin"
        ],
        "time": [start_timestamp, end_timestamp] if start_timestamp and end_timestamp else [],
        "time_filter": "ctime",
        "keyword": keyword,
        "match_fields": ["content", "title", "retweeted.content", "retweeted.title"],
        "filters": [
            {
                "field": "gather.site_name",
                "type": "input",
                "logic": "+",
                "values": sources or [
                    "新浪微博", "微信", "抖音", "西瓜", "快手", "今日头条", "小红书"
                ]
            },
            {
                "field": "analysis.sentiment",
                "logic": "+",
                "type": "input",
                "values": sentiments or ["-2", "-5", "-6"]  # 负面为主，包含攻击性、中性偏负等
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwOi8va3VhaXNlYXJjaC1kb3dkaW5nLmlzdGFyc2hpbmUubmV0LmNuL2FwaSIsImlhdCI6MTY5OTU4NjE2MSwibmJmIjoxNjk5NTg2MTYxLCJleHAiOjI2NDU2NjYxNjEsImRkX2FpZCI6OTAyMTUwNiwiZGRfY2lkIjoyNjY5LCJkZF9sb2UiOiIxNjYwMTI2NzE2NCIsImtzX2FpZCI6OTAyMTUwNiwiZG93ZGluZ19kZXZpY2UiOiJhcGkiLCJsb2dpbl9pZCI6ImxvZ2luX2lkX2ZFN3BnMyIsImp1bXBfYWNjb3VudF9pZCI6MCwia2V5IjoiZG93ZGluZ19wcm9kX2FpZF85MDIxNTA2In0.c5bVmFLnpAYc94HT55Q4ty_3kd8uaqx9zVs63ECfWr8'
    }
    url = "https://dowding-gwa.istarshine.com/api/v3/consult/total"

    # 发送 POST 请求
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # 如果请求成功，返回响应的 JSON 数据
    if response.status_code == 200:
        return response.json()
    else:
        return {"code": response.status_code, "msg": response.text}
