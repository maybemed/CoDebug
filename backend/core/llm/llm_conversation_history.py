from typing import Dict, Any, Optional, List, Generator, Union, Callable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()

from backend.config.settings import settings
from backend.core.prompt_manager import PromptManager
from backend.utils.logger import logger

class LLMConversationHistory:
    """LLM 对话历史管理类"""

    def __init__(self, session_id: str, max_messages: int = 50, max_tokens: int = 4000):
        """
        初始化 LLM 对话历史

        Args:
            session_id: 会话唯一标识
            max_messages: 最大消息数量
            max_tokens: 最大token数量（粗略估算）
        """
        self.session_id = session_id
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.messages: List[BaseMessage] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        logger.info(f"为会话 {session_id} 创建 LLM 对话历史")

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.messages.append(HumanMessage(content=content))
        self.updated_at = datetime.now()
        self._cleanup_if_needed()
        logger.debug(f"已添加用户消息到 LLM 会话 {self.session_id}")

    def add_ai_message(self, content: str):
        """添加AI消息"""
        self.messages.append(AIMessage(content=content))
        self.updated_at = datetime.now()
        self._cleanup_if_needed()
        logger.debug(f"已添加AI消息到 LLM 会话 {self.session_id}")

    def update_system_message(self, content: str):
        """更新或添加系统消息"""
        # 检查是否已存在系统消息，如果存在则替换
        for i, msg in enumerate(self.messages):
            if isinstance(msg, SystemMessage):
                self.messages[i] = SystemMessage(content=content)
                logger.debug(f"已更新 LLM 系统消息在会话 {self.session_id}")
                return

        # 如果不存在，在开头插入
        self.messages.insert(0, SystemMessage(content=content))
        logger.debug(f"已添加 LLM 系统消息到会话 {self.session_id}")

    def get_messages(self) -> List[BaseMessage]:
        """获取所有消息"""
        return self.messages.copy()

    def get_messages_without_system(self) -> List[BaseMessage]:
        """获取除系统消息外的所有消息"""
        return [msg for msg in self.messages if not isinstance(msg, SystemMessage)]

    def get_recent_messages(self, count: int) -> List[BaseMessage]:
        """获取最近的N条消息"""
        return self.messages[-count:] if count < len(self.messages) else self.messages.copy()

    def clear_history(self, keep_system_message: bool = True):
        """清除历史记录"""
        if keep_system_message:
            system_messages = [msg for msg in self.messages if isinstance(msg, SystemMessage)]
            self.messages = system_messages
        else:
            self.messages = []

        self.updated_at = datetime.now()
        logger.info(f"已清除 LLM 会话 {self.session_id} 的历史记录")

    def _cleanup_if_needed(self):
        """根据设定的限制清理历史记录"""
        # 1. 限制消息数量
        if len(self.messages) > self.max_messages:
            # 保留系统消息和最近的消息
            system_messages = [msg for msg in self.messages if isinstance(msg, SystemMessage)]
            other_messages = [msg for msg in self.messages if not isinstance(msg, SystemMessage)]

            # 保留最近的消息
            recent_messages = other_messages[-(self.max_messages - len(system_messages)):]
            self.messages = system_messages + recent_messages

            logger.info(f"LLM 会话 {self.session_id} 历史记录已清理，保留 {len(self.messages)} 条消息")

        # 2. 限制token数量（粗略估算：1个中文字符≈1.5个token）
        total_chars = sum(len(msg.content) for msg in self.messages)
        estimated_tokens = int(total_chars * 1.5)

        if estimated_tokens > self.max_tokens:
            # 从最老的非系统消息开始删除
            while estimated_tokens > self.max_tokens and len(self.messages) > 1:
                # 找到第一个非系统消息并删除
                for i, msg in enumerate(self.messages):
                    if not isinstance(msg, SystemMessage):
                        removed_msg = self.messages.pop(i)
                        estimated_tokens -= int(len(removed_msg.content) * 1.5)
                        break
                else:
                    # 如果只剩系统消息，跳出循环
                    break

            logger.info(f"LLM 会话 {self.session_id} 因token限制清理历史，估算token数: {estimated_tokens}")

    def get_stats(self) -> Dict[str, Any]:
        """获取对话统计信息"""
        message_types = {}
        total_chars = 0

        for msg in self.messages:
            msg_type = type(msg).__name__
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
            total_chars += len(msg.content)

        return {
            "session_id": self.session_id,
            "total_messages": len(self.messages),
            "message_types": message_types,
            "total_characters": total_chars,
            "estimated_tokens": int(total_chars * 1.5),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }