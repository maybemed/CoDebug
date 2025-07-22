# @user: maybemed
# @last_update: 2025-07-12 02:10:44 UTC
# @version: simplified_single_conversation_per_instance

from typing import Dict, Any, Optional, List, Generator, Union, Callable, AsyncGenerator
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
from backend.core.RAG.rag_engine import RAGEngine

# 原有的导入保持不变...
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_community.chat_models import QianfanChatEndpoint
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.chat_models import ChatTongyi
from langchain_community.chat_models import ChatSparkLLM


class LLMInstance:
    """
    LLM 实例类 - 一个实例绑定一个对话历史
    每个实例只维护一个对话历史，更清晰简洁
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
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # 每个实例只有一个对话历史
        self.conversation = LLMConversationHistory(
            session_id=instance_id,
            max_messages=max_messages,
            max_tokens=max_tokens
        )

        logger.info(f"创建 LLM 实例: {instance_id} (模型: {model_name})")

    def chat(self, user_message: str, system_prompt_name: str = "default") -> str:
        """
        进行对话（非流式）

        Args:
            user_message: 用户消息
            system_prompt_name: 系统提示词名称

        Returns:
            str: AI 回复
        """
        try:
            # RAG 检索
            rag_engine = RAGEngine()
            rag_contexts = rag_engine.query(user_message, top_k=3)
            rag_context_str = "\n\n".join(rag_contexts)
            # 更新系统消息
            system_content = LLMManager._get_system_prompt_content(system_prompt_name)
            if system_content:
                if rag_contexts:
                    system_content = f"【以下是知识库检索内容，可作为回答参考】\n{rag_context_str}\n\n{system_content}"
                self.conversation.update_system_message(system_content)
            # 添加用户消息
            self.conversation.add_user_message(user_message)

            # 获取 LLM 并进行对话
            llm = LLMManager.get_llm(self.model_name, self.temperature, streaming=False)
            messages = self.conversation.get_messages()

            response = llm.invoke(messages)
            ai_reply = response.content if isinstance(response.content, str) else str(response.content)

            # 添加AI回复
            self.conversation.add_ai_message(ai_reply)
            self.updated_at = datetime.now()

            logger.info(f"实例 {self.instance_id} 完成对话")
            return ai_reply

        except Exception as e:
            logger.error(f"实例对话失败: {e}", exc_info=True)
            raise RuntimeError(f"实例对话失败: {e}")

    # 位于您的 LLM 实例类中
    async def chat_stream(self, user_message: str, system_prompt_name: str = "default") -> AsyncGenerator[str, None]:
        """
        进行流式对话 (异步版本)

        Args:
            user_message: 用户消息
            system_prompt_name: 系统提示词名称

        Yields:
            str: 每个内容块
        """
        try:
            # RAG 检索
            rag_engine = RAGEngine()
            rag_contexts = rag_engine.query(user_message, top_k=3)
            rag_context_str = "\n\n".join(rag_contexts)
            # 更新系统消息
            system_content = LLMManager._get_system_prompt_content(system_prompt_name)
            if system_content:
                if rag_contexts:
                    system_content = f"【以下是知识库检索内容，可作为回答参考】\n{rag_context_str}\n\n{system_content}"
                self.conversation.update_system_message(system_content)
            # 添加用户消息
            self.conversation.add_user_message(user_message)

            # 获取 LLM 并进行流式对话
            llm = LLMManager.get_llm(self.model_name, self.temperature, streaming=True)
            messages = self.conversation.get_messages()

            # 创建一个列表来收集所有数据块
            full_content_parts = []

            # 流式调用
            async for chunk in llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    content_piece = chunk.content
                    if isinstance(content_piece, str):
                        full_content_parts.append(content_piece)
                        yield content_piece

            # 在循环结束后，将收集到的数据块拼接成完整消息
            full_content = "".join(full_content_parts)

            # 添加完整回复到对话历史
            self.conversation.add_ai_message(full_content)
            self.updated_at = datetime.now()

            logger.info(f"实例 {self.instance_id} 完成流式对话，共计 {len(full_content)} 字符")

        except Exception as e:
            logger.error(f"实例流式对话失败: {e}", exc_info=True)
            raise RuntimeError(f"实例流式对话失败: {e}")

    def get_conversation_history(self) -> List[BaseMessage]:
        """获取对话历史"""
        return self.conversation.get_messages()

    def clear_conversation(self, keep_system_message: bool = True):
        """清除对话历史"""
        self.conversation.clear_history(keep_system_message)
        self.updated_at = datetime.now()
        logger.info(f"实例 {self.instance_id} 清除对话历史")

    def copy_memory_from(self, source_instance: 'LLMInstance'):
        """
        从另一个实例复制记忆

        Args:
            source_instance: 源实例
        """
        # 深拷贝对话历史
        source_conversation = source_instance.conversation

        # 重新初始化对话历史
        self.conversation = LLMConversationHistory(
            session_id=self.instance_id,
            max_messages=self.max_messages,
            max_tokens=self.max_tokens
        )

        # 复制所有消息
        self.conversation.messages = copy.deepcopy(source_conversation.messages)
        self.conversation.created_at = source_conversation.created_at
        self.conversation.updated_at = datetime.now()
        self.updated_at = datetime.now()

        logger.info(f"实例 {self.instance_id} 从 {source_instance.instance_id} 复制记忆")

    def transfer_memory_to(self, target_instance: 'LLMInstance'):
        """
        将记忆转移到另一个实例

        Args:
            target_instance: 目标实例
        """
        target_instance.copy_memory_from(self)
        logger.info(f"实例 {self.instance_id} 向 {target_instance.instance_id} 转移记忆")

    def get_stats(self) -> Dict[str, Any]:
        """获取实例统计信息"""
        conversation_stats = self.conversation.get_stats()

        return {
            "instance_id": self.instance_id,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_messages": self.max_messages,
            "max_tokens": self.max_tokens,
            "total_messages": conversation_stats["total_messages"],
            "message_types": conversation_stats["message_types"],
            "total_characters": conversation_stats["total_characters"],
            "estimated_tokens": conversation_stats["estimated_tokens"],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "conversation_created_at": conversation_stats["created_at"],
            "conversation_updated_at": conversation_stats["updated_at"]
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

    # LLM 用户实例管理
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

    # =============== 记忆操作方法 ===============

    @classmethod
    def copy_memory(cls,
                    source_instance_id: str,
                    target_instance_id: str) -> bool:
        """
        复制记忆从一个实例到另一个实例

        Args:
            source_instance_id: 源实例ID
            target_instance_id: 目标实例ID

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
            target_instance.copy_memory_from(source_instance)
            logger.info(f"成功复制记忆: {source_instance_id} -> {target_instance_id}")
            return True
        except Exception as e:
            logger.error(f"复制记忆失败: {e}")
            return False

    @classmethod
    def transfer_memory(cls,
                        source_instance_id: str,
                        target_instance_id: str,
                        clear_source: bool = False) -> bool:
        """
        转移记忆从一个实例到另一个实例

        Args:
            source_instance_id: 源实例ID
            target_instance_id: 目标实例ID
            clear_source: 是否清除源实例的记忆

        Returns:
            bool: 操作是否成功
        """
        if not cls.copy_memory(source_instance_id, target_instance_id):
            return False

        if clear_source:
            source_instance = cls.get_instance(source_instance_id)
            if source_instance:
                source_instance.clear_conversation()
                logger.info(f"已清除源实例 {source_instance_id} 的记忆")

        return True

    @classmethod
    def switch_model_with_memory(cls,
                                 source_instance_id: str,
                                 new_model_name: str,
                                 new_instance_id: str = None,
                                 temperature: float = 0.7) -> LLMInstance:
        """
        切换模型并保留记忆

        Args:
            source_instance_id: 源实例ID
            new_model_name: 新模型名称
            new_instance_id: 新实例ID，如果为None则自动生成
            temperature: 新实例的温度

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
        cls.transfer_memory(source_instance_id, new_instance_id, clear_source=False)

        logger.info(f"模型切换完成: {source_instance.model_name} -> {new_model_name} (实例: {new_instance_id})")
        return new_instance

    @classmethod
    def clone_instance(cls,
                       source_instance_id: str,
                       new_instance_id: str,
                       new_model_name: str = None,
                       new_temperature: float = None) -> LLMInstance:
        """
        克隆实例（保留记忆，可选择性修改模型和参数）

        Args:
            source_instance_id: 源实例ID
            new_instance_id: 新实例ID
            new_model_name: 新模型名称，如果为None则使用源实例的模型
            new_temperature: 新温度，如果为None则使用源实例的温度

        Returns:
            LLMInstance: 克隆的实例
        """
        source_instance = cls.get_instance(source_instance_id)
        if not source_instance:
            raise ValueError(f"源实例 {source_instance_id} 不存在")

        # 使用源实例的配置（除非明确指定新值）
        model_name = new_model_name or source_instance.model_name
        temperature = new_temperature if new_temperature is not None else source_instance.temperature

        # 创建新实例
        new_instance = cls.create_instance(
            instance_id=new_instance_id,
            model_name=model_name,
            temperature=temperature,
            max_messages=source_instance.max_messages,
            max_tokens=source_instance.max_tokens
        )

        # 复制记忆
        cls.copy_memory(source_instance_id, new_instance_id)

        logger.info(f"克隆实例完成: {source_instance_id} -> {new_instance_id}")
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

    # =============== 便捷方法 ===============

    @classmethod
    def quick_chat(cls,
                   instance_id: str,
                   user_message: str,
                   model_name: str = "deepseek-chat",
                   system_prompt_name: str = "default",
                   create_if_not_exists: bool = True) -> str:
        """
        快速对话方法

        Args:
            instance_id: 实例ID
            user_message: 用户消息
            model_name: 模型名称（仅在创建新实例时使用）
            system_prompt_name: 系统提示词名称
            create_if_not_exists: 如果实例不存在是否自动创建

        Returns:
            str: AI 回复
        """
        instance = cls.get_instance(instance_id)

        if not instance:
            if create_if_not_exists:
                instance = cls.create_instance(instance_id, model_name)
            else:
                raise ValueError(f"实例 {instance_id} 不存在")

        return instance.chat(user_message, system_prompt_name)

    @classmethod
    async def quick_chat_stream(cls,
                        instance_id: str,
                        user_message: str,
                        model_name: str = "deepseek-chat",
                        system_prompt_name: str = "default",
                        create_if_not_exists: bool = True) -> AsyncGenerator[str, None]:
        """
        快速流式对话 (异步版本)

        Args:
            instance_id: 实例ID
            user_message: 用户消息
            model_name: 模型名称
            system_prompt_name: 系统提示词名称
            create_if_not_exists: 如果实例不存在是否创建

        Yields:
            str: 每个内容块
        """
        try:
            # 获取或创建实例
            instance = cls.get_instance(instance_id)
            if not instance and create_if_not_exists:
                instance = cls.create_instance(
                    instance_id=instance_id,
                    model_name=model_name
                )
            elif not instance:
                raise ValueError(f"实例不存在: {instance_id}")

            # 使用实例进行流式对话
            async for chunk in instance.chat_stream(user_message, system_prompt_name):
                yield chunk

        except Exception as e:
            logger.error(f"快速流式对话失败: {e}", exc_info=True)
            raise RuntimeError(f"快速流式对话失败: {e}")



import asyncio

async def main():
    instance_id = "debug-stream"
    model_name = "deepseek-chat"
    user_message = "你好，请给我一个50字的科幻故事。"

    # # 确保实例存在
    # instance = LLMManager.get_instance(instance_id)
    # if not instance:
    #     instance = LLMManager.create_instance(instance_id=instance_id, model_name=model_name)
    #
    # print(">>> 开始流式输出：")
    # async for chunk in instance.chat_stream(user_message):
    #     print(chunk, end="", flush=True)  # 模拟流式输出
    print(">>> quick_chat_stream 流式输出测试：")
    async for chunk in LLMManager.quick_chat_stream(
            instance_id=instance_id,
            user_message=user_message,
            model_name=model_name,
            system_prompt_name="default",
            create_if_not_exists=True
    ):
        print(chunk, end="", flush=True)  # 模拟前端实时显示


if __name__ == "__main__":
    asyncio.run(main())
