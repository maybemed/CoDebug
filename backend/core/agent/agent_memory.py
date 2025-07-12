from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import SystemMessage, BaseMessage
from typing import List
from backend.utils.logger import logger


class AgentMemory:
    """Agent 记忆管理类"""

    def __init__(self, session_id: str, agent_name: str, memory_window: int = 10):
        self.session_id = session_id
        self.agent_name = agent_name
        self.memory = ConversationBufferWindowMemory(
            k=memory_window,
            memory_key="chat_history",
            input_key="input",
            output_key="output",
            return_messages=True
        )
        logger.info(f"为会话 {session_id} 的 Agent {agent_name} 创建记忆，窗口大小: {memory_window}")

    def add_interaction(self, user_input: str, agent_output: str):
        """添加一次交互到记忆中"""
        self.memory.save_context(
            {"input": user_input},
            {"output": agent_output}
        )
        logger.debug(f"已保存交互到 Agent {self.agent_name} 记忆中")

    def get_history(self) -> List[BaseMessage]:
        """获取记忆中的历史消息"""
        return self.memory.chat_memory.messages

    def clear(self):
        """清除记忆"""
        self.memory.clear()
        logger.info(f"已清除 Agent {self.agent_name} 在会话 {self.session_id} 中的记忆")

    def get_context_string(self) -> str:
        """获取记忆的文本表示"""
        messages = self.get_history()
        context_parts = []

        for msg in messages:
            if hasattr(msg, 'type'):
                if msg.type == "human":
                    context_parts.append(f"用户: {msg.content}")
                elif msg.type == "ai":
                    context_parts.append(f"助手: {msg.content}")

        return "\n".join(context_parts) if context_parts else "无历史记录"