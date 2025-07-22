# @user: maybemed
# @last_update: 2025-07-12 02:23:07 UTC
# @version: agent_execution_api

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.core.agent.agent_manager import AgentManager
from backend.utils.logger import logger

router = APIRouter()


class AgentInfo(BaseModel):
    name: str
    description: str
    tools: List[str]


class AgentsResponse(BaseModel):
    agents: List[AgentInfo]


class AgentRunRequest(BaseModel):
    agent_name: str
    user_input: str
    session_id: str
    llm_model_name: Optional[str] = "deepseek-chat"
    system_prompt_name: Optional[str] = "default"
    memory_window: Optional[int] = 10


class IntermediateStep(BaseModel):
    thought: str
    action: Dict[str, Any]
    observation: str


class AgentRunResponse(BaseModel):
    result: str
    intermediate_steps: List[IntermediateStep]
    status: str
    error: Optional[str] = None


@router.get("/agents", response_model=AgentsResponse)
async def get_available_agents():
    """获取所有可用的Agent"""
    try:
        available_agents = AgentManager.get_available_agents_info()

        agents = []
        for agent_name, config in available_agents.items():
            agents.append(AgentInfo(
                name=agent_name,
                description=config.get("description", f"{agent_name} Agent"),
                tools=config.get("tools", [])
            ))

        return AgentsResponse(agents=agents)

    except Exception as e:
        logger.error(f"获取可用Agent失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available agents")


@router.post("/agent/run", response_model=AgentRunResponse)
async def run_agent_task(request: AgentRunRequest):
    """执行Agent任务（带记忆）"""
    try:
        # 验证Agent是否存在
        available_agents = AgentManager.get_available_agents_info()
        if request.agent_name not in available_agents:
            return AgentRunResponse(
                result="",
                intermediate_steps=[],
                status="error",
                error=f"Invalid agent name: {request.agent_name}"
            )

        # 使用带记忆的Agent执行任务
        result = AgentManager.run_agent_with_memory(
            agent_name=request.agent_name,
            user_input=request.user_input,
            session_id=request.session_id,
            llm_model_name=request.llm_model_name,
            system_prompt_name=request.system_prompt_name,
            memory_window=request.memory_window
        )

        # 注意：当前的AgentManager.run_agent_with_memory只返回最终结果
        # 如果需要intermediate_steps，需要修改AgentManager来捕获中间步骤
        # 这里暂时返回空的intermediate_steps

        return AgentRunResponse(
            result=result,
            intermediate_steps=[],  # TODO: 实现中间步骤捕获
            status="success"
        )

    except Exception as e:
        logger.error(f"Agent执行失败: {e}")
        return AgentRunResponse(
            result="",
            intermediate_steps=[],
            status="error",
            error=f"Agent failed to execute task: {str(e)}"
        )

# TODO: 如果需要实现intermediate_steps的捕获，可以考虑以下方案：
# 1. 修改AgentStreamingCallbackHandler来捕获更多信息
# 2. 在AgentManager中添加专门的方法来返回详细的执行步骤
# 3. 或者创建一个新的回调处理器来专门收集中间步骤信息