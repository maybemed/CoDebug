import streamlit as st
import requests
import json
from typing import Dict, Any, Generator
import time
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="LLM API 测试工具",
    page_icon="🤖",
    layout="wide"
)

# 全局配置
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8501"  # 假设您的 FastAPI 运行在 8000 端口

# 会话管理
if "all_session_ids" not in st.session_state:
    st.session_state.all_session_ids = [f"test_session_{int(time.time())}"]
if "current_session_index" not in st.session_state:
    st.session_state.current_session_index = 0

# 基于当前索引设置活跃的 session_id
st.session_state.session_id = st.session_state.all_session_ids[st.session_state.current_session_index]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  # 为每个会话存储独立的聊天历史


def make_api_request(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None, stream_output: bool = False):
    """
    发送API请求的核心函数。

    Args:
        endpoint (str): API的路径.
        method (str): HTTP方法 (GET, POST, DELETE).
        data (Dict, optional): 发送的JSON数据.
        stream_output (bool): ✅ 关键参数：如果为True，则以流式处理响应.

    Returns:
        - 如果 stream_output 为 True，返回一个生成器 (Generator) 来逐块读取响应.
        - 否则，返回一个包含JSON响应的字典 (dict).
    """
    url = f"{st.session_state.api_base_url}{endpoint}"
    headers = {"Content-Type": "application/json", "Accept": "text/plain"}

    try:
        if method == "POST":
            # ✅ **修改点 1: 处理流式请求**
            if stream_output:
                # 使用 stream=True 参数，requests库不会立即下载全部内容
                response = requests.post(url, json=data, headers=headers, stream=True)
                response.raise_for_status()

                # ✅ **修改点 2: 返回一个生成器**
                # 这个生成器会逐块(chunk)地 yield 解码后的响应内容
                def stream_generator() -> Generator[str, None, None]:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            # 将字节解码为UTF-8字符串
                            yield chunk.decode("utf-8", errors="ignore")

                return stream_generator()
            else:
                # 非流式请求保持不变
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
                return response.json()

        elif method in ["GET", "DELETE"]:
            # GET 和 DELETE 请求通常不用于流式输出
            response = requests.request(method, url, headers=headers)
            response.raise_for_status()
            return response.json()

        else:
            return {"error": f"Unsupported method: {method}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"请求失败: {str(e)}"}
    except json.JSONDecodeError:
        response_text = response.text if 'response' in locals() else "无原始响应"
        return {"error": f"响应不是有效的JSON格式: {response_text}"}


def display_json_response(response: Dict[Any, Any], title: str = "API响应"):
    """美化显示JSON响应"""
    st.subheader(title)

    if isinstance(response, dict) and "error" in response:
        st.error(f"错误: {response['error']}")
    else:
        st.success("请求成功")

    with st.expander("查看完整响应", expanded=True):
        st.json(response)


def main():
    st.title("🤖 LLM API 测试工具")

    # --- 侧边栏 ---
    with st.sidebar:
        st.header("⚙️ 配置")
        new_base_url = st.text_input("API基础URL", value=st.session_state.api_base_url)
        if new_base_url != st.session_state.api_base_url:
            st.session_state.api_base_url = new_base_url
            st.rerun()

        st.subheader("🗓️ 会话管理")
        selected_session_label = st.selectbox(
            "选择会话",
            options=[f"{s} (当前)" if s == st.session_state.session_id else s for s in
                     st.session_state.all_session_ids],
            index=st.session_state.current_session_index
        )
        actual_selected_session_id = selected_session_label.replace(" (当前)", "")
        new_index = st.session_state.all_session_ids.index(actual_selected_session_id)
        if new_index != st.session_state.current_session_index:
            st.session_state.current_session_index = new_index
            st.session_state.session_id = st.session_state.all_session_ids[new_index]
            st.rerun()

        if st.button("➕ 创建新会话"):
            new_session_id = f"test_session_{int(time.time())}"
            st.session_state.all_session_ids.append(new_session_id)
            st.session_state.current_session_index = len(st.session_state.all_session_ids) - 1
            st.session_state.session_id = new_session_id
            if new_session_id not in st.session_state.chat_history:
                st.session_state.chat_history[new_session_id] = []
            st.rerun()

        st.text_input("当前会话ID", value=st.session_state.session_id, disabled=True)

    # --- 功能标签页 ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 获取模型列表", "💬 对话测试", "📚 对话历史", "🗑️ 清除历史", "📊 会话实例"
    ])

    # 标签页1: 获取模型列表 (无变化)
    with tab1:
        st.header("📋 获取可用模型列表")
        if st.button("获取模型列表", key="get_models"):
            response = make_api_request("/models")
            display_json_response(response)
            if isinstance(response, dict) and "models" in response:
                st.subheader("🎯 可用模型")
                for model in response["models"]:
                    with st.expander(f"🤖 {model['model_name']} ({model['provider']})"):
                        st.write(f"**描述:** {model['description']}")

    # 标签页2: 对话测试
    with tab2:
        st.header("💬 LLM对话测试 (流式)")
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("🎛️ 对话参数")
            user_message = st.text_area("用户消息", height=100, key=f"user_msg_{st.session_state.session_id}")
            model_name = st.text_input("模型名称", value="deepseek-chat",
                                       key=f"model_name_{st.session_state.session_id}")
            temperature = st.slider("温度", 0.0, 2.0, 0.7, 0.1, key=f"temp_{st.session_state.session_id}")

        with col2:
            st.subheader("📝 操作")
            if st.button("🚀 发送消息 (测试流式)", key=f"send_{st.session_state.session_id}", type="primary"):
                if not user_message.strip():
                    st.warning("请输入消息内容")
                else:
                    chat_data = {
                        "user_message": user_message,
                        "session_id": st.session_state.session_id,
                        "model_name": model_name,
                        "temperature": temperature,
                        # 其他参数可以按需添加
                    }

                    # ✅ **修改点 3: 调用API并处理流式响应**
                    # 调用 make_api_request 时，设置 stream_output=True
                    response_stream = make_api_request("/qa/chat", "POST", chat_data, stream_output=True)

                    # 检查返回的是否是错误字典
                    if isinstance(response_stream, dict) and "error" in response_stream:
                        display_json_response(response_stream)
                    else:
                        st.subheader("🤖 AI 回复 (流式)")
                        # 创建一个空占位符，用于后续更新内容
                        message_placeholder = st.empty()
                        full_response = ""
                        try:
                            # 遍历从API返回的生成器
                            for chunk in response_stream:
                                # 每个chunk可能是一行完整的 data: {...}，或者多个data片段组成
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

                            # 循环结束后，用最终的完整内容更新占位符（去掉光标）
                            message_placeholder.markdown(full_response)

                            # 将本次对话存入本地会话历史
                            history_key = st.session_state.session_id
                            if history_key not in st.session_state.chat_history:
                                st.session_state.chat_history[history_key] = []

                            st.session_state.chat_history[history_key].append({
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "user_message": user_message,
                                "response": full_response,
                                "model_name": model_name
                            })

                        except Exception as e:
                            st.error(f"处理流式响应时发生错误: {e}")

        # 显示当前会话的本地历史记录
        history_key = st.session_state.session_id
        if history_key in st.session_state.chat_history and st.session_state.chat_history[history_key]:
            st.subheader("💭 本地会话速记")
            # 只显示最近的5条
            for chat in reversed(st.session_state.chat_history[history_key][-5:]):
                with st.expander(f"({chat['timestamp']}) - {chat['user_message'][:30]}..."):
                    st.markdown(f"**👤 用户:**\n> {chat['user_message']}")
                    st.markdown(f"**🤖 AI ({chat['model_name']}):**\n> {chat['response']}")

    # 其他标签页 (tab3, tab4, tab5) 保持原样即可，它们的功能不受影响
    with tab3:
        st.header("📚 获取远端对话历史")
        if st.button("获取历史记录", key=f"get_history_{st.session_state.session_id}"):
            with st.spinner("正在从服务器获取历史..."):
                response = make_api_request(f"/qa/memory/{st.session_state.session_id}")
                display_json_response(response)

    with tab4:
        st.header("🗑️ 清除远端对话历史")
        st.warning("⚠️ 此操作将永久删除服务器上指定会话的所有对话历史记录。")
        if st.button("🗑️ 清除历史记录", key="clear_history_button", type="secondary"):
            with st.spinner(f"正在清除会话 {st.session_state.session_id} 的历史..."):
                response = make_api_request(f"/qa/memory/{st.session_state.session_id}", "DELETE")
                display_json_response(response)

    with tab5:
        st.header("📊 查看会话实例")
        if st.button("获取会话实例", key=f"get_instances_{st.session_state.session_id}"):
            with st.spinner("正在获取实例信息..."):
                response = make_api_request(f"/qa/session/{st.session_state.session_id}/instances")
                display_json_response(response)


if __name__ == "__main__":
    main()