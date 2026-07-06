from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import PushLog, get_db
from app.services.settings_service import (
    get_llm_config, get_serverchan_config, update_llm_config, update_serverchan_config,
)
from app.tools.llm_tool import LLMTool
from app.tools.serverchan_tool import ServerChanTool


router = APIRouter(prefix="/api/settings", tags=["settings"])


class LLMConfigInput(BaseModel):
    enabled: bool = False
    provider: str
    base_url: str = ""
    model: str = ""
    api_key: str | None = Field(default=None, max_length=1000)


class ServerChanConfigInput(BaseModel):
    enabled: bool = False
    api_base: str = "https://sctapi.ftqq.com"
    sendkey: str | None = Field(default=None, max_length=1000)


@router.get("/llm")
def llm_config(session: Session = Depends(get_db)):
    return get_llm_config(session)


@router.post("/llm")
def save_llm_config(data: LLMConfigInput, session: Session = Depends(get_db)):
    try:
        return update_llm_config(session, data.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/test-llm")
def test_llm(session: Session = Depends(get_db)):
    config = get_llm_config(session, include_secret=True)
    if not config["api_key_configured"]:
        return {"success": False, "error": "未配置 API Key", "output": ""}
    try:
        output = LLMTool(config["base_url"], config["model"], config["api_key"]).test()
        return {"success": True, "error": "", "output": output}
    except Exception as exc:
        return {"success": False, "error": str(exc), "output": ""}


@router.get("/serverchan")
def serverchan_config(session: Session = Depends(get_db)):
    config = get_serverchan_config(session)
    logs = session.query(PushLog).order_by(PushLog.created_at.desc()).limit(10).all()
    config["recent_pushes"] = [
        {"id": row.id, "week": row.week, "status": row.status,
         "error_message": row.error_message, "created_at": row.created_at}
        for row in logs
    ]
    return config


@router.post("/serverchan")
def save_serverchan_config(data: ServerChanConfigInput, session: Session = Depends(get_db)):
    return update_serverchan_config(session, data.model_dump())


@router.post("/test-push")
def test_push(session: Session = Depends(get_db)):
    config = get_serverchan_config(session, include_secret=True)
    if not config["enabled"]: raise HTTPException(400, "Server 酱未启用")
    if not config["sendkey_configured"]: raise HTTPException(400, "未配置 Server 酱 SendKey")
    title = "AI Agent 微信情报官测试推送"
    content = "如果你收到这条消息，说明 Server 酱配置成功。"
    try:
        response = ServerChanTool(config["api_base"], config["sendkey"]).push(title, content)
        session.add(PushLog(week="test", title=title, content=content, status="success", response=str(response)))
        session.commit()
        return {"success": True, "response": response}
    except Exception as exc:
        session.add(PushLog(week="test", title=title, content=content, status="failed", error_message=str(exc)))
        session.commit()
        raise HTTPException(502, str(exc)) from exc
