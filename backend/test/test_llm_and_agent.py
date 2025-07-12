# @user: maybemed
# @last_update: 2025-07-11 07:29:43 UTC

from backend.core.prompt_manager import PromptManager
from backend.core.agent.agent_manager import AgentManager


def test_dynamic_prompt_update():
    """测试动态更新 Agent 系统提示词"""

    # 1. 创建一个 Agent（使用默认提示词）
    agent1 = AgentManager.get_agent(
        agent_name="general_web_search_agent",
        llm_model_name="deepseek-chat",
        system_prompt_name="default"
    )
    print("创建了使用默认提示词的 Agent")

    # 2. 创建自定义提示词
    PromptManager.create_system_prompt(
        name="search_expert",
        content="""你是一个搜索专家，擅长快速找到准确和相关的信息。

你的专长：
1. 快速理解用户的搜索意图
2. 选择最佳的搜索策略
3. 从搜索结果中提取关键信息
4. 提供简洁而全面的答案

当前时间：{current_time}
用户：{user_name}""",
        description="搜索专家模式"
    )

    # 3. 更新 Agent 使用新的提示词
    success = AgentManager.update_agent_system_prompt(
        agent_name="general_web_search_agent",
        llm_model_name="deepseek-chat",
        new_system_prompt_name="search_expert"
    )

    if success:
        print("成功更新 Agent 的系统提示词")

    # 4. 获取更新后的 Agent（应该使用新提示词）
    agent2 = AgentManager.get_agent(
        agent_name="general_web_search_agent",
        llm_model_name="deepseek-chat",
        system_prompt_name="search_expert"
    )

    # 5. 验证它们是不同的实例
    print(f"Agent1 和 Agent2 是否为同一实例: {agent1 is agent2}")  # 应该是 False

    # 6. 查看当前缓存情况
    cached_info = AgentManager.get_cached_agents_info()
    print("当前缓存的 Agent:")
    for cache_key, description in cached_info.items():
        print(f"  {cache_key}: {description}")


if __name__ == "__main__":
    test_dynamic_prompt_update()