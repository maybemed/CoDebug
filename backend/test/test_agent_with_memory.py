# @user: maybemed
# @last_update: 2025-07-11 08:40:59 UTC
# @version: complete_memory_agent_tests

import time
from typing import List
from backend.core.agent.agent_manager import AgentManager
from backend.core.prompt_manager import PromptManager
from backend.utils.logger import logger


def test_basic_memory_functionality():
    """测试基础记忆功能"""
    print("=" * 60)
    print("测试 1: 基础记忆功能")
    print("=" * 60)

    session_id = "maybemed_basic_test"
    agent_name = "general_web_search_agent"

    # 第一轮对话
    print("\n📍 第一轮对话:")
    print("用户: 帮我搜索一下 Python FastAPI 教程")
    print("AI: ", end="", flush=True)

    response1 = ""
    for chunk in AgentManager.run_agent_with_memory_stream(
            agent_name=agent_name,
            user_input="帮我搜索一下 Python FastAPI 教程",
            session_id=session_id,
            memory_window=5  # 保留5轮对话
    ):
        print(chunk, end="", flush=True)
        response1 += chunk
        time.sleep(0.02)

    print(f"\n\n✅ 第一轮完成，回复长度: {len(response1)} 字符")

    # 第二轮对话 - 测试记忆功能
    print("\n📍 第二轮对话（测试记忆）:")
    print("用户: 第一个教程看起来不错，能详细介绍一下吗？")
    print("AI: ", end="", flush=True)

    response2 = ""
    for chunk in AgentManager.run_agent_with_memory_stream(
            agent_name=agent_name,
            user_input="第一个教程看起来不错，能详细介绍一下吗？",
            session_id=session_id
    ):
        print(chunk, end="", flush=True)
        response2 += chunk
        time.sleep(0.02)

    print(f"\n\n✅ 第二轮完成，Agent 应该能理解'第一个教程'指的是什么")

    # 查看记忆历史
    print("\n📋 当前记忆历史:")
    history = AgentManager.get_agent_memory_history(session_id, agent_name)
    for i, msg in enumerate(history, 1):
        msg_type = type(msg).__name__.replace("Message", "")
        content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
        print(f"  {i}. [{msg_type}] {content}")


def test_memory_management():
    """测试记忆管理功能"""
    print("\n" + "=" * 60)
    print("测试 2: 记忆管理功能")
    print("=" * 60)

    session_id = "maybemed_memory_mgmt"
    agent_name = "general_web_search_agent"

    # 添加一些对话
    print("📝 添加对话到记忆...")
    AgentManager.run_agent_with_memory(
        agent_name=agent_name,
        user_input="我的名字是 maybemed，我是一个开发者",
        session_id=session_id
    )

    AgentManager.run_agent_with_memory(
        agent_name=agent_name,
        user_input="我正在学习 AI 和机器学习",
        session_id=session_id
    )

    # 查看记忆历史
    print("\n📋 查看记忆历史:")
    history = AgentManager.get_agent_memory_history(session_id, agent_name)
    print(f"记忆中有 {len(history)} 条消息:")
    for i, msg in enumerate(history, 1):
        msg_type = type(msg).__name__.replace("Message", "")
        content = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
        print(f"  {i}. [{msg_type}] {content}")

    # 测试记忆是否生效
    print("\n🧠 测试记忆效果:")
    print("用户: 你还记得我的名字吗？")
    print("AI: ", end="", flush=True)

    for chunk in AgentManager.run_agent_with_memory_stream(
            agent_name=agent_name,
            user_input="你还记得我的名字吗？",
            session_id=session_id
    ):
        print(chunk, end="", flush=True)
        time.sleep(0.02)

    # 查看记忆统计
    print("\n\n📊 记忆统计信息:")
    stats = AgentManager.get_memory_stats()
    for key, stat in stats.items():
        if session_id in key:
            print(f"  会话: {stat['session_id']}")
            print(f"  Agent: {stat['agent_name']}")
            print(f"  消息数: {stat['message_count']}")
            print(f"  窗口大小: {stat['memory_window']}")
            print(f"  内容预览: {stat['context_preview']}")

    # 清除记忆
    print("\n🗑️ 清除记忆...")
    AgentManager.clear_agent_memory(session_id, agent_name)

    # 验证记忆已清除
    print("验证记忆清除效果:")
    print("用户: 你还记得我的名字吗？")
    print("AI: ", end="", flush=True)

    for chunk in AgentManager.run_agent_with_memory_stream(
            agent_name=agent_name,
            user_input="你还记得我的名字吗？",
            session_id=session_id
    ):
        print(chunk, end="", flush=True)
        time.sleep(0.02)

    print("\n✅ 记忆已清除，Agent 不再记得之前的信息")


