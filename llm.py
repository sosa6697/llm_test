"""LLM 调用模块。

读取 config 中的配置，用 requests 把请求体（messages、tools）上传到大模型接口。
后续要换成 httpx 时，改掉 requests.post 那一行即可。
"""

import requests

from config import Setting

# 单次请求超时时间（秒）
REQUEST_TIMEOUT = 60


def upload(messages, tools=None):
    """上传请求体，返回模型响应的 JSON。

    :param messages: 对话消息列表，例如 [{"role": "user", "content": "你好"}]
    :param tools: 工具（函数）定义列表；为空时请求体不带 tools 字段
    """
    setting = Setting.from_env()

    # 请求体
    payload = {
        "model": setting.model,
        "messages": messages,
        "temperature": setting.temperature,
    }
    if tools:
        payload["tools"] = tools

    # 请求头
    headers = {
        "Authorization": f"Bearer {setting.api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        setting.url,
        headers=headers,
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()
