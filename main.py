from tools.schema import get_weather_schemas
from llm import upload
from tools.tools import tool_call,get_weather
from tools.schema import schemas
import json
from prompts import SYSTEM_PROMPT
max_steps=20
messages=[{"role":"system","content":SYSTEM_PROMPT}]
messages_input=input("请输入用户消息：")
messages.append({"role":"user","content":messages_input})
for i in range(max_steps):
    resp=upload(messages,tools=schemas)
    if(resp["choices"][0]["message"].get("tool_calls")):
        tool_res=tool_call(resp["choices"][0]["message"]["tool_calls"][0]["function"]["name"],resp["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"])
        messages.append(resp["choices"][0]["message"])
        messages.append({"role":"tool","tool_call_id": resp["choices"][0]["message"]["tool_calls"][0]["id"]
,"content": json.dumps(tool_res, ensure_ascii=False)})
    else:
        final_res=resp["choices"][0]["message"]["content"]
        print(final_res)
        break