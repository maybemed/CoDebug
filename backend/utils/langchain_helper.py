import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

# 加载.env文件
load_dotenv()

class LLMHelper:
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", 0.7))
        )

    async def get_completion_from_messages(self, messages, system_prompt=None):
        chat_messages = []
        if system_prompt:
            chat_messages.append(SystemMessage(content=system_prompt))
        for msg in messages:
            if msg['role'] == 'user':
                chat_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'system':
                chat_messages.append(SystemMessage(content=msg['content']))
        return (await self.llm.agenerate([chat_messages])).generations[0][0].text

    async def ask_question(self, question, system_prompt=None):
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': question})
        return await self.get_completion_from_messages(messages, system_prompt)

# 单例实例，便于全局调用
llm_helper = LLMHelper() 