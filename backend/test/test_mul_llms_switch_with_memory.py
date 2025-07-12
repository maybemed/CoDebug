# @user: maybemed
# @last_update: 2025-07-11 11:25:05 UTC

import time

from backend.core.llm.available_llms import AvailableLLMs
from backend.core.llm.llm_manager import LLMManager
from backend.core.llm import available_llms
from backend.core.prompt_manager import PromptManager


def test_multi_instance_isolation():
    """测试多实例隔离"""
    print("=" * 60)
    print("测试 1: 多实例隔离")
    print("=" * 60)

    # 创建同一模型的多个实例
    instance1 = LLMManager.create_llm_instance(
        instance_id="deepseek_instance_1",
        model_name=AvailableLLMs.DeepSeek,
        temperature=0.7
    )

    instance2 = LLMManager.create_llm_instance(
        instance_id="deepseek_instance_2",
        model_name=AvailableLLMs.DeepSeek,
        temperature=0.3  # 不同的温度
    )

    # 在实例1中进行对话
    print("\n🔵 实例1对话:")
    print("用户: 我是 Alice，喜欢绘画")
    response1 = LLMManager.chat_with_instance(
        instance_id="deepseek_instance_1",
        user_message="我是 Alice，喜欢绘画",
        session_id="session_001"
    )
    print(f"AI: {response1}")

    # 在实例2中进行对话
    print("\n🔴 实例2对话:")
    print("用户: 我是 Bob，喜欢编程")
    response2 = LLMManager.chat_with_instance(
        instance_id="deepseek_instance_2",
        user_message="我是 Bob，喜欢编程",
        session_id="session_001"  # 相同的session_id
    )
    print(f"AI: {response2}")

    # 测试记忆隔离
    print("\n🔍 测试记忆隔离:")
    print("实例1 - 用户: 你还记得我的名字和爱好吗？")
    response3 = LLMManager.chat_with_instance(
        instance_id="deepseek_instance_1",
        user_message="你还记得我的名字和爱好吗？",
        session_id="session_001"
    )
    print(f"实例1 AI: {response3}")

    print("\n实例2 - 用户: 你还记得我的名字和爱好吗？")
    response4 = LLMManager.chat_with_instance(
        instance_id="deepseek_instance_2",
        user_message="你还记得我的名字和爱好吗？",
        session_id="session_001"
    )
    print(f"实例2 AI: {response4}")

    print("\n✅ 两个实例应该分别记住 Alice(绘画) 和 Bob(编程)")


def test_model_switching():
    """测试模型切换功能"""
    print("\n" + "=" * 60)
    print("测试 2: 模型切换功能")
    print("=" * 60)

    session_id = "model_switching_session"

    # 使用 DeepSeek 开始对话
    print("\n🤖 使用 DeepSeek 模型:")
    print("用户: 我在学习机器学习，请给我一些简短的建议")
    print("AI: ", end="", flush=True)

    for chunk in LLMManager.chat_with_model_switching_stream(
            user_message="我在学习机器学习，请给我一些简短的建议",
            session_id=session_id,
            model_name=AvailableLLMs.DeepSeek
    ):
        print(chunk, end="", flush=True)
        time.sleep(0.02)

    # 切换到 Qwen 继续对话
    print("\n\n🧠 切换到 Qwen 模型:")
    print("用户: 刚才你提到的第一点，能详细解释一下吗？")
    print("AI: ", end="", flush=True)

    for chunk in LLMManager.chat_with_model_switching_stream(
            user_message="刚才你提到的第一点，能详细解释一下吗？",
            session_id=session_id,
            model_name=AvailableLLMs.Qwen  # 切换模型
    ):
        print(chunk, end="", flush=True)
        time.sleep(0.02)

    # 再切换到 Zhipu
    print("\n\n🎯 切换到 Zhipu 模型:")
    print("用户: 基于我们的讨论，推荐一个学习路径")
    print("AI: ", end="", flush=True)

    for chunk in LLMManager.chat_with_model_switching_stream(
            user_message="基于我们的讨论，推荐一个学习路径",
            session_id=session_id,
            model_name=AvailableLLMs.Zhipu  # 再次切换
    ):
        print(chunk, end="", flush=True)
        time.sleep(0.02)

    print("\n\n✅ 模型切换完成，对话记忆应该保持连续")


def test_management_functions():
    """测试管理功能"""
    print("\n" + "=" * 60)
    print("测试 4: 管理功能")
    print("=" * 60)

    # 列出所有实例
    print("📋 所有 LLM 实例:")
    instances = LLMManager.list_llm_instances()
    for instance_id, stats in instances.items():
        print(
            f"  {instance_id}: {stats['model_name']} (T={stats['temperature']}, 会话数={stats['active_conversations']})")

    # 列出所有共享对话
    print("\n📋 所有共享对话:")
    conversations = LLMManager.list_shared_conversations()
    for session_id, stats in conversations.items():
        print(f"  {session_id}: 当前模型={stats['current_model']}, 消息数={stats['total_messages']}")
        print(f"    模型使用统计: {stats['model_usage']}")

    # 查看对话历史
    print("\n📜 查看共享对话历史:")
    history = LLMManager.get_shared_conversation_history("creative_writing")
    print(f"历史消息数: {len(history)}")
    for i, msg in enumerate(history[-4:], 1):  # 显示最后4条
        msg_type = type(msg).__name__.replace("Message", "")
        content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        print(f"  {i}. [{msg_type}] {content}")

    print("\n✅ 管理功能测试完成")


def main():
    """运行所有测试"""
    print("🚀 多实例和模型切换功能测试")
    print(f"当前时间: 2025-07-11 11:25:05 UTC")
    print(f"当前用户: maybemed")
    print("=" * 60)

    try:
        # test_multi_instance_isolation()
        test_model_switching()
        test_management_functions()

        print("\n" + "🎉" * 20)
        print("所有测试完成！")
        print("🎉" * 20)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    main()