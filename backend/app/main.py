from fastapi import FastAPI
from .api.endpoints import qa, kg, prompt

app = FastAPI()

# tags用于指定路由的标签，方便在文档中进行分类
app.include_router(qa.router, prefix="/api/qa", tags=["qa"])
app.include_router(kg.router, prefix="/api/kg", tags=["kg"])
app.include_router(prompt.router, prefix="/api/prompt", tags=["prompt"])