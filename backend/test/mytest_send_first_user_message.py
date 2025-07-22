import streamlit as st
import requests
import time
import json
from datetime import datetime

st.set_page_config(page_title="自动发送首条用户信息测试", page_icon="🧪", layout="wide")

# API基础URL
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8000"

# 会话管理
if "all_session_ids" not in st.session_state:
    st.session_state.all_session_ids = [f"test_session_{int(time.time())}"]
if "current_session_index" not in st.session_state:
    st.session_state.current_session_index = 0
if "session_models" not in st.session_state:
    st.session_state.session_models = {}  # 每个会话的当前模型
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}

st.session_state.session_id = st.session_state.all_session_ids[st.session_state.current_session_index]

# 默认模型
DEFAULT_MODEL = "deepseek-chat"

# 工具函数

def api_post(endpoint, data, stream_output=False):
    url = f"{st.session_state.api_base_url}{endpoint}"
    headers = {"Content-Type": "application/json"}
    # 只有/qa/chat才允许流式
    if endpoint == "/api/llm/qa/chat" and stream_output:
        response = requests.post(url, json=data, headers=headers, stream=True)
        response.raise_for_status()
        def stream_gen():
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk.decode("utf-8", errors="ignore")
        return stream_gen()
    else:
        resp = requests.post(url, json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()

def api_get(endpoint):
    url = f"{st.session_state.api_base_url}{endpoint}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

# 侧边栏：会话管理
with st.sidebar:
    st.header("会话管理")
    selected = st.selectbox(
        "选择会话",
        options=[f"{s} (当前)" if s == st.session_state.session_id else s for s in st.session_state.all_session_ids],
        index=st.session_state.current_session_index
    )
    actual_selected = selected.replace(" (当前)", "")
    new_index = st.session_state.all_session_ids.index(actual_selected)
    if new_index != st.session_state.current_session_index:
        st.session_state.current_session_index = new_index
        st.session_state.session_id = st.session_state.all_session_ids[new_index]
        st.rerun()

    if st.button("➕ 创建新会话"):
        new_id = f"test_session_{int(time.time())}"
        st.session_state.all_session_ids.append(new_id)
        st.session_state.current_session_index = len(st.session_state.all_session_ids) - 1
        st.session_state.session_id = new_id
        st.session_state.session_models[new_id] = DEFAULT_MODEL
        st.session_state.chat_history[new_id] = []
        st.rerun()

    st.text_input("当前会话ID", value=st.session_state.session_id, disabled=True)

# 主界面
st.title("🧪 自动发送首条用户信息接口测试")

# 模型切换
st.subheader("当前模型")
model_name = st.text_input("模型名称", value=st.session_state.session_models.get(st.session_state.session_id, DEFAULT_MODEL))
if model_name != st.session_state.session_models.get(st.session_state.session_id, DEFAULT_MODEL):
    st.session_state.session_models[st.session_state.session_id] = model_name
    st.success(f"已切换模型为: {model_name}")

# 旅游prompt生成器和自动AI回复
with st.expander("🚗 生成旅游用户提示词并自动发送 (推荐体验)", expanded=True):
    with st.form("travel_form"):
        destination = st.text_input("目的地", "三亚")
        date = st.text_input("日期", "2024-08-01")
        budget = st.text_input("预算", "5000元")
        preference = st.text_input("用户偏好", "喜欢海边、怕晒、喜欢轻便穿搭")
        submitted = st.form_submit_button("生成用户提示词并自动发送")
        if submitted:
            req = {"destination": destination, "date": date, "budget": budget, "preference": preference}
            resp = api_post("/api/prompt/build_travel_prompt", req, stream_output=False)
            user_prompt = resp["user_prompt"]
            st.write("生成的用户提示词:")
            st.code(user_prompt)
            send_req = {"session_id": st.session_state.session_id, "user_prompt": user_prompt}
            send_resp = api_post("/api/prompt/send_first_user_message", send_req, stream_output=False)
            # 自动流式发送给大模型并展示回复
            chat_data = {
                "user_message": user_prompt,
                "session_id": st.session_state.session_id,
                "model_name": st.session_state.session_models.get(st.session_state.session_id, DEFAULT_MODEL),
                "temperature": 0.7
            }
            st.info(f"已自动发送首条用户信息: {user_prompt}")
            st.subheader("🤖 AI 首次回复 (流式)")
            message_placeholder = st.empty()
            full_response = ""
            response_stream = api_post("/api/llm/qa/chat", chat_data, stream_output=True)
            try:
                for chunk in response_stream:
                    lines = chunk.strip().split("\n")
                    for line in lines:
                        if line.startswith("data:"):
                            try:
                                data_str = line[len("data:"):].strip()
                                data_json = json.loads(data_str)
                                if data_json.get("type") == "content":
                                    content = data_json.get("content", "")
                                    full_response += content
                                    message_placeholder.markdown(full_response + "▌")
                            except Exception as e:
                                st.error(f"解析流数据出错：{e}")
                message_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"处理流式响应时发生错误: {e}")
            # 存入本地历史
            hist_key = st.session_state.session_id
            if hist_key not in st.session_state.chat_history:
                st.session_state.chat_history[hist_key] = []
            st.session_state.chat_history[hist_key].append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_message": user_prompt,
                "response": full_response,
                "model_name": st.session_state.session_models.get(st.session_state.session_id, DEFAULT_MODEL)
            })

# 聊天输入
st.subheader("💬 发送用户消息 (流式)")
user_message = st.text_area("用户消息", height=80, key=f"user_msg_{st.session_state.session_id}")
if st.button("🚀 发送消息", key=f"send_{st.session_state.session_id}"):
    if not user_message.strip():
        st.warning("请输入消息内容")
    else:
        chat_data = {
            "user_message": user_message,
            "session_id": st.session_state.session_id,
            "model_name": st.session_state.session_models.get(st.session_state.session_id, DEFAULT_MODEL),
            "temperature": 0.7
        }
        response_stream = api_post("/api/llm/qa/chat", chat_data, stream_output=True)
        st.subheader("🤖 AI 回复 (流式)")
        message_placeholder = st.empty()
        full_response = ""
        try:
            for chunk in response_stream:
                lines = chunk.strip().split("\n")
                for line in lines:
                    if line.startswith("data:"):
                        try:
                            data_str = line[len("data:"):].strip()
                            data_json = json.loads(data_str)
                            if data_json.get("type") == "content":
                                content = data_json.get("content", "")
                                full_response += content
                                message_placeholder.markdown(full_response + "▌")
                        except Exception as e:
                            st.error(f"解析流数据出错：{e}")
            message_placeholder.markdown(full_response)
            # 存入本地历史
            hist_key = st.session_state.session_id
            if hist_key not in st.session_state.chat_history:
                st.session_state.chat_history[hist_key] = []
            st.session_state.chat_history[hist_key].append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_message": user_message,
                "response": full_response,
                "model_name": st.session_state.session_models.get(st.session_state.session_id, DEFAULT_MODEL)
            })
        except Exception as e:
            st.error(f"处理流式响应时发生错误: {e}")

# 展示本地历史
hist_key = st.session_state.session_id
if hist_key in st.session_state.chat_history and st.session_state.chat_history[hist_key]:
    st.subheader("💭 本地会话历史")
    for chat in reversed(st.session_state.chat_history[hist_key][-5:]):
        with st.expander(f"({chat['timestamp']}) - {chat['user_message'][:30]}..."):
            st.markdown(f"**👤 用户:**\n> {chat['user_message']}")
            st.markdown(f"**🤖 AI ({chat['model_name']}):**\n> {chat['response']}") 