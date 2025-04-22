import requests
import json
# 只能查询进七天的数据
url = "https://dowding-gwa.istarshine.com/api/v3/consult/total"

payload = json.dumps({
    "source": [
        "app",
        "blog",
        "forum",
        "insvideo",
        "news",
        "pingmei",
        "video",
        "weibo",
        "weixin"
    ],
    "time": [
        1743998881,
        1744085281
    ],
    "time_filter": "ctime",
    "keyword": "小米su7",
    "match_fields": [
        "content",
        "title",
        "retweeted.content",
        "retweeted.title"
    ],
    "filters": [
        {
            "field": "gather.site_name",
            "type": "input",
            "logic": "+",
            "values": [
                "新浪微博",
                "微信",
                "抖音",
                "西瓜",
                "快手",
                "今日头条",
                "小红书"
            ]

        },
{
                "field": "analysis.sentiment",
                "logic": "+",
                "type": "input",
                "values": ["1","2"]  # 负面为主，包含攻击性、中性偏负等
            }
    ]
})
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwOi8va3VhaXNlYXJjaC1kb3dkaW5nLmlzdGFyc2hpbmUubmV0LmNuL2FwaSIsImlhdCI6MTY5OTU4NjE2MSwibmJmIjoxNjk5NTg2MTYxLCJleHAiOjI2NDU2NjYxNjEsImRkX2FpZCI6OTAyMTUwNiwiZGRfY2lkIjoyNjY5LCJkZF9sb2UiOiIxNjYwMTI2NzE2NCIsImtzX2FpZCI6OTAyMTUwNiwiZG93ZGluZ19kZXZpY2UiOiJhcGkiLCJsb2dpbl9pZCI6ImxvZ2luX2lkX2ZFN3BnMyIsImp1bXBfYWNjb3VudF9pZCI6MCwia2V5IjoiZG93ZGluZ19wcm9kX2FpZF85MDIxNTA2In0.c5bVmFLnpAYc94HT55Q4ty_3kd8uaqx9zVs63ECfWr8'
}

response = requests.post(url, headers=headers, data=payload)

print(response.text)
# from server.social_media import fetch_data_from_api
#
# result = fetch_data_from_api("小米su7",[],"2025-04-02 00:00:00","2025-04-06 23:59:59")
# print(result)