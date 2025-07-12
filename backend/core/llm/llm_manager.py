# @user: maybemed
# @last_update: 2025-07-12 01:15:30 UTC
# @version: llm_instance_with_memory_transfer

from typing import Dict, Any, Optional, List, Generator, Union, Callable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from datetime import datetime
import copy

import os
from dotenv import load_dotenv

load_dotenv()

from backend.config.settings import settings
from backend.core.prompt_manager import PromptManager
from backend.utils.logger import logger
from backend.core.llm.llm_conversation_history import LLMConversationHistory

from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_community.chat_models import QianfanChatEndpoint
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.chat_models import ChatTongyi
from langchain_community.chat_models import ChatSparkLLM


class LLMInstance:
    """
    LLM 实例类 - 作为主要的对话接口

    每个实例封装了模型、配置和记忆，支持记忆迁移
    """

    def __init__(self,
                 instance_id: str,
                 model_name: str,
                 temperature: float = 0.7,
                 max_messages: int = 50,
                 max_tokens: int = 4000):
        self.instance_id = instance_id
        self.model_name = model_name
        self.temperature = temperature
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.conversation_histories: Dict[str, LLMConversationHistory] = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        logger.info(f"创建 LLM 实例: {instance_id} (模型: {model_name})")

    def _get_or_create_conversation(self, session_id: str) -> LLMConversationHistory:
        """获取或创建对话历史"""
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = LLMConversationHistory(
                session_id=f"{self.instance_id}-{session_id}",
                max_messages=self.max_messages,
                max_tokens=self.max_tokens
            )
        return self.conversation_histories[session_id]

    def chat(self,
             user_message: str,
             session_id: str,
             system_prompt_name: str = "default") -> str:
        """
        进行对话（非流式）

        Args:
            user_message: 用户消息
            session_id: 会话ID
            system_prompt_name: 系统提示词名称

        Returns:
            str: AI 回复
        """
        conversation = self._get_or_create_conversation(session_id)

        try:
            # 更新系统消息
            system_content = LLMManager._get_system_prompt_content(system_prompt_name)
            if system_content:
                conversation.update_system_message(system_content)

            # 添加用户消息
            conversation.add_user_message(user_message)

            # 获取 LLM 并进行对话
            llm = LLMManager.get_llm(self.model_name, self.temperature, streaming=False)
            messages = conversation.get_messages()

            response = llm.invoke(messages)
            ai_reply = response.content

            # 添加AI回复
            conversation.add_ai_message(ai_reply)
            self.updated_at = datetime.now()

            logger.info(f"实例 {self.instance_id} 完成对话 (会话: {session_id})")
            return ai_reply

        except Exception as e:
            logger.error(f"实例对话失败: {e}", exc_info=True)
            raise RuntimeError(f"实例对话失败: {e}")

    def chat_stream(self,
                    user_message: str,
                    session_id: str,
                    system_prompt_name: str = "default") -> Generator[str, None, str]:
        """
        进行流式对话

        Args:
            user_message: 用户消息
            session_id: 会话ID
            system_prompt_name: 系统提示词名称

        Yields:
            str: 每个内容块

        Returns:
            str: 完整的回复内容
        """
        conversation = self._get_or_create_conversation(session_id)

        try:
            # 更新系统消息
            system_content = LLMManager._get_system_prompt_content(system_prompt_name)
            if system_content:
                conversation.update_system_message(system_content)

            # 添加用户消息
            conversation.add_user_message(user_message)

            # 获取 LLM 并进行流式对话
            llm = LLMManager.get_llm(self.model_name, self.temperature, streaming=True)
            messages = conversation.get_messages()

            # 流式调用
            full_content = ""
            for chunk in llm.stream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    content_piece = chunk.content
                    full_content += content_piece
                    yield content_piece

            # 添加完整回复
            conversation.add_ai_message(full_content)
            self.updated_at = datetime.now()

            logger.info(f"实例 {self.instance_id} 完成流式对话 (会话: {session_id})")
            return full_content

        except Exception as e:
            logger.error(f"实例流式对话失败: {e}", exc_info=True)
            raise RuntimeError(f"实例流式对话失败: {e}")

    def get_conversation_history(self, session_id: str) -> List[BaseMessage]:
        """获取指定会话的对话历史"""
        if session_id in self.conversation_histories:
            return self.conversation_histories[session_id].get_messages()
        return []

    def get_all_conversations(self) -> Dict[str, List[BaseMessage]]:
        """获取所有会话的对话历史"""
        return {
            session_id: conversation.get_messages()
            for session_id, conversation in self.conversation_histories.items()
        }

    def clear_conversation(self, session_id: str, keep_system_message: bool = True):
        """清除指定会话的历史"""
        if session_id in self.conversation_histories:
            self.conversation_histories[session_id].clear_history(keep_system_message)
            self.updated_at = datetime.now()
            logger.info(f"实例 {self.instance_id} 清除会话 {session_id} 历史")

    def delete_conversation(self, session_id: str):
        """删除指定会话"""
        if session_id in self.conversation_histories:
            del self.conversation_histories[session_id]
            self.updated_at = datetime.now()
            logger.info(f"实例 {self.instance_id} 删除会话 {session_id}")

    def copy_memory_from(self, source_instance: 'LLMInstance', session_id: str = None):
        """
        从另一个实例复制记忆

        Args:
            source_instance: 源实例
            session_id: 指定会话ID，如果为None则复制所有会话
        """
        if session_id:
            # 复制指定会话
            if session_id in source_instance.conversation_histories:
                source_conversation = source_instance.conversation_histories[session_id]

                # 深拷贝对话历史
                new_conversation = LLMConversationHistory(
                    session_id=f"{self.instance_id}-{session_id}",
                    max_messages=self.max_messages,
                    max_tokens=self.max_tokens
                )

                # 复制所有消息
                new_conversation.messages = copy.deepcopy(source_conversation.messages)
                new_conversation.created_at = source_conversation.created_at
                new_conversation.updated_at = datetime.now()

                self.conversation_histories[session_id] = new_conversation
                self.updated_at = datetime.now()

                logger.info(f"实例 {self.instance_id} 从 {source_instance.instance_id} 复制会话 {session_id} 记忆")
        else:
            # 复制所有会话
            for src_session_id, src_conversation in source_instance.conversation_histories.items():
                new_conversation = LLMConversationHistory(
                    session_id=f"{self.instance_id}-{src_session_id}",
                    max_messages=self.max_messages,
                    max_tokens=self.max_tokens
                )

                # 复制所有消息
                new_conversation.messages = copy.deepcopy(src_conversation.messages)
                new_conversation.created_at = src_conversation.created_at
                new_conversation.updated_at = datetime.now()

                self.conversation_histories[src_session_id] = new_conversation

            self.updated_at = datetime.now()
            logger.info(f"实例 {self.instance_id} 从 {source_instance.instance_id} 复制所有会话记忆")

    def transfer_memory_to(self, target_instance: 'LLMInstance', session_id: str = None):
        """
        将记忆转移到另一个实例

        Args:
            target_instance: 目标实例
            session_id: 指定会话ID，如果为None则转移所有会话
        """
        target_instance.copy_memory_from(self, session_id)
        logger.info(f"实例 {self.instance_id} 向 {target_instance.instance_id} 转移记忆")

    def get_stats(self) -> Dict[str, Any]:
        """获取实例统计信息"""
        total_messages = sum(len(conv.get_messages()) for conv in self.conversation_histories.values())

        return {
            "instance_id": self.instance_id,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "active_conversations": len(self.conversation_histories),
            "total_messages": total_messages,
            "conversation_ids": list(self.conversation_histories.keys()),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class LLMManager:
    """
    LLM 管理器 - 管理 LLMInstance 实例
    """
    _available_models_info = {
        "gpt-4o-mini": {"provider": "GPT"},
        "deepseek-chat": {"provider": "DeepSeek"},
        "glm-4-air": {"provider": "Zhipu"},
        "qwen-max": {"provider": "Qwen"},
        "Spark X1": {"provider": "Spark"},
    }

    # 基础 LLM 实例缓存
    _llm_instances: Dict[str, BaseChatModel] = {}

    # LLM 实例管理
    _llm_user_instances: Dict[str, LLMInstance] = {}  # instance_id -> LLMInstance

    @classmethod
    def get_llm(cls, model_name: str, temperature: float = 0.7, streaming: bool = False) -> BaseChatModel:
        """获取基础 LLM 实例（内部使用）"""
        if model_name not in settings.AVAILABLE_LLMS:
            raise ValueError(f"LLM model '{model_name}' is not configured.")

        cache_key = f"{model_name}-{temperature}-{streaming}"
        if cache_key in cls._llm_instances:
            return cls._llm_instances[cache_key]

        # 创建 LLM 实例的逻辑保持不变
        model_config = settings.AVAILABLE_LLMS[model_name]
        provider = model_config["provider"]

        if provider == "GPT":
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=os.environ["OPENAI_API_KEY"],
                base_url=os.environ["OPENAI_API_BASE"],
                temperature=temperature,
                streaming=streaming,
            )
        elif provider == "Deepseek":
            llm = ChatDeepSeek(
                model=model_name,
                api_key=os.environ["DEEPSEEK_API_KEY"],
                base_url=os.environ["DEEPSEEK_API_BASE"],
                temperature=temperature,
                streaming=streaming,
            )
        elif provider == "Qianfan":
            llm = QianfanChatEndpoint(
                model=model_name,
                api_key=os.environ["QIANFAN_API_KEY"],
                secret_key=os.environ["QIANFAN_SECRET_KEY"],
                temperature=temperature,
                streaming=streaming,
            )
        elif provider == "Zhipu":
            llm = ChatZhipuAI(
                model=model_name,
                api_key=os.environ["ZHIPU_API_KEY"],
                base_url=os.environ["ZHIPU_API_BASE"],
                temperature=temperature,
                streaming=streaming,
            )
        elif provider == "Qwen":
            llm = ChatTongyi(
                model=model_name,
                api_key=os.environ["QWEN_API_KEY"],
                temperature=temperature,
                streaming=streaming,
            )
        elif provider == "Spark":
            llm = ChatSparkLLM(
                model=model_name,
                api_key=os.environ["SPARK_API_KEY"],
                api_secret=os.environ["SPARK_API_SECRET"],
                spark_app_id=os.environ["SPARK_APP_ID"],
                api_url=os.environ["SPARK_API_BASE"],
                temperature=temperature,
                streaming=streaming,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        cls._llm_instances[cache_key] = llm
        logger.info(f"成功创建基础 LLM 实例: {model_name} (temperature: {temperature}, streaming: {streaming})")
        return llm

    # =============== LLMInstance 管理方法 ===============

    @classmethod
    def create_instance(cls,
                        instance_id: str,
                        model_name: str,
                        temperature: float = 0.7,
                        max_messages: int = 50,
                        max_tokens: int = 4000) -> LLMInstance:
        """
        创建 LLM 实例

        Args:
            instance_id: 实例唯一标识符
            model_name: 模型名称
            temperature: 温度参数
            max_messages: 最大消息数
            max_tokens: 最大token数

        Returns:
            LLMInstance: 创建的实例
        """
        if instance_id in cls._llm_user_instances:
            raise ValueError(f"LLM 实例 '{instance_id}' 已存在")

        if model_name not in settings.AVAILABLE_LLMS:
            raise ValueError(f"LLM 模型 '{model_name}' 不支持")

        instance = LLMInstance(
            instance_id=instance_id,
            model_name=model_name,
            temperature=temperature,
            max_messages=max_messages,
            max_tokens=max_tokens
        )

        cls._llm_user_instances[instance_id] = instance
        logger.info(f"成功创建 LLM 实例: {instance_id}")
        return instance

    @classmethod
    def get_instance(cls, instance_id: str) -> Optional[LLMInstance]:
        """获取 LLM 实例"""
        return cls._llm_user_instances.get(instance_id)

    @classmethod
    def delete_instance(cls, instance_id: str) -> bool:
        """删除 LLM 实例"""
        if instance_id in cls._llm_user_instances:
            del cls._llm_user_instances[instance_id]
            logger.info(f"已删除 LLM 实例: {instance_id}")
            return True
        return False

    @classmethod
    def list_instances(cls) -> Dict[str, Dict[str, Any]]:
        """列出所有 LLM 实例"""
        return {
            instance_id: instance.get_stats()
            for instance_id, instance in cls._llm_user_instances.items()
        }

    # =============== 便捷的记忆操作方法 ===============

    @classmethod
    def copy_memory(cls,
                    source_instance_id: str,
                    target_instance_id: str,
                    session_id: str = None) -> bool:
        """
        复制记忆从一个实例到另一个实例

        Args:
            source_instance_id: 源实例ID
            target_instance_id: 目标实例ID
            session_id: 指定会话ID，如果为None则复制所有会话

        Returns:
            bool: 操作是否成功
        """
        source_instance = cls.get_instance(source_instance_id)
        target_instance = cls.get_instance(target_instance_id)

        if not source_instance:
            logger.error(f"源实例 {source_instance_id} 不存在")
            return False

        if not target_instance:
            logger.error(f"目标实例 {target_instance_id} 不存在")
            return False

        try:
            target_instance.copy_memory_from(source_instance, session_id)
            logger.info(f"成功复制记忆: {source_instance_id} -> {target_instance_id}")
            return True
        except Exception as e:
            logger.error(f"复制记忆失败: {e}")
            return False

    @classmethod
    def transfer_memory(cls,
                        source_instance_id: str,
                        target_instance_id: str,
                        session_id: str = None,
                        delete_source: bool = False) -> bool:
        """
        转移记忆从一个实例到另一个实例

        Args:
            source_instance_id: 源实例ID
            target_instance_id: 目标实例ID
            session_id: 指定会话ID，如果为None则转移所有会话
            delete_source: 是否删除源实例的记忆

        Returns:
            bool: 操作是否成功
        """
        if not cls.copy_memory(source_instance_id, target_instance_id, session_id):
            return False

        if delete_source:
            source_instance = cls.get_instance(source_instance_id)
            if source_instance:
                if session_id:
                    source_instance.delete_conversation(session_id)
                else:
                    # 清除所有会话
                    for conv_id in list(source_instance.conversation_histories.keys()):
                        source_instance.delete_conversation(conv_id)

                logger.info(f"已删除源实例 {source_instance_id} 的记忆")

        return True

    @classmethod
    def switch_model_with_memory(cls,
                                 source_instance_id: str,
                                 new_model_name: str,
                                 new_instance_id: str = None,
                                 temperature: float = 0.7,
                                 session_id: str = None) -> LLMInstance:
        """
        切换模型并保留记忆

        Args:
            source_instance_id: 源实例ID
            new_model_name: 新模型名称
            new_instance_id: 新实例ID，如果为None则自动生成
            temperature: 新实例的温度
            session_id: 指定会话ID，如果为None则转移所有会话

        Returns:
            LLMInstance: 新创建的实例
        """
        source_instance = cls.get_instance(source_instance_id)
        if not source_instance:
            raise ValueError(f"源实例 {source_instance_id} 不存在")

        # 自动生成新实例ID
        if new_instance_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_instance_id = f"{new_model_name.replace('-', '_')}_{timestamp}"

        # 创建新实例
        new_instance = cls.create_instance(
            instance_id=new_instance_id,
            model_name=new_model_name,
            temperature=temperature,
            max_messages=source_instance.max_messages,
            max_tokens=source_instance.max_tokens
        )

        # 转移记忆
        cls.transfer_memory(source_instance_id, new_instance_id, session_id, delete_source=False)

        logger.info(f"模型切换完成: {source_instance.model_name} -> {new_model_name} (实例: {new_instance_id})")
        return new_instance

    # =============== 辅助方法 ===============

    @classmethod
    def _get_system_prompt_content(cls, system_prompt_name: str) -> Optional[str]:
        """获取系统提示词内容"""
        try:
            PromptManager.initialize()
            if PromptManager.set_current_system_prompt(system_prompt_name):
                return PromptManager.get_current_system_prompt()
        except Exception as e:
            logger.error(f"获取系统提示词失败: {e}")
        return None

    @classmethod
    def get_available_models(cls) -> Dict[str, Any]:
        """获取可用的模型信息"""
        return settings.AVAILABLE_LLMS

    # =============== 向后兼容的方法保持不变 ===============
    # 这里可以保留原有的 chat_with_memory 等方法以保持向后兼容