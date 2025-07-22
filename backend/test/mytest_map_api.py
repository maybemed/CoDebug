import streamlit as st
import requests
import json

st.set_page_config(page_title="地图路线规划API测试", page_icon="🗺️", layout="wide")

if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8000"

if "waypoints" not in st.session_state:
    st.session_state.waypoints = []  # 存储所有途径点

if "waypoint_count" not in st.session_state:
    st.session_state.waypoint_count = 0

st.title("🗺️ 地图路线规划API测试")

st.subheader("输入信息")
city = st.text_input("城市", "北京市")
origin = st.text_input("起点", "天安门")
destination = st.text_input("终点", "北京南站")

st.markdown("---")

st.subheader("途径点设置")

# 动态生成途径点输入框
def render_waypoints():
    for i in range(st.session_state.waypoint_count):
        key = f"waypoint_{i+1}"
        if len(st.session_state.waypoints) <= i:
            st.session_state.waypoints.append("")
        st.session_state.waypoints[i] = st.text_input(f"途径点{i+1}", st.session_state.waypoints[i], key=key)

render_waypoints()

if st.button("增加途径点"):
    st.session_state.waypoint_count += 1
    st.rerun()

if st.button("清空所有途径点"):
    st.session_state.waypoints = []
    st.session_state.waypoint_count = 0
    st.rerun()

st.markdown("---")

if st.button("规划路线"):
    # 过滤空的途径点
    waypoints = [w for w in st.session_state.waypoints if w.strip()]
    waypoints_str = ",".join(waypoints) if waypoints else None
    req = {
        "city": city,
        "origin": origin,
        "destination": destination,
        "waypoints": waypoints_str
    }
    try:
        url = f"{st.session_state.api_base_url}/api/map/plan_route"
        resp = requests.post(url, json=req)
        resp.raise_for_status()
        data = resp.json()
        st.success("路线规划成功！")
        st.write("重要途径点经纬度：")
        st.json(data["points"])
    except Exception as e:
        st.error(f"路线规划失败: {e}") 