#天气查询 Agent（手写 ReAct 循环）

不依赖 LangChain / LangGraph 等 Agent 框架，从零实现 Tool Calling 与 ReAct 循环。

## 效果

```bash
python main.py
# 请输入用户消息：明天上海天气怎么样
# 上海后天（10月19日）气温在21℃到25℃之间，降水概率约21%…
```

## 技术选型

- LLM：OpenAI 兼容协议 chat/completions
- 天气数据：wttr.in（免费、免key、支持未来 3 天预报）
- 零第三方 Agent 框架，标准库 + requests

## 架构

```
config.py         配置层。读取并校验 .env，密钥打印时脱敏
llm.py            通信层。封装 chat/completions，统一关键字传参与超时
prompts.py        系统提示词集中管理（main 与server 共用同一份）
main.py           ReAct 主循环
tools/
  schema.py       工具说明书（模型唯一可见的部分）
  tools.py        工具实现 + 函数表 + 分发入口
```

## 手写了什么

**1. 三层工具结构**
说明书（模型可见）/ 真函数 + 函数表（模型不可见）/ 分发入口。
分发入口永远返回、不抛异常——工具报错要当成"失败的观察"回灌给模型，让它自我纠错。

**2. ReAct 循环**
思考 → 调工具 → 结果回灌 → 再思考，直到模型不再要求调工具。
三层终止条件：自然终止 / 步数上限 / 同类错误早停。

**3. 工具结果归一化**
原始 JSON 提取关键字段、编码转中文、单位写进字段名、
再补上模型算不出来的派生结论（如降水概率）。

**4. 日期查询**
支持 今天 / 明天 / 后天 / YYYY-MM-DD，超范围与格式错误都返回
可操作的提示，让模型下一轮自己纠正。

## 踩过的坑

- **tool 消息的 content 必须是字符串**，dict 要先 `json.dumps`，否则 API 报 400
- **`tool_call_id` 必须带**，且与assistant 消息里的 id 配对，否则报错
- **assistant 那条消息要原样append**，不能自己拼——丢了 `tool_calls` 字段就配不上对
- **`**` 展开的键名必须和函数形参一致**，schema 字段名写错会抛 TypeError
- **`arguments` 是 JSON 字符串**，要 `json.loads` 之后才能 `**` 展开
- **模型报的名字可能和函数表对不上**，要用 `.get` 查表并返回错误而非崩溃
- **wttr.in 要用 `format=j1`**，`j2` 的 weather 数组里没有 hourly，拿不到分时数据
- **系统提示词必须写成 `{"role","content"}`**，写成字符串 dict 模型收不到约束
- **`.gitignore` 不支持行尾注释**，`ui.py  # 说明` 整行会被当成文件名

## 说明

`ui.py`（tkinter 界面）、`server.py` + `web/`（网页版）属于本地演示层，已在
`.gitignore` 中排除，不参与提交。

核心逻辑（config / llm / prompts / tools / main）全部保留在仓库中。
