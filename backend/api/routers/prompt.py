# @user: maybemed
# @last_update: 2025-07-12 02:23:07 UTC
# @version: prompt_management_api

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from backend.core.prompt_manager import PromptManager
from backend.utils.logger import logger
from backend.core.llm.llm_manager import LLMManager
from backend.config.settings import settings

router = APIRouter()


class PromptUpdateRequest(BaseModel):
    prompt: str


class PromptResponse(BaseModel):
    system_prompt: str


class PromptUpdateResponse(BaseModel):
    msg: str
    system_prompt: str


class TravelPromptRequest(BaseModel):
    destination: str
    date: str
    budget: str
    preference: str

class TravelPromptResponse(BaseModel):
    user_prompt: str

class SendUserMessageRequest(BaseModel):
    session_id: str
    user_prompt: str

class SendUserMessageResponse(BaseModel):
    msg: str
    session_id: str
    user_prompt: str


@router.get("/", response_model=PromptResponse)
async def get_system_prompt():
    """获取当前系统提示词"""
    try:
        PromptManager.initialize()
        current_prompt = PromptManager.get_current_system_prompt()

        if current_prompt is None:
            raise HTTPException(status_code=500, detail="Failed to get current system prompt")

        return PromptResponse(system_prompt=current_prompt)

    except Exception as e:
        logger.error(f"获取系统提示词失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system prompt")


@router.post("/", response_model=PromptUpdateResponse)
async def update_system_prompt(request: PromptUpdateRequest):
    """更新系统提示词"""
    try:
        PromptManager.initialize()

        # 创建或更新名为 "current" 的系统提示词
        prompt_name = "current"

        # 先尝试更新，如果不存在则创建
        success = PromptManager.update_system_prompt(
            name=prompt_name,
            content=request.prompt,
            description="当前使用的系统提示词"
        )

        if not success:
            # 如果更新失败（可能是不存在），则创建新的
            success = PromptManager.create_system_prompt(
                name=prompt_name,
                content=request.prompt,
                description="当前使用的系统提示词"
            )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update system prompt")

        # 设置为当前使用的提示词
        if not PromptManager.set_current_system_prompt(prompt_name):
            raise HTTPException(status_code=500, detail="Failed to set current system prompt")

        return PromptUpdateResponse(
            msg="系统级prompt已更新",
            system_prompt=request.prompt
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新系统提示词失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to update system prompt")

# ----------- 新增接口1：自动构建旅游用户message -----------
@router.post("/build_travel_prompt", response_model=TravelPromptResponse)
async def build_travel_prompt(request: TravelPromptRequest):
    """根据旅游信息自动构建用户提示词"""
    try:
        user_prompt = (
            f"我想创建一个{request.date}去{request.destination}旅游的方案，"
            f"预算是{request.budget}，我的旅行偏好是{request.preference}，"
            "请你给我相关的出行建议，不要涉及到景点的路径规划，只给我关于天气、防晒、穿搭等的建议即可。"
        )
        return TravelPromptResponse(user_prompt=user_prompt)
    except Exception as e:
        logger.error(f"构建旅游用户提示词失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to build travel prompt")

# ----------- 新增接口2：初始化会话后自动发送第一条用户信息 -----------
@router.post("/send_first_user_message", response_model=SendUserMessageResponse)
async def send_first_user_message(request: SendUserMessageRequest):
    """向指定会话自动发送第一条用户信息"""
    try:
        # 获取当前活跃的实例
        current_instance = LLMManager.get_instance(request.session_id)
        if not current_instance:
            # 如果实例不存在，自动初始化，使用默认模型
            default_model = "deepseek-chat"
            if default_model not in settings.AVAILABLE_LLMS:
                default_model = list(settings.AVAILABLE_LLMS.keys())[0]
            LLMManager.create_instance(instance_id=request.session_id, model_name=default_model)
            current_instance = LLMManager.get_instance(request.session_id)
        if not current_instance:
            raise HTTPException(status_code=500, detail="Failed to initialize session instance")
        # 添加用户消息到会话
        current_instance.conversation.add_user_message(request.user_prompt)
        return SendUserMessageResponse(
            msg="用户消息已发送到会话",
            session_id=request.session_id,
            user_prompt=request.user_prompt
        )
    except Exception as e:
        logger.error(f"发送第一条用户信息失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to send first user message")