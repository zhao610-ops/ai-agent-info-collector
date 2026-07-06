from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import AppSetting, Base
from app.services.settings_service import (
    get_llm_config, get_serverchan_config, update_llm_config, update_serverchan_config,
)


def test_secret_values_are_preserved_and_never_returned():
    # 独立数据库验证空密码保留旧值，同时公开配置不包含任何密钥明文。
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        AppSetting(key="llm_api_key", value="secret-api-key", is_secret=True),
        AppSetting(key="server_chan_sendkey", value="secret-send-key", is_secret=True),
    ])
    session.commit()

    llm = update_llm_config(session, {
        "enabled": True, "provider": "deepseek", "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat", "api_key": None,
    })
    server = update_serverchan_config(session, {
        "enabled": True, "api_base": "https://sctapi.ftqq.com", "sendkey": None,
    })

    assert llm["api_key_configured"] is True
    assert server["sendkey_configured"] is True
    assert "api_key" not in get_llm_config(session)
    assert "sendkey" not in get_serverchan_config(session)
    assert get_llm_config(session, include_secret=True)["api_key"] == "secret-api-key"
    assert get_serverchan_config(session, include_secret=True)["sendkey"] == "secret-send-key"
