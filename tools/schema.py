get_weather_schemas = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "查询指定城市指定日期的天气，返回天气描述、最高最低气温、降水概率。"
            "当用户询问某个城市某天的天气时使用。"
            "只能查询今天及未来 3 天，无法查询历史。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city_name": {
                    "type": "string",
                    "description": "城市名，例如 上海、北京。不要带「市」字。",
                },
                "date_time": {
                    "type": "string",
                    "description": (
                        "日期。不填默认为今天。支持三种写法："
                        "相对日期（今天/明天/后天）或绝对日期（2026-10-18）。"
                    ),
                },
            },
            # 不设 required：模型可以不传 city_name 和 date_time，
            # 都会走函数里的默认值（上海 / 今天）
        },
    },
}

schemas = [get_weather_schemas]