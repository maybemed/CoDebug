# 处理edges
import json
import requests
from time import sleep
from itertools import combinations

import random
import re


def process_edges(names, edges, gaode_api_key, city):
    """
    处理edges数据，添加反转边、补充缺失的边，并调用高德地图API获取路径信息

    Args:
        names: list[str] - 景点名称列表
        edges: list[dict] - 现有的边数据
        gaode_api_key: str - 高德地图API密钥
        city: str - 城市名称

    Returns:
        list[dict] - 处理后的完整边数据
    """

    def extract_distance_km(distance_str):
        """从距离字符串中提取公里数"""
        match = re.search(r'(\d+(\.\d+)?)km', distance_str)
        if match:
            return float(match.group(1))
        return 0

    def minutes_to_time_format(minutes):
        """将分钟数转换为"h min"格式"""
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        if hours > 0:
            return f"{hours}h{mins}min"
        else:
            return f"{mins}min"

    def adjust_distance_and_time(distance, commuting_time):
        """调整距离和时间，如果距离超过1000km"""
        distance_km = extract_distance_km(distance)

        if distance_km > 1000:
            # 生成0-100之间的随机数
            new_distance_km = random.randint(0, 100)
            new_distance = f"{new_distance_km}km"

            # 计算新的通勤时间：distance/50 分钟
            new_commuting_minutes = new_distance_km / 50
            new_commuting_time = minutes_to_time_format(new_commuting_minutes)

            return new_distance, new_commuting_time
        else:
            return distance, commuting_time

    # 第1步：为现有edges添加反转边
    original_edges = edges.copy()
    # for edge in original_edges:
    #     # 对反转边也进行距离调整
    #     adjusted_distance, adjusted_time = adjust_distance_and_time(edge["distance"], edge["commuting_time"])
    #     reversed_edge = {
    #         "start_node": edge["end_node"],
    #         "end_node": edge["start_node"],
    #         "distance": adjusted_distance,
    #         "transport": edge["transport"],
    #         "commuting_time": adjusted_time
    #     }
    #     edges.append(reversed_edge)

    # 对原有edges也进行距离调整
    for edge in edges[:len(original_edges)]:
        edge["distance"], edge["commuting_time"] = adjust_distance_and_time(edge["distance"], edge["commuting_time"])

    # 第2步：为所有对象添加show字段
    for edge in edges:
        edge["show"] = "true"

    # 第3步：创建现有边的映射，用于快速查找和更新
    existing_edges_map = {}
    for i, edge in enumerate(edges):
        existing_edges_map[(edge["start_node"], edge["end_node"])] = i

    # 第4步：遍历所有景点的两两组合，添加缺失的边或更新现有边
    for i, name1 in enumerate(names):
        for j, name2 in enumerate(names):
            if j > i:  # 保证没有反转边，也不包括自己到自己的边
                if (name1, name2) not in existing_edges_map:
                    # 调用高德地图API获取路径信息
                    distance, transport, commuting_time = get_route_info(name1, name2, gaode_api_key, city)

                    # 调整距离和时间
                    distance, commuting_time = adjust_distance_and_time(distance, commuting_time)

                    # 添加新边
                    new_edge = {
                        "start_node": name1,
                        "end_node": name2,
                        "distance": distance,
                        "transport": transport,
                        "commuting_time": commuting_time,
                        "show": "false"
                    }
                    edges.append(new_edge)
                    existing_edges_map[(name1, name2)] = len(edges) - 1
                else:
                    # 边已存在，使用get_route_info获取信息并更新现有边
                    distance, transport, commuting_time = get_route_info(name1, name2, gaode_api_key, city)

                    # 调整距离和时间
                    distance, commuting_time = adjust_distance_and_time(distance, commuting_time)

                    # 更新现有边的信息
                    edge_index = existing_edges_map[(name1, name2)]
                    edges[edge_index]["distance"] = distance
                    edges[edge_index]["transport"] = transport
                    edges[edge_index]["commuting_time"] = commuting_time

    return edges


