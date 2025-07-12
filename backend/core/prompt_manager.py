import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from backend.config.settings import settings
from backend.utils.logger import logger


class SystemPromptConfig(BaseModel):
    """系统提示词配置模型"""
    name: str = Field(..., description="提示词名称")
    content: str = Field(..., description="提示词内容")
    description: str = Field(default="", description="提示词描述")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")
    is_active: bool = Field(default=True, description="是否启用")


class PromptManager:
    """
    提示词管理器

    负责：
    1. 管理系统级提示词
    2. 提供提示词的增删改查功能
    3. 支持提示词的持久化存储
    4. 提供提示词模板和变量替换功能
    """

    _default_prompts_file = "prompts/system_prompts.json"
    _custom_prompts: Dict[str, SystemPromptConfig] = {}
    _current_system_prompt: Optional[str] = None
    _initialized = False

    @classmethod
    def initialize(cls):
        """初始化提示词管理器"""
        if cls._initialized:
            return

        cls._load_default_prompts()
        cls._load_custom_prompts()
        cls._set_default_system_prompt()
        cls._initialized = True
        logger.info("提示词管理器初始化完成。")

    @classmethod
    def _load_default_prompts(cls):
        """加载默认提示词"""
        default_prompts = {
            "default": SystemPromptConfig(
                name="default",
                content="""你是一个有用、准确、诚实的AI助手。你的目标是为用户提供最佳的帮助。

请遵循以下原则：
1. 如果不确定答案，请诚实地说明
2. 优先提供准确和有用的信息
3. 保持友好和专业的语调
4. 如果需要使用工具来获取信息，请合理使用

当前时间：{current_time}
用户：{user_name}""",
                description="默认系统提示词",
                is_active=True
            ),
            "creative": SystemPromptConfig(
                name="creative",
                content="""你是一个富有创造力和想象力的AI助手。你善于进行创意思考、头脑风暴和创新性问题解决。

你的特点：
1. 思维活跃，善于联想
2. 能够从多角度思考问题
3. 鼓励用户探索新的可能性
4. 提供原创性的建议和方案

让我们一起探索无限的可能性！

当前时间：{current_time}
用户：{user_name}""",
                description="创意助手提示词",
                is_active=True
            ),
            "analytical": SystemPromptConfig(
                name="analytical",
                content="""你是一个逻辑严谨、分析能力强的AI助手。你擅长数据分析、逻辑推理和系统性思考。

你的工作方式：
1. 系统性地分析问题
2. 基于事实和数据进行推理
3. 提供结构化的分析结果
4. 明确指出假设和限制条件

让我们用理性和逻辑来解决问题。

当前时间：{current_time}
用户：{user_name}""",
                description="分析型助手提示词",
                is_active=True
            )
        }

        for prompt_id, prompt_config in default_prompts.items():
            cls._custom_prompts[prompt_id] = prompt_config

    @classmethod
    def _load_custom_prompts(cls):
        """从文件加载自定义提示词"""
        try:
            prompts_file_path = os.path.join(os.getcwd(), cls._default_prompts_file)
            if os.path.exists(prompts_file_path):
                with open(prompts_file_path, 'r', encoding='utf-8') as f:
                    prompts_data = json.load(f)

                for prompt_id, prompt_dict in prompts_data.items():
                    cls._custom_prompts[prompt_id] = SystemPromptConfig(**prompt_dict)

                logger.info(f"从文件加载了 {len(prompts_data)} 个自定义提示词。")
            else:
                logger.info("自定义提示词文件不存在，将创建默认文件。")
                cls._save_prompts_to_file()
        except Exception as e:
            logger.error(f"加载自定义提示词失败: {e}")

    @classmethod
    def _save_prompts_to_file(cls):
        """保存提示词到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(cls._default_prompts_file), exist_ok=True)

            # 将提示词转换为可序列化的字典
            prompts_data = {}
            for prompt_id, prompt_config in cls._custom_prompts.items():
                prompts_data[prompt_id] = prompt_config.dict()

            with open(cls._default_prompts_file, 'w', encoding='utf-8') as f:
                json.dump(prompts_data, f, ensure_ascii=False, indent=2)

            logger.info(f"提示词已保存到文件: {cls._default_prompts_file}")
        except Exception as e:
            logger.error(f"保存提示词到文件失败: {e}")

    @classmethod
    def _set_default_system_prompt(cls):
        """设置默认系统提示词"""
        if "default" in cls._custom_prompts:
            cls._current_system_prompt = cls._format_prompt("default")
            logger.info("已设置默认系统提示词。")

    @classmethod
    def create_system_prompt(cls, name: str, content: str, description: str = "") -> bool:
        """
        创建新的系统提示词

        Args:
            name: 提示词名称（唯一标识符）
            content: 提示词内容
            description: 提示词描述

        Returns:
            bool: 创建是否成功
        """
        try:
            if not cls._initialized:
                cls.initialize()

            if name in cls._custom_prompts:
                logger.warning(f"提示词 '{name}' 已存在，创建失败。")
                return False

            prompt_config = SystemPromptConfig(
                name=name,
                content=content,
                description=description
            )

            cls._custom_prompts[name] = prompt_config
            cls._save_prompts_to_file()

            logger.info(f"成功创建系统提示词: {name}")
            return True

        except Exception as e:
            logger.error(f"创建系统提示词失败: {e}")
            return False

    @classmethod
    def update_system_prompt(cls, name: str, content: str = None, description: str = None) -> bool:
        """
        更新现有的系统提示词

        Args:
            name: 提示词名称
            content: 新的提示词内容（可选）
            description: 新的提示词描述（可选）

        Returns:
            bool: 更新是否成功
        """
        try:
            if not cls._initialized:
                cls.initialize()

            if name not in cls._custom_prompts:
                logger.warning(f"提示词 '{name}' 不存在，更新失败。")
                return False

            prompt_config = cls._custom_prompts[name]

            if content is not None:
                prompt_config.content = content
            if description is not None:
                prompt_config.description = description

            prompt_config.updated_at = datetime.now().isoformat()

            cls._save_prompts_to_file()

            # 如果更新的是当前使用的提示词，重新格式化
            if cls._current_system_prompt and name in cls._current_system_prompt:
                cls.set_current_system_prompt(name)

            logger.info(f"成功更新系统提示词: {name}")
            return True

        except Exception as e:
            logger.error(f"更新系统提示词失败: {e}")
            return False

    @classmethod
    def delete_system_prompt(cls, name: str) -> bool:
        """
        删除系统提示词

        Args:
            name: 要删除的提示词名称

        Returns:
            bool: 删除是否成功
        """
        try:
            if not cls._initialized:
                cls.initialize()

            if name not in cls._custom_prompts:
                logger.warning(f"提示词 '{name}' 不存在，删除失败。")
                return False

            if name == "default":
                logger.warning("无法删除默认提示词。")
                return False

            del cls._custom_prompts[name]
            cls._save_prompts_to_file()

            logger.info(f"成功删除系统提示词: {name}")
            return True

        except Exception as e:
            logger.error(f"删除系统提示词失败: {e}")
            return False

    @classmethod
    def set_current_system_prompt(cls, name: str) -> bool:
        """
        设置当前使用的系统提示词

        Args:
            name: 提示词名称

        Returns:
            bool: 设置是否成功
        """
        try:
            if not cls._initialized:
                cls.initialize()

            if name not in cls._custom_prompts:
                logger.warning(f"提示词 '{name}' 不存在。")
                return False

            if not cls._custom_prompts[name].is_active:
                logger.warning(f"提示词 '{name}' 未启用。")
                return False

            cls._current_system_prompt = cls._format_prompt(name)
            logger.info(f"成功设置当前系统提示词: {name}")
            return True

        except Exception as e:
            logger.error(f"设置当前系统提示词失败: {e}")
            return False

    @classmethod
    def get_current_system_prompt(cls) -> Optional[str]:
        """
        获取当前的系统提示词

        Returns:
            str: 当前格式化后的系统提示词内容
        """
        if not cls._initialized:
            cls.initialize()
        return cls._current_system_prompt

    @classmethod
    def _format_prompt(cls, name: str, **kwargs) -> str:
        """
        格式化提示词，替换变量

        Args:
            name: 提示词名称
            **kwargs: 额外的变量

        Returns:
            str: 格式化后的提示词
        """
        if name not in cls._custom_prompts:
            return ""

        # 默认变量
        variables = {
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'user_name': 'maybemed',  # 可以从 session 或配置中获取
        }

        # 添加额外变量
        variables.update(kwargs)

        try:
            return cls._custom_prompts[name].content.format(**variables)
        except Exception as e:
            logger.warning(f"格式化提示词失败，返回原始内容: {e}")
            return cls._custom_prompts[name].content

    @classmethod
    def list_system_prompts(cls) -> Dict[str, SystemPromptConfig]:
        """
        获取所有系统提示词

        Returns:
            Dict[str, SystemPromptConfig]: 所有提示词的字典
        """
        if not cls._initialized:
            cls.initialize()
        return cls._custom_prompts.copy()

    @classmethod
    def get_system_prompt(cls, name: str) -> Optional[SystemPromptConfig]:
        """
        获取指定的系统提示词配置

        Args:
            name: 提示词名称

        Returns:
            SystemPromptConfig: 提示词配置对象
        """
        if not cls._initialized:
            cls.initialize()
        return cls._custom_prompts.get(name)