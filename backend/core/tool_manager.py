# @user: maybemed
# @last_update: 2025-07-11 06:27:39 UTC
# @version: chinese_logs

import logging
from typing import List, Dict, Optional
from langchain.tools import Tool

# 导入各种工具和 API 包装器
from langchain_community.utilities.serpapi import SerpAPIWrapper
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.utilities.openweathermap import OpenWeatherMapAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.tools.openweathermap import OpenWeatherMapQueryRun

# 项目内部导入
from backend.config.settings import settings
from backend.utils.logger import logger


class ToolManager:
    """
    统一管理 LangChain Agent 可用工具的管理器。

    这个类负责：
    1. 初始化所有可用的工具实例
    2. 提供根据名称获取工具的接口
    3. 处理工具初始化失败的情况
    4. 缓存工具实例以提高性能
    """

    # 类级别的状态变量
    _initialized = False  # 标记是否已经初始化过工具
    _initialized_tools: Dict[str, Tool] = {}  # 存储所有成功初始化的工具实例

    @classmethod
    def initialize_tools(cls):
        """
        初始化所有可用的工具。

        这个方法只会执行一次（通过 _initialized 标志控制），
        即使多次调用也不会重复初始化。
        """
        # 防重复初始化检查
        if cls._initialized:
            logger.debug("工具已经初始化完成，跳过重复初始化。")
            return

        logger.info("开始初始化 Agent 工具...")

        # 1. SerpAPI 搜索工具
        cls._initialize_serpapi_search()

        # 2. Tavily 搜索工具
        cls._initialize_tavily_search()

        # 3. DuckDuckGo 搜索工具
        cls._initialize_duckduckgo_search()

        # 4. Python REPL 工具
        cls._initialize_python_repl()

        # 5. Wikipedia 工具
        cls._initialize_wikipedia_tool()

        # 6. OpenWeatherMap 天气工具
        cls._initialize_weather_tool()

        # 7. 标记初始化完成
        cls._initialized = True
        logger.info(f"所有 Agent 工具初始化完成。成功初始化 {len(cls._initialized_tools)} 个工具。")

    @classmethod
    def _initialize_serpapi_search(cls):
        """
        初始化 SerpAPI 搜索工具。

        SerpAPI 是一个付费的搜索引擎 API，提供高质量的搜索结果。
        需要 SERPAPI_API_KEY 环境变量。
        """
        try:
            if settings.SERPAPI_API_KEY:
                # 创建 SerpAPI 包装器实例
                serp_api = SerpAPIWrapper(serpapi_api_key=settings.SERPAPI_API_KEY)

                # 定义工具名称（必须与 settings.py 中配置的名称一致）
                tool_name = "SerpApiSearch"

                # 创建 LangChain Tool 实例
                cls._initialized_tools[tool_name] = Tool(
                    name=tool_name,
                    func=serp_api.run,  # 工具的执行函数
                    description="基于 Google 的强大搜索引擎。适用于回答时事问题、最新新闻和一般网络信息查询。"
                )
                logger.info(f"  ✓ {tool_name} 工具初始化成功。")
            else:
                logger.warning("  ⚠ 未设置 SERPAPI_API_KEY 环境变量。SerpApiSearch 工具将不可用。")
        except Exception as e:
            logger.error(f"  ✗ SerpApiSearch 工具初始化失败: {e}")

    @classmethod
    def _initialize_tavily_search(cls):
        """
        初始化 Tavily 搜索工具。

        Tavily 是另一个搜索 API 服务，专为 AI 应用优化。
        需要 TAVILY_API_KEY 环境变量。
        """
        try:
            if settings.TAVILY_API_KEY:
                tavily_api = TavilySearchAPIWrapper(tavily_api_key=settings.TAVILY_API_KEY)
                tool_name = "TavilySearch"

                cls._initialized_tools[tool_name] = Tool(
                    name=tool_name,
                    func=tavily_api.run,
                    description="为 AI 优化的搜索引擎。擅长获取全面且结构化的主题信息。"
                )
                logger.info(f"  ✓ {tool_name} 工具初始化成功。")
            else:
                logger.warning("  ⚠ 未设置 TAVILY_API_KEY 环境变量。TavilySearch 工具将不可用。")
        except Exception as e:
            logger.error(f"  ✗ TavilySearch 工具初始化失败: {e}")

    @classmethod
    def _initialize_duckduckgo_search(cls):
        """
        初始化 DuckDuckGo 搜索工具。

        DuckDuckGo 是免费的搜索工具，不需要 API 密钥。
        这是一个很好的备用搜索选项。
        """
        try:
            tool_name = "DuckDuckGoSearch"

            # 直接创建 DuckDuckGoSearchRun 实例
            duckduckgo_tool = DuckDuckGoSearchRun()

            # 确保工具名称匹配配置
            duckduckgo_tool.name = tool_name

            cls._initialized_tools[tool_name] = duckduckgo_tool
            logger.info(f"  ✓ {tool_name} 工具初始化成功。")
        except Exception as e:
            logger.error(f"  ✗ DuckDuckGoSearch 工具初始化失败: {e}")

    @classmethod
    @classmethod
    def _initialize_python_repl(cls):
        """
        初始化 Python REPL 工具。

        这个工具允许 Agent 执行 Python 代码，对于数学计算、
        数据分析、图表生成等任务非常有用。

        特别优化：
        - 自动为未包含 print 的表达式添加 print 输出
        - 提供友好的错误处理，避免 Agent 因空 Observation 而循环
        """
        try:
            tool_name = "PythonREPLTool"

            # 创建自定义的 Python REPL 工具实例
            class SafePythonREPLTool(PythonREPLTool):
                """
                安全的 Python REPL 工具，确保总是有 Observation 输出。
                """

                def run(self, code: str, **kwargs) -> str:
                    """
                    执行 Python 代码并确保有输出结果。

                    Args:
                        code: 要执行的 Python 代码
                        **kwargs: 其他参数（如 verbose, color 等），传递给父类

                    Returns:
                        执行结果或错误信息
                    """
                    try:
                        # 清理代码，移除前后空白
                        code = code.strip()
                        if not code:
                            return "ERROR: 代码为空，请提供有效的 Python 代码。"

                        # 处理单行或多行代码
                        processed_code = self._process_code_for_output(code)

                        # 调用父类的 run 方法执行代码，传递所有额外参数
                        result = super().run(processed_code, **kwargs)

                        # 确保返回非空结果
                        if not result or result.strip() == '':
                            return "代码执行完成，但无输出结果。"

                        return result

                    except Exception as e:
                        # 返回友好的错误信息，避免空 Observation
                        error_msg = f"Python 代码执行错误: {str(e)}"
                        logger.warning(f"PythonREPLTool 执行失败: {error_msg}")
                        return error_msg

                def _process_code_for_output(self, code: str) -> str:
                    """
                    处理代码以确保有输出。

                    Args:
                        code: 原始代码

                    Returns:
                        处理后的代码
                    """
                    # 处理单行分号分隔的代码
                    if ';' in code and '\n' not in code:
                        # 分号分隔的单行代码
                        parts = code.split(';')
                        last_part = parts[-1].strip()

                        if last_part and not self._is_statement(last_part):
                            # 最后一部分是表达式，添加 print
                            if not last_part.startswith('print'):
                                parts[-1] = f'print({last_part})'
                            return '; '.join(parts)
                        else:
                            # 如果最后一部分是语句或为空，添加一个 print 来确保有输出
                            return code + '; print("执行完成")'

                    # 处理多行代码
                    lines = code.split('\n')
                    last_line = lines[-1].strip()

                    if last_line and not self._is_statement(last_line):
                        # 最后一行是表达式，添加 print
                        if not last_line.startswith('print'):
                            lines[-1] = f'print({last_line})'
                    else:
                        # 如果最后一行是语句或为空，添加一个 print 来确保有输出
                        lines.append('print("执行完成")')

                    return '\n'.join(lines)

                def _is_statement(self, line: str) -> bool:
                    """
                    判断一行代码是否是语句（而非表达式）。

                    语句包括：赋值、import、def、class、if、for、while、try、with 等
                    表达式包括：变量名、函数调用、数学运算等

                    Args:
                        line: 代码行

                    Returns:
                        True 如果是语句，False 如果是表达式
                    """
                    line = line.strip()
                    if not line:
                        return True

                    # 语句关键字列表
                    statement_keywords = [
                        'import', 'from', 'def', 'class', 'if', 'elif', 'else',
                        'for', 'while', 'try', 'except', 'finally', 'with',
                        'break', 'continue', 'pass', 'return', 'yield', 'raise',
                        'assert', 'del', 'global', 'nonlocal', 'print('
                    ]

                    # 检查是否以语句关键字开头
                    for keyword in statement_keywords:
                        if line.startswith(keyword):
                            return True

                    # 检查是否是赋值语句（简单检查）
                    if '=' in line and not line.startswith('=') and not any(
                            op in line for op in ['==', '!=', '<=', '>=', '+=', '-=', '*=', '/=', '%=', '**=', '//=']):
                        return True

                    return False

            # 创建工具实例
            python_repl = SafePythonREPLTool()
            python_repl.name = tool_name

            # 更新工具描述，提供使用提示
            python_repl.description = (
                "执行 Python 代码的工具。适用于数学计算、数据分析、图表生成等任务。"
                "代码中的表达式会自动输出结果，无需手动添加 print()。"
                "如果需要多个输出，请使用 print() 函数。"
            )

            cls._initialized_tools[tool_name] = python_repl
            logger.info(f"  ✓ {tool_name} 工具初始化成功（已启用自动输出优化）。")

        except Exception as e:
            logger.error(f"  ✗ PythonREPLTool 工具初始化失败: {e}")

    @classmethod
    def _initialize_wikipedia_tool(cls):
        """
        初始化 Wikipedia 工具。

        这个工具允许 Agent 搜索和获取 Wikipedia 上的信息。
        对于获取准确的百科知识非常有用。

        注意：需要安装 'wikipedia' Python 包。
        """
        try:
            tool_name = "WikipediaTool"

            # 先创建 Wikipedia API 包装器
            api_wrapper = WikipediaAPIWrapper(
                top_k_results=3,  # 返回前3个搜索结果
                doc_content_chars_max=1000  # 每个结果最大字符数
            )

            # 创建 Wikipedia 查询工具
            wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)
            wiki_tool.name = tool_name

            cls._initialized_tools[tool_name] = wiki_tool
            logger.info(f"  ✓ {tool_name} 工具初始化成功。")
        except Exception as e:
            logger.error(f"  ✗ WikipediaTool 工具初始化失败: {e}")
            if "No module named 'wikipedia'" in str(e):
                logger.error("  💡 提示: 请安装 wikipedia 包: pip install wikipedia")

    @classmethod
    def _initialize_weather_tool(cls):
        """
        初始化 OpenWeatherMap 天气工具。

        这个工具允许 Agent 查询任何地点的实时天气信息。
        需要 OPENWEATHERMAP_API_KEY 环境变量。
        """
        try:
            if settings.OPENWEATHERMAP_API_KEY:
                tool_name = "OpenWeatherMapTool"

                # 创建 OpenWeatherMap API 包装器实例
                api_wrapper = OpenWeatherMapAPIWrapper()

                # 创建天气查询工具实例
                weather_tool_run = OpenWeatherMapQueryRun(api_wrapper=api_wrapper)

                # 包装成 LangChain Tool
                cls._initialized_tools[tool_name] = Tool(
                    name=tool_name,
                    func=weather_tool_run.run,
                    description="获取全球任何地点的当前天气信息。请提供城市名称或坐标。"
                )
                logger.info(f"  ✓ {tool_name} 工具初始化成功。")
            else:
                logger.warning("  ⚠ 未设置 OPENWEATHERMAP_API_KEY 环境变量。OpenWeatherMapTool 工具将不可用。")
        except Exception as e:
            logger.error(f"  ✗ OpenWeatherMapTool 工具初始化失败: {e}")

    @classmethod
    def get_tools_by_names(cls, tool_names: List[str]) -> List[Tool]:
        """
        根据工具名称列表获取对应的工具实例。

        Args:
            tool_names: 需要获取的工具名称列表

        Returns:
            成功找到的工具实例列表

        注意：如果某个工具未找到或初始化失败，会记录警告但不会中断程序。
        """
        # 确保工具已初始化
        if not cls._initialized:
            logger.warning("ToolManager 尚未显式初始化。正在自动调用 initialize_tools()。")
            cls.initialize_tools()

        tools = []
        missing_tools = []

        for name in tool_names:
            tool = cls._initialized_tools.get(name)
            if tool:
                tools.append(tool)
                logger.debug(f"  ✓ 找到工具: {name}")
            else:
                missing_tools.append(name)
                logger.warning(f"  ✗ 请求的工具 '{name}' 未找到或初始化失败。跳过该工具。")

        # 提供有用的调试信息
        if missing_tools:
            available_tools = list(cls._initialized_tools.keys())
            logger.info(f"可用工具列表: {available_tools}")
            logger.info(f"缺失工具列表: {missing_tools}")

        return tools

    @classmethod
    def get_all_tools(cls) -> List[Tool]:
        """
        获取所有成功初始化的工具实例。

        Returns:
            所有可用工具的列表
        """
        if not cls._initialized:
            cls.initialize_tools()
        return list(cls._initialized_tools.values())

    @classmethod
    def get_available_tool_names(cls) -> List[str]:
        """
        获取所有可用工具的名称列表。

        Returns:
            可用工具名称的列表
        """
        if not cls._initialized:
            cls.initialize_tools()
        return list(cls._initialized_tools.keys())

    @classmethod
    def is_tool_available(cls, tool_name: str) -> bool:
        """
        检查指定的工具是否可用。

        Args:
            tool_name: 要检查的工具名称

        Returns:
            True 如果工具可用，False 否则
        """
        if not cls._initialized:
            cls.initialize_tools()
        return tool_name in cls._initialized_tools

    @classmethod
    def get_tool_info(cls) -> Dict[str, str]:
        """
        获取所有工具的基本信息。

        Returns:
            工具名称到描述的映射字典
        """
        if not cls._initialized:
            cls.initialize_tools()

        tool_info = {}
        for name, tool in cls._initialized_tools.items():
            tool_info[name] = getattr(tool, 'description', '无描述信息')

        return tool_info