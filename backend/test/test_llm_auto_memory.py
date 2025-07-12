# @user: maybemed
# @last_update: 2025-07-11 09:08:45 UTC

import time
from backend.core.llm.llm_manager import LLMManager
from backend.core.llm.available_llms import AvailableLLMs
from backend.core.prompt_manager import PromptManager

def test_llm_memory_stream():
    """测试流式 LLM 记忆功能"""
    print("\n" + "=" * 60)
    print("测试 1: 流式 LLM 记忆功能")
    print("=" * 60)

    session_id = "maybemed_stream_test"

    # 第一轮流式对话
    print("\n📍 第一轮流式对话:")
    print("用户: 我正在学习大语言模型的应用开发")
    print("AI: ", end="", flush=True)

    for chunk in LLMManager.chat_with_memory_stream(
            user_message="我正在学习大语言模型的应用开发",
            session_id=session_id,
            model_name=AvailableLLMs.DeepSeek
    ):
        print(chunk, end="", flush=True)
        time.sleep(0.02)

    # 第二轮流式对话
    print("\n\n📍 第二轮流式对话:")
    print("用户: 能给我一些建议吗？")
    print("AI: ", end="", flush=True)

    for chunk in LLMManager.chat_with_memory_stream(
            user_message="能给我一些建议吗？",
            session_id=session_id,
            model_name=AvailableLLMs.DeepSeek
    ):
        print(chunk, end="", flush=True)
        time.sleep(0.02)

    print("\n\n✅ LLM 应该基于第一轮的学习内容给出相关建议")


def test_llm_memory_management():
    """测试 LLM 记忆管理功能"""
    print("\n" + "=" * 60)
    print("测试 2: LLM 记忆管理功能")
    print("=" * 60)

    session_id = "maybemed_memory_mgmt"

    # 添加一些对话
    print("📝 添加对话到记忆...")
    LLMManager.chat_with_memory(
        user_message="我的兴趣是机器学习",
        session_id=session_id,
        model_name=AvailableLLMs.DeepSeek
    )

    LLMManager.chat_with_memory(
        user_message="我目前在学习 transformer 架构",
        session_id=session_id,
        model_name=AvailableLLMs.DeepSeek
    )

    # 查看对话历史
    print("\n📋 查看对话历史:")
    history = LLMManager.get_conversation_history(session_id)
    print(f"对话历史中有 {len(history)} 条消息:")
    for i, msg in enumerate(history, 1):
        msg_type = type(msg).__name__.replace("Message", "")
        content = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
        print(f"  {i}. [{msg_type}] {content}")

    # 测试记忆效果
    print("\n🧠 测试记忆效果:")
    print("用户: 总结一下我们刚才聊的内容")
    print("AI: ", end="", flush=True)

    for chunk in LLMManager.chat_with_memory_stream(
            user_message="总结一下我们刚才聊的内容",
            session_id=session_id,
            model_name=AvailableLLMs.DeepSeek
    ):
        print(chunk, end="", flush=True)
        time.sleep(0.02)

    # 查看统计信息
    print("\n\n📊 对话统计信息:")
    stats = LLMManager.get_conversation_stats(session_id)
    print(f"  会话ID: {stats.get('session_id')}")
    print(f"  总消息数: {stats.get('total_messages')}")
    print(f"  消息类型: {stats.get('message_types')}")
    print(f"  总字符数: {stats.get('total_characters')}")
    print(f"  估算token数: {stats.get('estimated_tokens')}")

    # 清除记忆
    print("\n🗑️ 清除记忆...")
    LLMManager.clear_conversation_history(session_id)

    # 验证记忆已清除
    print("验证记忆清除效果:")
    print("用户: 我们刚才聊了什么？")
    response = LLMManager.chat_with_memory(
        user_message="我们刚才聊了什么？",
        session_id=session_id,
        model_name=AvailableLLMs.DeepSeek
    )
    print(f"AI: {response}")
    print("✅ 记忆已清除，AI 不再记得之前的对话")


def test_llm_multiple_sessions():
    """测试多会话隔离"""
    print("\n" + "=" * 60)
    print("测试 5: LLM 多会话隔离")
    print("=" * 60)

    # 会话 A
    session_a = "maybemed_session_A"
    print("🅰️ 会话 A:")
    print("用户: 我是前端开发者，专注 React 开发")
    LLMManager.chat_with_memory(
        user_message="我是前端开发者，专注 React 开发",
        session_id=session_a,
        model_name=AvailableLLMs.DeepSeek
    )
    print("✅ 会话 A 记录完成")

    # 会话 B
    session_b = "maybemed_session_B"
    print("\n🅱️ 会话 B:")
    print("用户: 我是后端工程师，主要用 Python Django")
    LLMManager.chat_with_memory(
        user_message="我是后端工程师，主要用 Python Django",
        session_id=session_b,
        model_name=AvailableLLMs.DeepSeek
    )
    print("✅ 会话 B 记录完成")

    # 在会话 A 中测试记忆
    print("\n🔍 在会话 A 中测试:")
    print("用户: 你知道我的技术栈是什么吗？")
    response_a = LLMManager.chat_with_memory(
        user_message="你知道我的技术栈是什么吗？",
        session_id=session_a,
        model_name=AvailableLLMs.DeepSeek
    )
    print(f"AI: {response_a}")
    print("✅ 会话 A 应该回答 React 前端开发")

    # 在会话 B 中测试记忆
    print("\n🔍 在会话 B 中测试:")
    print("用户: 你知道我的技术栈是什么吗？")
    response_b = LLMManager.chat_with_memory(
        user_message="你知道我的技术栈是什么吗？",
        session_id=session_b,
        model_name=AvailableLLMs.DeepSeek
    )
    print(f"AI: {response_b}")
    print("✅ 会话 B 应该回答 Python Django 后端开发")

    # 显示所有活跃会话
    print("\n📋 所有活跃 LLM 会话:")
    active_conversations = LLMManager.list_active_conversations()
    print(f"活跃会话: {active_conversations}")


def main():
    """运行所有测试"""
    print("🧠 LLM 记忆功能完整测试")
    print(f"当前时间: 2025-07-11 09:08:45 UTC")
    print(f"当前用户: maybemed")
    print("=" * 60)

    try:
        # 运行所有测试
        test_llm_memory_stream()
        print("="*46)
        print("="*46)
        test_llm_memory_management()
        print("="*46)
        print("="*46)
        test_llm_multiple_sessions()

        print("\n" + "🎉" * 20)
        print("所有 LLM 记忆测试完成！")
        print("🎉" * 20)

        # 最终统计
        print("\n📊 最终 LLM 对话统计:")
        all_stats = LLMManager.get_conversation_stats()
        print(f"总会话数: {len(all_stats)}")
        for session_id, stats in all_stats.items():
            print(f"  {session_id}: {stats['total_messages']} 条消息, {stats['estimated_tokens']} tokens")

        print(f"\n📋 活跃 LLM 会话: {LLMManager.list_active_conversations()}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    main()