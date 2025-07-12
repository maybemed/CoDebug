from langchain_core.callbacks import BaseCallbackHandler


class AgentStreamingCallbackHandler(BaseCallbackHandler):
    """Agent 流式输出回调处理器"""

    def __init__(self):
        self.tokens = []
        self.current_step = ""
        self.finished = False

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """当收到新token时调用"""
        self.tokens.append(token)

    def on_agent_action(self, action, **kwargs) -> None:
        """当Agent执行动作时调用"""
        self.current_step = f"🔧 使用工具: {action.tool} - {action.tool_input}"

    def on_agent_finish(self, finish, **kwargs) -> None:
        """当Agent完成时调用"""
        self.finished = True

    def get_content(self) -> str:
        """获取完整内容"""
        return "".join(self.tokens)