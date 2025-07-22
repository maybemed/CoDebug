from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import tempfile
import os
from pathlib import Path
import httpx

# 导入你的工具函数和客户端类
from backend.utils.txt_tools import node_json2name_list, history2txt, name_list2txt
from backend.core.agent.agent_highlight_nodes import DifyHighlightNodesClient
from backend.config.settings import settings

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class AttractionItem(BaseModel):
    item_name: str
    item_price: str
    item_play_time: str


class Node(BaseModel):
    node_name: str
    price: str
    play_time: str
    attractions: List[AttractionItem] = []


class HighlightNodesRequest(BaseModel):
    session_id: str
    nodes: List[Node]


class HighlightNodesResponse(BaseModel):
    highlight_nodes: List[str]


async def get_chat_history_from_api() -> Dict[str, List[Dict[str, str]]]:
    """
    从配置的API路径获取聊天历史

    Returns:
        聊天历史字典，格式与原来的chat_history相同
    """
    chat_history_url = f"{settings.BACKEND_RUN_URL}/api/llm/qa/chat-history"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(chat_history_url)

            if response.status_code == 200:
                chat_history = response.json()
                return chat_history
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"获取聊天历史失败，状态码: {response.status_code}, 响应: {response.text}"
                )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"请求聊天历史API失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取聊天历史时发生未知错误: {str(e)}"
        )


@router.post("/get_highlight_nodes", response_model=HighlightNodesResponse)
async def get_highlight_nodes(request: HighlightNodesRequest):
    """
    根据用户聊天记录获取用户有意向前往的景点名

    Args:
        request: 包含会话ID和景点节点数据的请求体

    Returns:
        用户有意向前往的景点名列表
    """

    # 创建临时目录用于存储文件
    print("开始执行接口函数000！")
    temp_dir = "temp_data"

    try:
        print("开始执行接口函数！")

        # 1. 从API获取聊天历史
        print("正在获取聊天历史...")
        chat_history = await get_chat_history_from_api()
        print(f"成功获取聊天历史，包含 {len(chat_history)} 个会话")

        # 2. 准备文件路径
        chat_history_path = r"E:\WorkStation\LLMProject\v3.6\backend\api\routers\temp_data\chat_history.json"
        user_messages_path = r"E:\WorkStation\LLMProject\v3.6\backend\api\routers\temp_data\user_messages.txt"
        nodes_list_path = r"E:\WorkStation\LLMProject\v3.6\backend\api\routers\temp_data\nodes_list.txt"

        # 3. 保存聊天历史到临时文件
        with open(chat_history_path, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)

        # 4. 提取指定session的用户消息
        history2txt(chat_history_path, user_messages_path, request.session_id)

        # 5. 提取景点名列表并保存到文件
        node_names = [node.node_name for node in request.nodes]
        name_list2txt(node_names, nodes_list_path)

        # 6. 检查文件是否存在且有内容
        print("111111")
        if not os.path.exists(user_messages_path) or os.path.getsize(user_messages_path) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"指定的会话ID '{request.session_id}' 中没有用户消息"
            )

        if not os.path.exists(nodes_list_path) or os.path.getsize(nodes_list_path) == 0:
            raise HTTPException(
                status_code=400,
                detail="景点节点数据为空"
            )

        # 7. 使用Dify客户端处理文件
        dify_client = DifyHighlightNodesClient()
        print("222222")
        with open(user_messages_path, 'r', encoding='utf-8') as f1:
            with open(nodes_list_path, 'r', encoding='utf-8') as f2:
                content1 = f1.read()
                content2 = f2.read()
                print(f"传送给dify的请求为：\n {content1} \n *** \n {content2}")
        print("33333")

        # 8. 调用工作流
        result = dify_client.run_workflow_with_uploaded_files(
            file1_path=user_messages_path,
            file2_path=nodes_list_path,
            file1_param_name="messages",  # 根据你的工作流配置调整
            file2_param_name="nodes_list",  # 根据你的工作流配置调整
            user="maybemed"
        )

        # 9. 处理返回结果
        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=f"工作流执行失败: {result['error']}"
            )

        # 10. 提取输出结果
        print(f"原始输出为：{result}")
        outputs = result.get("data", {}).get("outputs", {})

        # 根据实际的输出格式调整这里的键名
        highlight_nodes_raw = outputs.get("target_nodes", "")

        # 11. 过滤结果，确保返回的景点名在原始节点列表中
        valid_highlight_nodes = [
            node for node in highlight_nodes_raw
            if node in node_names
        ]

        return HighlightNodesResponse(highlight_nodes=valid_highlight_nodes)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理请求时发生错误: {str(e)}"
        )