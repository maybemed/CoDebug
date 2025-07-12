# @user: maybemed
# @last_update: 2025-07-11 07:54:18 UTC

import time
from backend.core.llm.llm_manager import LLMManager
from backend.core.llm.available_llms import AvailableLLMs
from backend.core.agent.agent_manager import AgentManager
from backend.core.prompt_manager import PromptManager


def test_llm_streaming():
    """测试 LLM 流式输出"""
    print("=== LLM 流式输出测试 ===")

    # 1. 生成器方式
    print("生成器方式:")
    full_response = ""
    for chunk in LLMManager.chat_with_prompt_stream(
            user_message="请详细介绍一下 Python 编程语言的特点和优势",
            model_name=AvailableLLMs.DeepSeek,
            system_prompt_name="default",
            temperature=0.7
    ):
        print(chunk, end="", flush=True)
        full_response += chunk
        time.sleep(0.02)  # 模拟打字机效果

    print(f"\n\n完整回复长度: {len(full_response)} 字符")



def test_agent_streaming():
    """测试 Agent 流式输出"""
    print("\n=== Agent 流式输出测试 ===")

    # 创建一个简单的提示词
    PromptManager.create_system_prompt(
        name="research_assistant",
        content="""你是一个研究助手，当前时间是 {current_time}。

你的任务：
1. 使用可用的工具搜索信息
2. 提供准确和有用的回答
3. 引用可靠的来源

用户：{user_name}""",
        description="研究助手模式"
    )

    print("Agent 流式执行:")
    full_result = ""
    for chunk in AgentManager.run_agent_stream(
            agent_name="general_web_search_agent",
            user_input="搜索一下2024年人工智能的最新发展趋势",
            llm_model_name=AvailableLLMs.DeepSeek,
            system_prompt_name="research_assistant"
    ):
        print(chunk, end="", flush=True)
        full_result += chunk
        time.sleep(0.03)

    print(f"\n\nAgent 执行完成，结果长度: {len(full_result)} 字符")



if __name__ == "__main__":
    try:
        test_llm_streaming()
        test_agent_streaming()

        print("\n🎉 所有流式输出测试完成！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")