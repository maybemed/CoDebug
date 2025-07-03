# LLM 问答与知识图谱系统

## 目录结构
- backend/  后端FastAPI+LangChain服务
- frontend/ 前端Vue CLI项目

## 启动方式

### 后端
```bash
cd backend
pip install -r requirements.txt (只需在当前环境中pip一次)
uvicorn app.main:app --reload
```

### 前端
```bash
cd frontend
npm install (只需在当前环境中install一次)
npm run serve
```

### 关系三元组抽取
- 函数位置：`backend/app/core/rte.py`
- 用法：
```python
from app.core.rte import rte_from_text
rte_from_text("你的文本内容", "app/knowledge/triples.json")
``` 