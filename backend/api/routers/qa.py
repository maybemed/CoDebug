from fastapi import APIRouter, Body
from backend.utils.langchain_helper import llm_helper

router = APIRouter()

@router.post("")
async def qa(question: str = Body(...), system_prompt: str = Body("")):
    # 表示 question 参数的值将从请求的 JSON 体中获取。如果请求体中没有 {"question": "..."} 这样的键值对，FastAPI 会返回错误。
    # 如果请求体中没有 {"system_prompt": "..."} 这样的键值对，FastAPI 会使用默认值 ""。
    try:
        answer = await llm_helper.ask_question(question, system_prompt)
        return {"answer": answer}
    except Exception as e:
        print(f"Error in qa endpoint: {e}") # 添加这一行，捕获并打印异常
        import traceback
        traceback.print_exc() # 打印完整的错误堆栈
        raise # 重新抛出异常，让FastAPI返回500错误