from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import AppSetting


PROVIDER_DEFAULTS = {
    "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
    "qwen": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "kimi": {"base_url": "https://api.moonshot.ai/v1", "model": "kimi-latest"},
    "siliconflow": {"base_url": "https://api.siliconflow.cn/v1", "model": "deepseek-ai/DeepSeek-V3"},
    "custom": {"base_url": "", "model": ""},
}


def _read(session: Session, key: str, default: str = "") -> str:
    item = session.query(AppSetting).filter(AppSetting.key == key).first()
    return item.value if item else default


def _write(session: Session, key: str, value: str, secret: bool = False) -> None:
    item = session.query(AppSetting).filter(AppSetting.key == key).first()
    if item:
        item.value = value
        item.is_secret = secret
    else:
        session.add(AppSetting(key=key, value=value, is_secret=secret))


def get_llm_config(session: Session, include_secret: bool = False) -> dict:
    env = get_settings()
    provider = _read(session, "llm_provider", env.llm_provider)
    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["custom"])
    api_key = _read(session, "llm_api_key", env.llm_api_key)
    result = {
        "enabled": _read(session, "llm_enabled", str(env.llm_enabled)).lower() == "true",
        "provider": provider,
        "base_url": _read(session, "llm_base_url", env.llm_base_url or defaults["base_url"]),
        "model": _read(session, "llm_model", env.llm_model or defaults["model"]),
        "api_key_configured": bool(api_key),
    }
    if include_secret:
        result["api_key"] = api_key
    return result


def update_llm_config(session: Session, data: dict) -> dict:
    provider = data["provider"]
    if provider not in PROVIDER_DEFAULTS:
        raise ValueError("不支持的模型提供商")
    _write(session, "llm_enabled", str(bool(data["enabled"])).lower())
    _write(session, "llm_provider", provider)
    _write(session, "llm_base_url", data.get("base_url", "").strip())
    _write(session, "llm_model", data.get("model", "").strip())
    if data.get("api_key"):
        _write(session, "llm_api_key", data["api_key"].strip(), secret=True)
    session.commit()
    return get_llm_config(session)


def get_serverchan_config(session: Session, include_secret: bool = False) -> dict:
    env = get_settings()
    sendkey = _read(session, "server_chan_sendkey", env.server_chan_sendkey)
    result = {
        "enabled": _read(session, "server_chan_enabled", str(env.server_chan_enabled)).lower() == "true",
        "api_base": _read(session, "server_chan_api_base", env.server_chan_api_base),
        "sendkey_configured": bool(sendkey),
    }
    if include_secret:
        result["sendkey"] = sendkey
    return result


def update_serverchan_config(session: Session, data: dict) -> dict:
    """保存 Server 酱配置；SendKey 为空时保留已有密钥。"""
    _write(session, "server_chan_enabled", str(bool(data["enabled"])).lower())
    _write(session, "server_chan_api_base", data.get("api_base", "").strip())
    if data.get("sendkey"):
        _write(session, "server_chan_sendkey", data["sendkey"].strip(), secret=True)
    session.commit()
    return get_serverchan_config(session)
