# @user: maybemed
# @last_update: 2025-07-18 08:44:23 UTC
# @version: dify_workflow_client

import requests
import ast
import logging
from backend.utils.graph_data_func import *
from backend.config.settings import settings

# 设置日志
logger = logging.getLogger(__name__)


def extract_nodes_and_edges_safe(response_data):
    """
    安全地从响应数据中提取 nodes 和 edges

    Args:
        response_data: API 响应数据

    Returns:
        tuple: (nodes, edges)
    """
    try:
        # 如果响应是字符串形式的 Python 字典
        if isinstance(response_data, str):
            logger.info("响应是字符串格式，尝试解析")
            response_data = ast.literal_eval(response_data)
        print("extract_nodes_and_edges_safe中解析后的 response_data:\n", response_data)

        # 多种可能的数据结构
        possible_paths = [
            ['data', 'outputs'],
            ['outputs'],
            []  # 直接在根级别
        ]

        for path in possible_paths:
            current_data = response_data
            try:
                # 遍历路径
                for key in path:
                    current_data = current_data[key]

                # 尝试提取 nodes 和 edges
                if 'nodes' in current_data and 'edges' in current_data:
                    nodes = current_data['nodes']
                    edges = current_data['edges']
                    logger.info(f"从路径 {' -> '.join(path) if path else 'root'} 成功提取数据")
                    return nodes if nodes is not None else [], edges if edges is not None else []

            except (KeyError, TypeError):
                continue

        # 如果所有路径都失败了
        logger.warning("无法从任何已知路径提取 nodes 和 edges")
        return [], []

    except Exception as e:
        logger.error(f"提取数据时发生错误: {e}")
        return [], []


def validate_nodes_and_edges(nodes, edges):
    """
    验证 nodes 和 edges 数据的有效性

    Args:
        nodes: 节点数据列表
        edges: 边数据列表

    Returns:
        tuple: (validated_nodes, validated_edges)
    """
    validated_nodes = []
    validated_edges = []

    # 验证 nodes
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict):
                # 确保节点有必要的字段
                if 'node_name' in node:
                    validated_nodes.append(node)
                else:
                    logger.warning(f"节点缺少 node_name 字段: {node}")
            else:
                logger.warning(f"无效的节点格式: {node}")

    # 验证 edges
    if isinstance(edges, list):
        for edge in edges:
            if isinstance(edge, dict):
                # 确保边有必要的字段
                if 'start_node' in edge and 'end_node' in edge:
                    validated_edges.append(edge)
                else:
                    logger.warning(f"边缺少必要字段: {edge}")
            else:
                logger.warning(f"无效的边格式: {edge}")

    logger.info(f"验证完成 - 有效节点: {len(validated_nodes)}, 有效边: {len(validated_edges)}")
    return validated_nodes, validated_edges


def run_dify_workflow_blocking(user_input, user_id):
    """
    以阻塞方式调用 Dify 工作流，并获取最终结果。

    Args:
        user_input (dict): 要发送给工作流的输入内容。
        user_id (str): 用户的唯一标识符，用于保持会话连续性。

    Returns:
        tuple: (nodes, edges) 如果成功，否则返回 (None, None)。
    """

    # --- 1. 构造请求头和请求体 ---
    headers = {
        "Authorization": f"Bearer {settings.NODES_AND_EDGES_API_KEY}",
        "Content-Type": "application/json"
    }

    # 'inputs' 中的键必须与您工作流"开始"节点中定义的变量名完全一致
    # 'user' 是必须的，用于 Dify 后台跟踪和记录对话
    data = {
        "inputs": user_input,
        "response_mode": "blocking",
        "user": user_id
    }

    try:
        # --- 2. 发送 POST 请求 ---
        logger.info(f"正在调用 Dify API，用户输入: {user_input}")
        response = requests.post(settings.GET_NODES_AND_EDGES_AGENTS_URL, headers=headers, json=data)

        # 检查请求是否成功
        response.raise_for_status()

        # --- 3. 获取并解析响应 ---
        result = response.json()
        logger.info(f"获取到的原始响应类型: {type(result)}")
        print("获取到的原始响应内容:\n", result)

        # 使用安全提取函数
        nodes, edges = extract_nodes_and_edges_safe(result)

        # 使用验证函数
        validated_nodes, validated_edges = validate_nodes_and_edges(nodes, edges)

        return validated_nodes, validated_edges

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP 错误: {e}")
        logger.error(f"响应状态码: {response.status_code}")
        try:
            logger.error(f"错误响应内容: {response.text}")
        except:
            pass
        return None, None
    except requests.exceptions.RequestException as e:
        logger.error(f"请求 Dify API 时发生错误: {e}")
        return None, None
    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        return None, None