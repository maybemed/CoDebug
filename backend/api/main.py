# main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,  # 输出所有 DEBUG 及以上等级的日志
    format="%(asctime)s [%(levelname)s] %(message)s",
)
from fastapi import FastAPI
from backend.api.routers import image, prompt, kg, llm, agent, map as map_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8502",  # 假设 Streamlit 运行在 8502 端口
    "http://192.168.1.111:8000",
    "http://192.168.1.108:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法 (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # 允许所有 HTTP 头
)

# tags用于指定路由的标签，方便在文档中进行分类
app.include_router(kg.router, prefix="/api/kg", tags=["kg"])
app.include_router(prompt.router, prefix="/api/prompt", tags=["prompt"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
#app.include_router(llm.router, tags=["LLM Core"]) # *这一行修改了
app.include_router(map_router.router, prefix="/api/map", tags=["map"])
app.include_router(image.router, prefix="/api/image", tags=["image"])

if __name__ == "__main__":
    uvicorn.run("backend.api.main:app",host="192.168.1.108", port=8000)