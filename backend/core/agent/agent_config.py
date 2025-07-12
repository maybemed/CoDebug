from pydantic import BaseModel, Field
from typing import List


class AgentConfig(BaseModel):
    """Agent 配置模型"""
    name: str = Field(..., description="Agent 的显示名称")
    description: str = Field(..., description="关于 Agent 功能的详细描述")
    tools: List[str] = Field(..., description="该 Agent 可以使用的工具列表")