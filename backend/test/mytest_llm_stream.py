import streamlit as st
import requests

st.title("LLM 流式对话测试")

user_message = st.text_input("请输入消息", value="测试")

if st.button("发送"):
    if not user_message.strip():
        st.warning("请输入消息内容")
    else:
        with st.spinner("等待流式回复..."):
            # 这里用 requests 的流式请求
            url = "http://127.0.0.1:8501/qa/chat"
            headers = {
                "Accept": "text/event-stream",
                "Content-Type": "application/json"
            }
            payload = {
                "user_message": user_message,
                "session_id": "streamlit_test_sess1",
            }

            response = requests.post(url, headers=headers, json=payload, stream=True)

            output_area = st.empty()
            collected_text = ""

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    # 形如 data: {"type": "content", "content": "..."}
                    if line.startswith("data:"):
                        data_str = line[len("data:"):].strip()
                        if data_str == '{"type": "end"}':
                            output_area.text_area("LLM回复结束", value=collected_text, height=300)
                            break
                        try:
                            import json
                            data_json = json.loads(data_str)
                            if data_json.get("type") == "content":
                                content = data_json.get("content", "")
                                collected_text += content
                                output_area.text_area("LLM回复（流式）", value=collected_text, height=300)
                        except json.JSONDecodeError:
                            # 忽略解析错误
                            pass
