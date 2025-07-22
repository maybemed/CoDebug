from fastapi import APIRouter, HTTPException
import json
import requests
from pathlib import Path
from pydantic import BaseModel
from itertools import combinations
import os

from backend.core.agent.agent_graph_and_edges import run_dify_workflow_blocking
from backend.utils.graph_data_func import process_edges,validate_nodes
from backend.config.settings import settings

router = APIRouter()

class TravelRequest(BaseModel):
    destination: str
    budget: str
    days: str


@router.post("/travel_route")
async def generate_travel_route(request: TravelRequest):
    # """
    # 生成旅行路线的节点和边数据
    #
    # Args:
    #     request: TravelRequest - 包含destination, budget, days的请求体
    #
    # Returns:
    #     dict: 包含nodes和edges的响应数据
    # """
    # try:
    #     # 构造发送给Dify的输入
    #     user_input = {
    #         "destination": request.destination,
    #         "budget": request.budget,
    #         "days": request.days
    #     }
    #
    #     # 使用当前用户ID作为会话标识
    #     user_id = "001"
    #
    #     # 调用Dify工作流获取初始数据
    #     print("开始获取旅行路线数据...")
    #     nodes, edges = run_dify_workflow_blocking(user_input, user_id)
    #     nodes = json.loads(nodes) if isinstance(nodes, str) else nodes
    #     edges = json.loads(edges) if isinstance(edges, str) else edges
    #     print(f"获取到的节点: {nodes}")
    #     print(f"获取到的边: {edges}")
    #     if nodes is None or edges is None:
    #         raise HTTPException(status_code=500, detail="Faile`d to get data from Dify workflow")
    #
    #     # 从nodes中提取景点名称列表
    #     names = []
    #     if nodes:
    #         # 假设nodes中包含景点信息，提取名称
    #         for node in nodes:
    #             if isinstance(node, dict) and "node_name" in node:
    #                 names.append(node["node_name"])
    #             elif isinstance(node, str):
    #                 names.append(node)
    #
    #     # 如果edges为空，初始化为空列表
    #     if edges is None:
    #         edges = []
    #
    #     # 处理edges数据
    #     processed_edges = process_edges(names, edges, settings.GAODE_API_KEY,city=request.destination)
    #     nodes = validate_nodes(nodes)
    #
    #     return {
    #         "nodes": nodes,
    #         "edges": processed_edges,
    #         "message": "Travel route generated successfully"
    #     }
    #
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     print(f"生成旅行路线时发生错误: {e}")
    #     raise HTTPException(status_code=500, detail=f"Failed to generate travel route: {str(e)}")

    import json
    with open(r"E:\WorkStation\LLMProject\v3.6\backend\test\data\nodes.json",'r',encoding='utf-8') as f1:
        with open(r"E:\WorkStation\LLMProject\v3.6\backend\test\data\edges.json",'r',encoding='utf-8') as f2:
            nodes=json.load(f1)
            edges=json.load(f2)
        return {
            "nodes":nodes,
            "edges":edges,
            "message": "Travel route generated successfully"
        }


# @router.get("/")
# async def get_travel_info():
#     """获取旅行路线API信息"""
#     return {
#         "message": "Travel Route API",
#         "version": "travel_route_api",
#         "endpoints": {
#             "POST /travel-route": "Generate travel route with nodes and edges"
#         }
#     }