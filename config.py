"""配置模块。

从同目录下的 .env 读取配置，校验合法性后封装成 Setting 类。
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# .env 文件的绝对路径（与当前文件同目录）
ENV_PATH = Path(__file__).resolve().parent / ".env"

# TEMPERATURE 留空时使用的默认值
DEFAULT_TEMPERATURE = 0.7
# 常见大模型 temperature 的取值范围
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0

# MAXSTEPS 留空时使用的默认值
DEFAULT_MAXSTEPS = 5


class Setting:
    """封装 .env 中的配置，构造时完成合法性校验。"""

    def __init__(self, url: str, api_key: str, temperature: float, model: str, maxsteps: int) -> None:
        self.url = url
        self.api_key = api_key
        self.temperature = temperature
        self.model = model
        self.maxsteps = maxsteps

    @classmethod
    def from_env(cls, env_path: Path | str = ENV_PATH) -> "Setting":
        """读取 .env 文件，返回一个已通过校验的 Setting 实例。"""
        env_path = Path(env_path)
        if not env_path.is_file():
            raise FileNotFoundError(f"找不到配置文件: {env_path}")

        load_dotenv(env_path)

        setting = cls(
            url=(os.getenv("URL") or "").strip(),
            api_key=(os.getenv("APIKEY") or "").strip(),
            temperature=cls._parse_temperature((os.getenv("TEMPERATURE") or "").strip()),
            model=(os.getenv("MODEL") or "").strip(),
            maxsteps=cls._parse_maxsteps((os.getenv("MAXSTEPS") or "").strip()),
        )
        setting.validate()
        return setting

    @staticmethod
    def _parse_temperature(text: str) -> float:
        """把 TEMPERATURE 文本转成 float，留空则使用默认值。"""
        if not text:
            return DEFAULT_TEMPERATURE
        try:
            return float(text)
        except ValueError:
            raise ValueError(f"TEMPERATURE 必须是数字，当前值为: {text!r}") from None

    @staticmethod
    def _parse_maxsteps(text: str) -> int:
        """把 MAXSTEPS 文本转成 int，留空则使用默认值。"""
        if not text:
            return DEFAULT_MAXSTEPS
        try:
            return int(text)
        except ValueError:
            raise ValueError(f"MAXSTEPS 必须是整数，当前值为: {text!r}") from None

    def validate(self) -> None:
        """校验各项配置是否合法，不合法时抛出 ValueError 并列出全部问题。"""
        errors: list[str] = []

        if not self.url:
            errors.append("URL 不能为空")
        elif not self.url.startswith(("http://", "https://")):
            errors.append(f"URL 必须以 http:// 或 https:// 开头，当前值为: {self.url!r}")

        if not self.api_key:
            errors.append("APIKEY 不能为空")

        if not self.model:
            errors.append("MODEL 不能为空")

        if not MIN_TEMPERATURE <= self.temperature <= MAX_TEMPERATURE:
            errors.append(
                f"TEMPERATURE 必须在 {MIN_TEMPERATURE} ~ {MAX_TEMPERATURE} 之间，"
                f"当前值为: {self.temperature}"
            )

        if self.maxsteps <= 0:
            errors.append(f"MAXSTEPS 必须大于 0，当前值为: {self.maxsteps}")

        if errors:
            raise ValueError("配置校验失败:\n- " + "\n- ".join(errors))

    def __repr__(self) -> str:
        # 打印时对密钥做脱敏处理
        masked_key = f"{self.api_key[:4]}****" if self.api_key else ""
        return (
            f"Setting(url={self.url!r}, api_key={masked_key!r}, "
            f"temperature={self.temperature}, model={self.model!r}, maxsteps={self.maxsteps})"
        )