def test_multiple_sessions():
    """测试多会话隔离"""
    print("\n" + "=" * 60)
    print("测试 3: 多会话记忆隔离")
    print("=" * 60)

    agent_name = "general_web_search_agent"

    # 会话 A
    session_a = "maybemed_session_A"
    print("🅰️ 会话 A:")
    print("用户: 我喜欢编程，特别是 Python")
    AgentManager.run_agent_with_memory(
        agent_name=agent_name,
        user_input="我喜欢编程，特别是 Python",
        session_id=session_a
    )
    print("✅ 会话 A 记录完成")

    # 会话 B
    session_b = "maybemed_session_B"
    print("\n🅱️ 会话 B:")
    print("用户: 我是设计师，对 UI/UX 很感兴趣")
    AgentManager.run_agent_with_memory(
        agent_name=agent_name,
        user_input="我是设计师，对 UI/UX 很感兴趣",
        session_id=session_b
    )
    print("✅ 会话 B 记录完成")

    # 在会话 A 中测试记忆
    print("\n🔍 在会话 A 中测试:")
    print("用户: 你知道我的兴趣是什么吗？")
    print("AI: ", end="", flush=True)

    for chunk in AgentManager.run_agent_with_memory_stream(
            agent_name=agent_name,
            user_input="你知道我的兴趣是什么吗？",
            session_id=session_a
    ):
        print(chunk, end="", flush=True)
        time.sleep(0.02)

    print("\n✅ 会话 A 应该回答 Python 编程")

    # 在会话 B 中测试记忆
    print("\n🔍 在会话 B 中测试:")
    print("用户: 你知道我的兴趣是什么吗？")
    print("AI: ", end="", flush=True)

    for chunk in AgentManager.run_agent_with_memory_stream(
            agent_name=agent_name,
            user_input="你知道我的兴趣是什么吗？",
            session_id=session_b
    ):
        print(chunk, end="", flush=True)
        time.sleep(0.02)

    print("\n✅ 会话 B 应该回答 UI/UX 设计")

    # 显示所有活跃会话
    print("\n📋 所有活跃会话:")
    active_sessions = AgentManager.list_active_sessions()
    print(f"活跃会话: {active_sessions}")


def main():
    """运行所有测试"""
    print("🧠 Agent 记忆功能完整测试")
    print(f"当前时间: 2025-07-11 08:40:59 UTC")
    print(f"当前用户: maybemed")
    print("=" * 60)

    try:
        # 运行所有测试
        test_basic_memory_functionality()

        test_memory_management()
        test_multiple_sessions()

        print("\n" + "🎉" * 20)
        print("所有 Agent 记忆测试完成！")
        print("🎉" * 20)

        # 最终统计
        print("\n📊 最终记忆统计:")
        final_stats = AgentManager.get_memory_stats()
        print(f"总记忆实例数: {len(final_stats)}")
        for key, stats in final_stats.items():
            print(f"  {key}: {stats['message_count']} 条消息")

        print(f"\n📋 活跃会话: {AgentManager.list_active_sessions()}")

    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    main()