# test_prompt_api.py
import streamlit as st
import requests

# 默认后端接口地址
API_BASE = "http://localhost:8000"  # 视你的FastAPI启动端口而定
PROMPT_ENDPOINT = f"{API_BASE}/api/prompt"

st.set_page_config(page_title="Prompt 管理测试工具", layout="wide")
st.title("🧪 Prompt 管理接口测试工具")

# 获取当前系统提示词
st.header("🔍 获取系统提示词")
if st.button("获取系统提示词"):
    try:
        res = requests.get(PROMPT_ENDPOINT)
        if res.status_code == 200:
            prompt = res.json().get("system_prompt", "")
            st.success(f"当前系统提示词：\n\n{prompt}")
        else:
            st.error(f"获取失败，状态码：{res.status_code}，错误信息：{res.text}")
    except Exception as e:
        st.error(f"请求出错：{e}")

# 更新系统提示词
st.header("✏️ 更新系统提示词")
new_prompt = st.text_area("请输入新的系统提示词", height=200)

if st.button("更新系统提示词"):
    try:
        res = requests.post(PROMPT_ENDPOINT, json={"prompt": new_prompt})
        if res.status_code == 200:
            data = res.json()
            st.success(f"更新成功：{data['msg']}\n\n新系统提示词：{data['system_prompt']}")
        else:
            st.error(f"更新失败，状态码：{res.status_code}，错误信息：{res.text}")
    except Exception as e:
        st.error(f"请求出错：{e}")
