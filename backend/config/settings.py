import os
from dotenv import load_dotenv

load_dotenv()
class Settings:
    """
    项目配置类，读取环境变量和配置文件。
    """
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_TEMPERATURE = float(os.getenv("DEEPSEEK_TEMPERATURE", 0.7))

    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
    TAVILY_API_KEY=""
    OPENWEATHERMAP_API_KEY=""
    # 定义可用的 LLM 模型及其描述
    AVAILABLE_LLMS = {
        "gpt-4o-mini": {
            "description": "OpenAI GPT-4o-mini，擅长复杂推理和多模态。",
            "provider": "GPT"
        },
        "deepseek-chat": {
            "description": "DeepSeek Chat 模型，擅长多轮对话和复杂推理。",
            "provider": "Deepseek"
        },
        # "ERNIE-3.5-8K-0701": {
        #     "description": "百度千帆 ERNIE-3.5-8K-0701，中文能力强，适合企业应用。",
        #     "provider": "Baidu"
        # },
        "glm-4-air": {
            "description": "智谱 AI GLM-4-Air，国产大模型，适合各类中文场景。",
            "provider": "Zhipu"
        },
        "qwen-max": {
            "description": "阿里 Qwen-Max，通用大模型，支持多语言和多任务。",
            "provider": "Qwen"
        },
        "Spark X1": {
            "description": "讯飞星火 Spark X1，国产多模态大模型，适合中文问答和知识推理。",
            "provider": "Spark"
        }
    }

    # 定义可用的 Agent 及其描述，这些名称会对应 agent_manager 中的逻辑
    AVAILABLE_AGENTS = {
        "general_web_search_agent": {
            "name": "通用网络搜索助手",
            "description": "一个能够利用搜索引擎和维基百科回答通用问题的助手。",
            "tools": [
                "SerpApiSearch",
                # "DuckDuckGoSearch",
                # "WikipediaTool"  # 确保这个工具在 tool_manager.py 中被正确初始化
            ]
        },
        "math_solver_agent": {
            "name": "数学计算助手",
            "description": "一个能够执行 Python 代码来解决复杂数学问题的助手。",
            "tools": [
                "PythonREPLTool"
            ]
        },
        "weather_reporter_agent": {
            "name": "天气查询助手",
            "description": "一个专门用于查询特定地点当前天气的助手。",
            "tools": [
                "OpenWeatherMapTool"
            ]
        }
    }

settings = Settings()