from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from backend.core.llm.llm_manager import LLMManager
from backend.core.llm.available_llms import AvailableLLMs
from backend.core.prompt_manager import PromptManager


def test_basic_history_usage():
    """基础的 history 使用示例"""
    print("=== 基础 History 使用 ===")

    # 1. 初始化空的 history
    conversation_history: List[BaseMessage] = []

    # 2. 第一轮对话
    user_input_1 = "我想学习 Python 编程"
    print(f"用户: {user_input_1}")
    print("AI: ", end="", flush=True)

    # 流式对话
    ai_response_1 = ""
    for chunk in LLMManager.chat_with_history_stream(
            user_message=user_input_1,
            history=conversation_history,  # 空的 history
            model_name=AvailableLLMs.DeepSeek,
            system_prompt_name="default"
    ):
        print(chunk, end="", flush=True)
        ai_response_1 += chunk

    # 3. 将这轮对话添加到 history
    conversation_history.append(HumanMessage(content=user_input_1))
    conversation_history.append(AIMessage(content=ai_response_1))

    print(f"\n\n当前 history 长度: {len(conversation_history)} 条消息\n")

    # 4. 第二轮对话（基于之前的上下文）
    user_input_2 = "从哪里开始比较好？"  # 这里的"从哪里"指的是学习Python
    print(f"用户: {user_input_2}")
    print("AI: ", end="", flush=True)

    ai_response_2 = ""
    for chunk in LLMManager.chat_with_history_stream(
            user_message=user_input_2,
            history=conversation_history,  # 包含前面对话的 history
            model_name=AvailableLLMs.DeepSeek,
            system_prompt_name="default"
    ):
        print(chunk, end="", flush=True)
        ai_response_2 += chunk

    # 5. 更新 history
    conversation_history.append(HumanMessage(content=user_input_2))
    conversation_history.append(AIMessage(content=ai_response_2))

    print(f"\n\n最终 history 长度: {len(conversation_history)} 条消息")

    # 6. 查看完整对话历史
    print("\n=== 完整对话历史 ===")
    for i, msg in enumerate(conversation_history):
        msg_type = type(msg).__name__.replace("Message", "")
        content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        print(f"{i + 1}. [{msg_type}] {content}")


if __name__ == "__main__":
    test_basic_history_usage()