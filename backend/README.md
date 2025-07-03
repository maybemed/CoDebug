# 后端使用说明

## 启动API服务
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 配置API密钥

1. 在 `backend/` 目录下配置 `.env` 文件，内容如下：
   ```
   DEEPSEEK_API_KEY=你的key
   DEEPSEEK_API_BASE=https://api.deepseek.com
   DEEPSEEK_MODEL=deepseek-chat
   DEEPSEEK_TEMPERATURE=0.7
   ```
2. 安装依赖：`pip install -r requirements.txt`
3. 启动服务即可。

## 关系三元组抽取函数

- 位置：`app/core/rte.py`
- 函数：`rte_from_text(document, output_path)`
- 用法示例：
```python
from app.core.rte import rte_from_text
rte_from_text("你的文本内容", "app/knowledge/triples.json")
``` 