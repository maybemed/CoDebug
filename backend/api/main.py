# main.py
import logging

import uvicorn

logging.basicConfig(
    level=logging.DEBUG,  # 输出所有 DEBUG 及以上等级的日志
    format="%(asctime)s [%(levelname)s] %(message)s",
)
from fastapi import FastAPI
from backend.api.routers import prompt, kg, llm, agent, graph,highlight, map as map_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://192.168.1.105:8000"
    "http://192.168.1.106:3000",
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
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(highlight.router, prefix="/api/agent", tags=["graph"])

if __name__ == "__main__":
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)  # 设置为 True 可以在代码更改时自动重启服务器