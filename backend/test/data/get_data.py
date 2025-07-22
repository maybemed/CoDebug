import requests
import json

def call_travel_route_save_to_files(destination, budget, days, nodes_file, edges_file):
    # 定义 API URL
    api_url = "http://127.0.0.1:8000/api/graph/travel_route"  # 替换为实际的服务器地址

    # 构造请求体
    payload = {
        "destination": destination,
        "budget": budget,
        "days": days
    }

    try:
        # 发送 POST 请求
        response = requests.post(api_url, json=payload)

        # 检查请求是否成功
        if response.status_code == 200:
            # 解析响应数据
            response_data = response.json()
            nodes = response_data.get("nodes", [])
            edges = response_data.get("edges", [])

            # 保存 nodes 到文件
            with open(nodes_file, "w", encoding="utf-8") as f_nodes:
                json.dump(nodes, f_nodes, ensure_ascii=False, indent=4)

            # 保存 edges 到文件
            with open(edges_file, "w", encoding="utf-8") as f_edges:
                json.dump(edges, f_edges, ensure_ascii=False, indent=4)

            print(f"Nodes 已保存到 {nodes_file}")
            print(f"Edges 已保存到 {edges_file}")
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")

    except Exception as e:
        print(f"调用接口或保存文件时发生错误: {e}")

# 调用示例
call_travel_route_save_to_files(
    destination="Beijing",
    budget="5000",
    days="5",
    nodes_file="nodes.json",
    edges_file="edges.json"
)