def get_route_info(start_location, end_location, api_key,city):
    """
    调用高德地图API获取两点间的路径信息

    Args:
        start_location: str - 起点名称
        end_location: str - 终点名称
        api_key: str - 高德地图API密钥

    Returns:
        tuple: (distance, transport, commuting_time)
    """
    try:
        sleep(0.1)
        # 第一步：获取起点和终点的坐标
        start_coords = get_coordinates(start_location, api_key,city)
        end_coords = get_coordinates(end_location, api_key,city)

        if not start_coords or not end_coords:
            return "", "", ""

        # 第二步：调用路径规划API（这里使用驾车路径规划）
        url = "https://restapi.amap.com/v5/direction/driving"
        params = {
            "origin": start_coords,
            "destination": end_coords,
            "key": api_key,
            "show_fields": ["cost"],
            "output": "json"
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") == "1" and data.get("route"):
            route = data["route"]["paths"][0]

            # 距离（转换为km）
            distance_m = int(route["distance"])
            distance = f"{distance_m / 1000:.1f}km"

            # 时间（转换为秒）
            duration_s = int(route['cost']["duration"])


            # 交通方式（这里默认为驾车，你可以根据距离调整）
            if distance_m < 2000:
                transport = "步行"
                duration_s*=2
            elif distance_m < 50000:
                transport = "打车"
            else:
                transport = "公共交通"

            # 时间（转换为小时分钟格式）
            hours = duration_s // 3600
            minutes = (duration_s % 3600) // 60

            if hours > 0:
                commuting_time = f"{hours}h{minutes}min"
            else:
                commuting_time = f"{minutes}min"



            return distance, transport, commuting_time

    except Exception as e:
        print(f"获取路径信息失败: {start_location} -> {end_location}, 错误: {e}")

    return "", "", ""


def get_coordinates(location_name, api_key,city):
    """
    通过地名获取坐标

    Args:
        location_name: str - 地点名称
        api_key: str - 高德地图API密钥

    Returns:
        str: 坐标字符串 "经度,纬度"
    """
    try:
        location_name = city+location_name
        url = "https://restapi.amap.com/v3/geocode/geo"
        params = {
            "address": location_name,
            "key": api_key,
            "output": "json"
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") == "1" and data.get("geocodes"):
            location = data["geocodes"][0]["location"]
            return location

    except Exception as e:
        print(f"获取坐标失败: {location_name}, 错误: {e}")

    return None


def validate_nodes(nodes):
    """
    验证并清理nodes数组，删除不符合格式要求的数据

    Args:
        nodes: list[dict] - 原始的nodes数组

    Returns:
        list[dict] - 清理后符合格式要求的nodes数组
    """

    def validate_node(node):
        """验证单个node是否符合格式要求"""
        if not isinstance(node, dict):
            return False

        # 检查必需字段是否存在且为字符串类型
        required_string_fields = ['node_name', 'price', 'play_time']
        for field in required_string_fields:
            if field not in node or not isinstance(node[field], str):
                return False

        # 检查attractions字段是否存在且为数组类型
        if 'attractions' not in node or not isinstance(node['attractions'], list):
            return False

        return True

    def validate_attraction(attraction):
        """验证attraction对象的格式（可选的额外验证）"""
        if not isinstance(attraction, dict):
            return False

        # 如果attraction存在，建议也验证其字段格式
        expected_fields = ['item_name', 'item_price', 'item_play_time']
        for field in expected_fields:
            if field in attraction and not isinstance(attraction[field], str):
                return False

        return True

    def clean_node(node):
        """清理单个node，移除格式不正确的attractions"""
        cleaned_node = node.copy()

        # 清理attractions数组，移除格式不正确的元素
        if 'attractions' in cleaned_node and isinstance(cleaned_node['attractions'], list):
            cleaned_attractions = []
            for attraction in cleaned_node['attractions']:
                if validate_attraction(attraction):
                    cleaned_attractions.append(attraction)
            cleaned_node['attractions'] = cleaned_attractions

        return cleaned_node

    # 主验证逻辑
    if not isinstance(nodes, list):
        return []

    validated_nodes = []

    for node in nodes:
        if validate_node(node):
            # 如果node格式正确，进一步清理其attractions
            cleaned_node = clean_node(node)
            validated_nodes.append(cleaned_node)
        # 如果node格式不正确，直接跳过（删除）

    return validated_nodes