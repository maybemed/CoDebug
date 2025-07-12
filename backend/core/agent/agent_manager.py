from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, BaseMessage
from typing import Dict, Any, Optional, Generator, Callable, List
from langchain import hub
import time

from typing import List

from backend.config.settings import settings
from backend.core.llm.llm_manager import LLMManager
from backend.core.tool_manager import ToolManager
from backend.core.prompt_manager import PromptManager
from backend.utils.logger import logger
from backend.core.agent.agent_memory import AgentMemory
from backend.core.agent.agent_config import AgentConfig
from backend.core.agent.agent_streaming_callback_handler import AgentStreamingCallbackHandler

class AgentManager:
    """
    负责 LangChain AgentExecutor 实例的创建和管理。
    支持动态更新系统提示词、流式输出和记忆功能。
    """
    _agent_instances: Dict[str, AgentExecutor] = {}
    _agent_memories: Dict[str, AgentMemory] = {}  # 新增：记忆存储 {session_id-agent_name: AgentMemory}

    @classmethod
    def get_agent(cls,
                  agent_name: str,
                  llm_model_name: str = "deepseek-chat",
                  system_prompt_name: str = "default",
                  force_refresh: bool = False,
                  streaming: bool = False) -> AgentExecutor:
        """
        获取或创建 AgentExecutor 实例（不带记忆的版本）

        Args:
            agent_name: Agent 名称
            llm_model_name: LLM 模型名称
            system_prompt_name: 系统提示词名称
            force_refresh: 是否强制刷新
            streaming: 是否启用流式输出

        Returns:
            AgentExecutor: Agent 执行器实例
        """
        # 修改缓存键策略：包含流式输出标志
        cache_key = f"{agent_name}-{llm_model_name}-{system_prompt_name}-{streaming}"

        if not force_refresh and cache_key in cls._agent_instances:
            logger.debug(f"返回缓存的 Agent 实例: {cache_key}")
            return cls._agent_instances[cache_key]

        if force_refresh:
            old_keys_to_remove = [key for key in cls._agent_instances.keys()
                                  if key.startswith(f"{agent_name}-{llm_model_name}-")]
            for old_key in old_keys_to_remove:
                del cls._agent_instances[old_key]
                logger.info(f"已清除旧的 Agent 缓存: {old_key}")

        logger.info(f"正在创建新的 Agent 实例: {cache_key}")

        # 1. 获取 Agent 配置
        agent_config_dict = settings.AVAILABLE_AGENTS.get(agent_name)
        if not agent_config_dict:
            logger.error(f"Agent '{agent_name}' 未在 settings.AVAILABLE_AGENTS 中配置。")
            raise ValueError(f"Agent '{agent_name}' 未配置。")

        try:
            agent_config = AgentConfig(**agent_config_dict)
        except Exception as e:
            logger.error(f"解析 Agent '{agent_name}' 配置失败: {e}")
            raise ValueError(f"Agent '{agent_name}' 配置无效。")

        # 2. 获取 LLM 实例（支持流式输出）
        try:
            llm_for_agent = LLMManager.get_llm(llm_model_name, temperature=0.0, streaming=streaming)
            if not isinstance(llm_for_agent, BaseChatModel):
                raise TypeError(f"LLM '{llm_model_name}' 不是有效的 ChatModel 实例。")
        except Exception as e:
            logger.error(f"获取 LLM '{llm_model_name}' 失败: {e}", exc_info=True)
            raise RuntimeError(f"无法初始化 Agent '{agent_name}': LLM '{llm_model_name}' 不可用。")

        # 3. 获取工具列表
        tools_for_agent = ToolManager.get_tools_by_names(agent_config.tools)
        if not tools_for_agent:
            logger.error(f"Agent '{agent_name}' 找不到可用工具。")
            raise RuntimeError(f"Agent '{agent_name}' 无法初始化: 没有可用工具。")
        logger.info(f"为 '{agent_name}' 加载工具: {[tool.name for tool in tools_for_agent]}")

        # 4. 构建集成了系统提示词的 Prompt
        try:
            prompt = cls._build_prompt_with_system_message(system_prompt_name)
            logger.info(f"成功构建包含系统提示词 '{system_prompt_name}' 的 Prompt。")
        except Exception as e:
            logger.error(f"构建 Prompt 失败: {e}", exc_info=True)
            raise RuntimeError("无法构建 Agent Prompt。")

        # 5. 创建 Agent 和 AgentExecutor
        try:
            agent = create_structured_chat_agent(llm_for_agent, tools_for_agent, prompt)
            executor = AgentExecutor(
                agent=agent,
                tools=tools_for_agent,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15,
                early_stopping_method="generate"
            )

            cls._agent_instances[cache_key] = executor
            logger.info(f"Agent '{agent_name}' 创建成功，流式输出: {streaming}")
            return executor

        except Exception as e:
            logger.error(f"创建 AgentExecutor 失败: {e}", exc_info=True)
            raise RuntimeError(f"Agent '{agent_name}' 初始化失败。")

    # =============== 新增：记忆相关方法 ===============

    @classmethod
    def _get_memory_key(cls, session_id: str, agent_name: str) -> str:
        """生成记忆键"""
        return f"{session_id}-{agent_name}"

    @classmethod
    def _get_or_create_memory(cls, session_id: str, agent_name: str, memory_window: int = 10) -> AgentMemory:
        """获取或创建 Agent 记忆"""
        memory_key = cls._get_memory_key(session_id, agent_name)

        if memory_key not in cls._agent_memories:
            cls._agent_memories[memory_key] = AgentMemory(
                session_id=session_id,
                agent_name=agent_name,
                memory_window=memory_window
            )

        return cls._agent_memories[memory_key]

    @classmethod
    def _build_prompt_with_memory(cls, system_prompt_name: str, agent_memory: AgentMemory):
        """构建包含记忆的 Prompt"""
        # 获取基础 prompt
        base_prompt = cls._build_prompt_with_system_message(system_prompt_name)

        # 获取记忆上下文
        memory_context = agent_memory.get_context_string()

        if memory_context and memory_context != "无历史记录":
            # 修改系统消息，添加记忆上下文
            messages = list(base_prompt.messages)

            if messages and hasattr(messages[0], 'type') and messages[0].type == "system":
                original_content = messages[0].content
                new_content = f"""{original_content}

=== 对话历史记忆 ===
{memory_context}

请根据以上对话历史来理解用户的当前请求，保持对话的连续性和上下文相关性。
=============================
"""
                messages[0].content = new_content
                base_prompt.messages = messages
                logger.debug("已将记忆上下文集成到 Prompt 中")

        return base_prompt

    # =============== 带记忆的 Agent 执行方法 ===============

    @classmethod
    def run_agent_with_memory(cls,
                              agent_name: str,
                              user_input: str,
                              session_id: str,
                              llm_model_name: str = "deepseek-chat",
                              system_prompt_name: str = "default",
                              memory_window: int = 10) -> str:
        """
        运行带记忆的 Agent（非流式）

        Args:
            agent_name: Agent 名称
            user_input: 用户输入
            session_id: 会话ID
            llm_model_name: LLM 模型名称
            system_prompt_name: 系统提示词名称
            memory_window: 记忆窗口大小

        Returns:
            str: Agent 执行结果
        """
        try:
            # 获取或创建记忆
            agent_memory = cls._get_or_create_memory(session_id, agent_name, memory_window)

            # 获取 Agent 实例
            agent = cls.get_agent(
                agent_name=agent_name,
                llm_model_name=llm_model_name,
                system_prompt_name=system_prompt_name,
                streaming=False
            )

            # 构建包含记忆的 prompt
            memory_prompt = cls._build_prompt_with_memory(system_prompt_name, agent_memory)

            # 重新创建 agent 以使用新的 prompt
            llm_for_agent = LLMManager.get_llm(llm_model_name, temperature=0.0, streaming=False)
            tools_for_agent = ToolManager.get_tools_by_names(
                settings.AVAILABLE_AGENTS[agent_name]["tools"]
            )

            temp_agent = create_structured_chat_agent(llm_for_agent, tools_for_agent, memory_prompt)
            temp_executor = AgentExecutor(
                agent=temp_agent,
                tools=tools_for_agent,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15,
                early_stopping_method="generate"
            )

            # 执行
            result = temp_executor.invoke({"input": user_input})
            output = result.get("output", "")

            # 保存到记忆
            agent_memory.add_interaction(user_input, output)

            logger.info(f"Agent '{agent_name}' 在会话 {session_id} 中执行完成（带记忆）")
            return output

        except Exception as e:
            logger.error(f"带记忆的 Agent 执行失败: {e}", exc_info=True)
            raise RuntimeError(f"Agent 执行失败: {e}")

    @classmethod
    def run_agent_with_memory_stream(cls,
                                     agent_name: str,
                                     user_input: str,
                                     session_id: str,
                                     llm_model_name: str = "deepseek-chat",
                                     system_prompt_name: str = "default",
                                     memory_window: int = 10) -> Generator[str, None, str]:
        """
        运行带记忆的 Agent（流式）

        Args:
            agent_name: Agent 名称
            user_input: 用户输入
            session_id: 会话ID
            llm_model_name: LLM 模型名称
            system_prompt_name: 系统提示词名称
            memory_window: 记忆窗口大小

        Yields:
            str: 每个内容块

        Returns:
            str: 完整的执行结果
        """
        try:
            # 获取或创建记忆
            agent_memory = cls._get_or_create_memory(session_id, agent_name, memory_window)

            # 构建包含记忆的 prompt
            memory_prompt = cls._build_prompt_with_memory(system_prompt_name, agent_memory)

            # 创建临时的 Agent 实例
            llm_for_agent = LLMManager.get_llm(llm_model_name, temperature=0.0, streaming=True)
            tools_for_agent = ToolManager.get_tools_by_names(
                settings.AVAILABLE_AGENTS[agent_name]["tools"]
            )

            temp_agent = create_structured_chat_agent(llm_for_agent, tools_for_agent, memory_prompt)
            temp_executor = AgentExecutor(
                agent=temp_agent,
                tools=tools_for_agent,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15,
                early_stopping_method="generate"
            )

            # 创建流式回调处理器
            streaming_handler = AgentStreamingCallbackHandler()
            full_result = ""

            try:
                # 尝试流式执行
                result = temp_executor.invoke(
                    {"input": user_input},
                    config={"callbacks": [streaming_handler]}
                )

                # 实时yield状态和token
                for token in streaming_handler.tokens:
                    yield token
                    full_result += token

                # 如果没有流式token，返回最终结果
                if not streaming_handler.tokens and result.get("output"):
                    final_output = result["output"]
                    yield final_output
                    full_result = final_output

            except Exception as e:
                logger.warning(f"流式执行失败，回退到分块输出: {e}")
                # 回退策略：执行后分块返回结果
                result = temp_executor.invoke({"input": user_input})
                final_output = result.get("output", "")

                # 将结果分块流式返回
                chunk_size = 15  # 每次返回15个字符
                for i in range(0, len(final_output), chunk_size):
                    chunk = final_output[i:i + chunk_size]
                    yield chunk
                    full_result += chunk
                    time.sleep(0.03)  # 添加小延迟模拟流式效果

            # 保存到记忆
            agent_memory.add_interaction(user_input, full_result)

            logger.info(f"Agent '{agent_name}' 在会话 {session_id} 中流式执行完成（带记忆）")
            return full_result

        except Exception as e:
            logger.error(f"带记忆的 Agent 流式执行失败: {e}", exc_info=True)
            raise RuntimeError(f"Agent 流式执行失败: {e}")

    # =============== 记忆管理方法 ===============

    @classmethod
    def get_agent_memory_history(cls, session_id: str, agent_name: str) -> List[BaseMessage]:
        """获取 Agent 的记忆历史"""
        memory_key = cls._get_memory_key(session_id, agent_name)
        if memory_key in cls._agent_memories:
            return cls._agent_memories[memory_key].get_history()
        return []

    @classmethod
    def clear_agent_memory(cls, session_id: str, agent_name: str = None):
        """清除 Agent 记忆"""
        if agent_name:
            memory_key = cls._get_memory_key(session_id, agent_name)
            if memory_key in cls._agent_memories:
                cls._agent_memories[memory_key].clear()
                logger.info(f"已清除会话 {session_id} 中 Agent {agent_name} 的记忆")
        else:
            # 清除该会话的所有 Agent 记忆
            keys_to_clear = [key for key in cls._agent_memories.keys() if key.startswith(f"{session_id}-")]
            for key in keys_to_clear:
                cls._agent_memories[key].clear()
            logger.info(f"已清除会话 {session_id} 的所有 Agent 记忆")

    @classmethod
    def delete_agent_memory(cls, session_id: str, agent_name: str = None):
        """删除 Agent 记忆"""
        if agent_name:
            memory_key = cls._get_memory_key(session_id, agent_name)
            if memory_key in cls._agent_memories:
                del cls._agent_memories[memory_key]
                logger.info(f"已删除会话 {session_id} 中 Agent {agent_name} 的记忆")
        else:
            # 删除该会话的所有 Agent 记忆
            keys_to_delete = [key for key in cls._agent_memories.keys() if key.startswith(f"{session_id}-")]
            for key in keys_to_delete:
                del cls._agent_memories[key]
            logger.info(f"已删除会话 {session_id} 的所有 Agent 记忆")

    @classmethod
    def get_memory_stats(cls) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        stats = {}
        for key, memory in cls._agent_memories.items():
            session_id, agent_name = key.split('-', 1)
            stats[key] = {
                "session_id": session_id,
                "agent_name": agent_name,
                "message_count": len(memory.get_history()),
                "memory_window": memory.memory.k,
                "context_preview": memory.get_context_string()[:100] + "..." if memory.get_context_string() else "无内容"
            }
        return stats

    @classmethod
    def list_active_sessions(cls) -> List[str]:
        """列出所有活跃的会话ID"""
        sessions = set()
        for key in cls._agent_memories.keys():
            session_id = key.split('-', 1)[0]
            sessions.add(session_id)
        return list(sessions)

    # =============== 原有的流式输出相关方法保持不变 ===============

    @classmethod
    def run_agent_stream(cls,
                         agent_name: str,
                         user_input: str,
                         llm_model_name: str = "deepseek-chat",
                         system_prompt_name: str = "default",
                         **kwargs) -> Generator[str, None, str]:
        """
        流式运行 Agent（无记忆版本）
        """
        try:
            agent = cls.get_agent(
                agent_name=agent_name,
                llm_model_name=llm_model_name,
                system_prompt_name=system_prompt_name,
                streaming=True
            )

            streaming_handler = AgentStreamingCallbackHandler()
            full_result = ""

            try:
                result = agent.invoke(
                    {"input": user_input},
                    config={"callbacks": [streaming_handler]}
                )

                for token in streaming_handler.tokens:
                    yield token
                    full_result += token

                if not streaming_handler.tokens and result.get("output"):
                    final_output = result["output"]
                    yield final_output
                    full_result = final_output

            except Exception as e:
                logger.warning(f"流式执行失败，回退到分块输出: {e}")
                result = agent.invoke({"input": user_input})
                final_output = result.get("output", "")

                chunk_size = 10
                for i in range(0, len(final_output), chunk_size):
                    chunk = final_output[i:i + chunk_size]
                    yield chunk
                    full_result += chunk
                    time.sleep(0.05)

            logger.info(f"Agent '{agent_name}' 流式执行完成（无记忆）")
            return full_result

        except Exception as e:
            logger.error(f"Agent 流式执行失败: {e}", exc_info=True)
            raise RuntimeError(f"Agent 流式执行失败: {e}")

    @classmethod
    def run_agent_stream_callback(cls,
                                  agent_name: str,
                                  user_input: str,
                                  callback: Callable[[str], None],
                                  llm_model_name: str = "deepseek-chat",
                                  system_prompt_name: str = "default") -> str:
        """使用回调函数的方式流式运行 Agent（无记忆版本）"""
        full_result = ""
        try:
            for chunk in cls.run_agent_stream(
                    agent_name=agent_name,
                    user_input=user_input,
                    llm_model_name=llm_model_name,
                    system_prompt_name=system_prompt_name
            ):
                callback(chunk)
                full_result += chunk
        except Exception as e:
            logger.error(f"回调式 Agent 流式执行失败: {e}")
            raise

        return full_result

    # =============== 原有的非流式方法保持不变 ===============

    @classmethod
    def run_agent(cls,
                  agent_name: str,
                  user_input: str,
                  llm_model_name: str = "deepseek-chat",
                  system_prompt_name: str = "default") -> str:
        """非流式运行 Agent（保持向后兼容）"""
        try:
            agent = cls.get_agent(
                agent_name=agent_name,
                llm_model_name=llm_model_name,
                system_prompt_name=system_prompt_name,
                streaming=False
            )

            result = agent.invoke({"input": user_input})
            logger.info(f"Agent '{agent_name}' 非流式执行完成")
            return result.get("output", "")

        except Exception as e:
            logger.error(f"Agent 非流式执行失败: {e}", exc_info=True)
            raise RuntimeError(f"Agent 执行失败: {e}")

    # =============== 其他方法保持不变 ===============

    @classmethod
    def _build_prompt_with_system_message(cls, system_prompt_name: str):
        """构建包含自定义系统提示词的 Prompt"""
        try:
            prompt_identifier = "hwchase17/structured-chat-agent"
            base_prompt = hub.pull(prompt_identifier)
            logger.debug(f"从 LangChain Hub 拉取基础 Prompt: {prompt_identifier}")
        except Exception as e:
            logger.error(f"从 LangChain Hub 拉取 Prompt 失败: {e}")
            raise

        try:
            PromptManager.initialize()

            if not PromptManager.set_current_system_prompt(system_prompt_name):
                logger.warning(f"无法设置系统提示词 '{system_prompt_name}'，使用默认提示词。")
                PromptManager.set_current_system_prompt("default")

            system_prompt_content = PromptManager.get_current_system_prompt()

            if not system_prompt_content:
                logger.warning("未能获取系统提示词，将使用原始 Prompt。")
                return base_prompt

        except Exception as e:
            logger.error(f"获取系统提示词失败: {e}")
            return base_prompt

        try:
            messages = list(base_prompt.messages)

            if messages and hasattr(messages[0], 'type') and messages[0].type == "system":
                original_content = messages[0].content
                new_content = f"{system_prompt_content}\n\n--- 以下是 Agent 执行指令 ---\n{original_content}"
                messages[0].content = new_content
            else:
                system_message = SystemMessage(content=system_prompt_content)
                messages.insert(0, system_message)

            base_prompt.messages = messages
            logger.debug("成功将自定义系统提示词集成到基础 Prompt 中。")

        except Exception as e:
            logger.error(f"集成系统提示词到 Prompt 失败: {e}")
            return base_prompt

        return base_prompt

    @classmethod
    def update_agent_system_prompt(cls,
                                   agent_name: str,
                                   llm_model_name: str,
                                   new_system_prompt_name: str) -> bool:
        """更新现有 Agent 的系统提示词"""
        try:
            cls.get_agent(
                agent_name=agent_name,
                llm_model_name=llm_model_name,
                system_prompt_name=new_system_prompt_name,
                force_refresh=True
            )

            logger.info(f"成功更新 Agent '{agent_name}' 的系统提示词为: {new_system_prompt_name}")
            return True

        except Exception as e:
            logger.error(f"更新 Agent 系统提示词失败: {e}")
            return False

    @classmethod
    def get_available_agents_info(cls) -> Dict[str, Any]:
        """获取所有可用 Agent 的配置信息"""
        return settings.AVAILABLE_AGENTS