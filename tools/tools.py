import json
import requests
from datetime import datetime, timedelta
from urllib.parse import quote


def _解析日期(date_time):
    """把模型传的各种日期写法统一成 YYYY-MM-DD。

    模型可能传："今天" / "明天" / "后天" / "2026-10-18" / "" / None
    返回标准日期字符串；解析不出来返回 None（表示按今天处理）。
    """
    if not date_time:
        return None

    text = str(date_time).strip()

    # 相对日期：直接加减天数
    today = datetime.now()
    if text in ("今天", "今日", "现在", "today"):
        return today.strftime("%Y-%m-%d")
    if text in ("明天", "明日", "tomorrow"):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    if text in ("后天", "tomorrow2"):
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")
    if text in ("昨天", "昨日"):
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")

    # 绝对日期：已经是对的就直接用
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _挑当天的数据(weather_data, target_date):
    """从 wttr.in 返回的 forecast 数组里挑出目标日期那一条。

    wttr.in 只返回未来 3 天，数组里每一项代表一天。
    挑不到就返回 None。
    """
    # weather 是数组，每项是一个"日"，里面才有天气状况
    for day in weather_data.get("weather", []) or []:
        if day.get("date") == target_date:
            return day
    return None


def _取正午天气(day):
    """从某一天的 hourly 里取正午（12 点）那一条。

    hourly 数组是 00/03/06/09/12/15/18/21 点共 8 个时间点，
    time 字段的值是 "0"/"300"/"600".../"1200" 这种字符串。
    索引 4 正好是 1200（正午）。取正午比取早上更贴近出行时间。
    """
    hourly = day.get("hourly", []) or []
    if len(hourly) > 4:
        return hourly[4]
    # 数据不全时退而求其次，取第一条
    return hourly[0] if hourly else {}


def get_weather(city_name="上海", date_time=""):
    """查询指定城市指定日期的天气。

    :param city_name: 城市名
    :param date_time: 日期。支持 今天/明天/后天/YYYY-MM-DD，留空按今天处理
    """
    city_encoded = quote(city_name)
    # 必须用 j1：j2 的 weather 数组里没有 hourly，拿不到分时数据
    weather_url = "https://wttr.in/" + city_encoded + "?format=j1"

    # 先把日期算好。算不出来就用今天，并且后面会提示模型
    target_date = _解析日期(date_time)
    # 空值/None 视为"不指定日期"，直接按今天走
    if not date_time:
        target_date = datetime.now().strftime("%Y-%m-%d")

    try:
        resp_weather = requests.get(url=weather_url, timeout=15)
        resp_weather.raise_for_status()
        weather_data = resp_weather.json()
    except Exception as e:
        return "错误：查询天气失败，" + str(e)

    # ---- 分两种情况：查今天（读实时数据）/ 查未来（读预报数据）----
    today_str = datetime.now().strftime("%Y-%m-%d")

    if target_date is None:
        return (
            f"错误：无法识别日期「{date_time}」。"
            f"请使用 今天 / 明天 / 后天 或 YYYY-MM-DD 格式。"
        )

    # 查今天：current_condition 是"此刻"的实况，比预报准
    if target_date == today_str:
        current = weather_data["current_condition"][0]
        return (
            f"城市：{city_name}\n"
            f"日期：今天（{today_str}）\n"
            f"天气：{current['weatherDesc'][0]['value']}\n"
            f"当前温度：{current['temp_C']}℃\n"
            f"体感温度：{current['FeelsLikeC']}℃\n"
            f"湿度：{current['humidity']}%\n"
            f"风速：{current['windspeedKmph']} km/h"
        )

    # 查未来某天：从 forecast 里挑那一天的
    day = _挑当天的数据(weather_data, target_date)
    if day is None:
        可查范围 = [d.get("date") for d in weather_data.get("weather", []) or []]
        return (
            f"错误：只能查询未来 3 天的天气，查不到 {target_date}。"
            f"目前可查的日期：{'、'.join(可查范围)}"
        )

    noon = _取正午天气(day)
    desc = (noon.get("weatherDesc") or [{}])[0].get("value", "未知")
    # chanceofrain 是降水概率百分比，模型靠它决定要不要建议带伞
    rain_chance = noon.get("chanceofrain", "0")

    return (
        f"城市：{city_name}\n"
        f"日期：{target_date}\n"
        f"天气：{desc}\n"
        f"最高温度：{day.get('maxtempC')}℃\n"
        f"最低温度：{day.get('mintempC')}℃\n"
        f"降水概率：{rain_chance}%"
        # WindspeedKmph 在 j1 里确实存在，但值有时是字符串有时是数字，
        # 这里统一转成字符串输出，避免出现 None
        f"\n最大风速：{noon.get('WindspeedKmph', noon.get('windspeedKmph', '未知'))} km/h"
    )


tools_table = {"get_weather": get_weather}


def tool_call(tool_name, tool_args):
    """按名字分发执行工具。成功失败都返回字符串，不抛异常。"""
    tool = tools_table.get(tool_name)

    # 模型给的参数是 JSON 字符串，需要解析成 dict
    if isinstance(tool_args, str):
        try:
            tool_args = json.loads(tool_args or "{}")
        except json.JSONDecodeError as e:
            return "错误：参数不是合法 JSON，" + str(e)

    if tool is None:
        return "错误：工具不存在，可用工具：get_weather"

    try:
        return tool(**tool_args)
    except TypeError as e:
        return "错误：参数不匹配，" + str(e)
    except Exception as e:
        return "错误：" + str(e)