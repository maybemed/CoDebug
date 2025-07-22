from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.core.llm.llm_manager import LLMManager
from backend.utils.logger import logger
from fastapi import Response
from fastapi.responses import StreamingResponse, JSONResponse
import json
import logging

router = APIRouter()


class ModelInfo(BaseModel):
    model_name: str
    description: str
    provider: str


class ModelsResponse(BaseModel):
    models: List[ModelInfo]


class ChatRequest(BaseModel):
    user_message: str
    session_id: str
    model_name: Optional[str] = "deepseek-chat"
    system_prompt_name: Optional[str] = "default"
    temperature: Optional[float] = 0.7
    max_messages: Optional[int] = 50
    max_tokens: Optional[int] = 4000
    # history_file_path: Optional[str] = None  # 移除


class ChatResponse(BaseModel):
    response_message: str
    model_name: str
    status: str
    previous_model: Optional[str] = None  # *新 如果发生了模型切换，记录前一个模型
    model_switched: bool = False  # *新 标记是否发生了模型切换
    error: Optional[str] = None


class HistoryMessage(BaseModel):
    role: str
    content: str


class HistoryResponse(BaseModel):
    status: str
    messages: Optional[List[HistoryMessage]] = None
    current_model: Optional[str] = None  # *新 当前使用的模型
    error: Optional[str] = None


class DeleteHistoryResponse(BaseModel):
    status: str
    message: Optional[str] = None
    error: Optional[str] = None


class ModelSwitchRequest(BaseModel):
    session_id: str
    new_model_name: str
    temperature: Optional[float] = 0.7
    transfer_memory: bool = True  # 是否转移记忆，默认为True


class ModelSwitchResponse(BaseModel):
    status: str
    message: Optional[str] = None
    previous_model: Optional[str] = None
    new_model: Optional[str] = None
    memory_transferred: bool = False
    error: Optional[str] = None


@router.get("/models", response_model=ModelsResponse)
async def get_available_models():
    """获取所有可用的LLM模型"""
    try:
        available_models = LLMManager.get_available_models()

        models = []
        for model_name, config in available_models.items():
            # 生成模型描述
            provider = config.get("provider", "Unknown")
            description = f"{provider} 提供的 {model_name} 模型"

            # 为不同提供商添加特定描述
            if provider == "GPT":
                description = f"OpenAI {model_name}，擅长复杂推理和多模态任务"
            elif provider == "DeepSeek":
                description = f"DeepSeek {model_name}，擅长多轮对话和复杂推理"
            elif provider == "Zhipu":
                description = f"智谱AI {model_name}，擅长中文理解和生成"
            elif provider == "Qwen":
                description = f"通义千问 {model_name}，阿里云大语言模型"
            elif provider == "Spark":
                description = f"讯飞星火 {model_name}，擅长中文对话和理解"

            models.append(ModelInfo(
                model_name=model_name,
                description=description,
                provider=provider
            ))

        return ModelsResponse(models=models)

    except Exception as e:
        logger.error(f"获取可用模型失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available models")

@router.post("/qa/chat")
async def chat_with_llm(request: ChatRequest):
    from backend.config.settings import settings
    async def event_generator():
        try:
            # 验证模型是否可用
            available_models = LLMManager.get_available_models()
            if request.model_name not in available_models:
                yield f"data: {json.dumps({'error': f'Invalid model_name: {request.model_name or 'None'}'})}\n\n"
                return

            # 构造目标实例ID
            target_instance_id = _create_instance_id(request.session_id, request.model_name)

            # 获取当前活跃的实例
            current_active_instance_id = _get_active_instance_for_session(request.session_id)
            current_instance = LLMManager.get_instance(current_active_instance_id) if current_active_instance_id else None

            # 发送开始标记
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            if current_instance and current_instance.model_name != request.model_name:
                # 发送模型切换通知
                previous_model = current_instance.model_name
                yield f"data: {json.dumps({'type': 'model_switch', 'from': previous_model, 'to': request.model_name})}\n\n"

                target_instance = LLMManager.get_instance(target_instance_id)
                if not target_instance:
                    target_instance = LLMManager.create_instance(
                        instance_id=target_instance_id,
                        model_name=request.model_name,
                        temperature=request.temperature if request.temperature is not None else 0.7,
                        max_messages=request.max_messages if request.max_messages is not None else 50,
                        max_tokens=request.max_tokens if request.max_tokens is not None else 4000
                    )
                if current_instance:
                    target_instance.copy_memory_from(current_instance)

                try:
                    async for chunk in target_instance.chat_stream(
                        request.user_message,
                        request.system_prompt_name or "default"
                    ):
                        if chunk and isinstance(chunk, str):
                            # 打印调试，确认chunk类型和值
                            logging.debug(f"chunk (type={type(chunk)}): {repr(chunk)}")
                            data_json = json.dumps({"type": "content", "content": chunk})
                            yield f"data: {data_json}\n\n"
                except Exception as e:
                    logging.error(f"流式对话出错: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

            else:
                try:
                    async for chunk in LLMManager.quick_chat_stream(
                        instance_id=target_instance_id,
                        user_message=request.user_message,
                        model_name=request.model_name,
                        system_prompt_name=request.system_prompt_name or "default",
                        create_if_not_exists=True
                    ):
                        if chunk and isinstance(chunk, str):
                            logging.debug(f"quick chunk (type={type(chunk)}): {repr(chunk)}")
                            data_json = json.dumps({"type": "content", "content": chunk})
                            yield f"data: {data_json}\n\n"
                except Exception as e:
                    logging.error(f"快速流式对话出错: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

            yield f"data: {json.dumps({'type': 'end'})}\n\n"

            # 在对话结束后保存所有会话历史到json
            LLMManager.save_all_sessions_to_json()

        except Exception as e:
            logging.error(f"LLM对话失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream; charset=utf-8",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
    )

@router.get("/qa/memory/{session_id}", response_model=HistoryResponse)
async def get_conversation_history(session_id: str = Path(..., description="会话ID")):
    """获取指定会话的对话历史"""
    try:
        # 获取当前活跃的实例
        current_active_instance_id = _get_active_instance_for_session(session_id)
        current_instance = LLMManager.get_instance(current_active_instance_id) if current_active_instance_id else None

        if not current_instance:
            return HistoryResponse(
                status="success",
                messages=[],
                current_model=None
            )

        # 获取对话历史
        history = current_instance.get_conversation_history()

        # 转换为前端格式
        messages = []
        for msg in history:
            if hasattr(msg, 'type'):
                if msg.type == "human":
                    messages.append(HistoryMessage(role="user", content=msg.content))
                elif msg.type == "ai":
                    messages.append(HistoryMessage(role="assistant", content=msg.content))
                # 跳过系统消息

        return HistoryResponse(
            status="success",
            messages=messages,
            current_model=current_instance.model_name
        )

    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        return HistoryResponse(
            status="fail",
            error=f"Failed to get history from LLM: {str(e)}"
        )


@router.delete("/qa/memory/{session_id}", response_model=DeleteHistoryResponse)
async def clear_conversation_history(session_id: str = Path(..., description="会话ID")):
    """清除指定会话的对话历史"""
    try:
        # 查找该会话相关的所有实例
        all_instances = LLMManager.list_instances()

        # 寻找匹配的实例（以session_id开头的实例）
        matching_instances = [
            instance_id for instance_id in all_instances.keys()
            if instance_id.startswith(f"{session_id}_")
        ]

        cleared_count = 0
        for instance_id in matching_instances:
            instance = LLMManager.get_instance(instance_id)
            if instance:
                instance.clear_conversation()
                cleared_count += 1

        return DeleteHistoryResponse(
            status="success",
            message=f"对话历史已清除，共清除 {cleared_count} 个实例的历史记录"
        )

    except Exception as e:
        logger.error(f"清除对话历史失败: {e}")
        return DeleteHistoryResponse(
            status="fail",
            error=f"Failed to delete history from LLM: {str(e)}"
        )


@router.get("/qa/session/{session_id}/instances")
async def get_session_instances(session_id: str = Path(..., description="会话ID")):
    """获取指定会话的所有实例信息"""
    try:
        all_instances = LLMManager.list_instances()

        # 查找该会话相关的所有实例
        session_instances = {}
        for instance_id, instance_info in all_instances.items():
            if instance_id.startswith(f"{session_id}_"):
                session_instances[instance_id] = instance_info

        # 找到当前活跃的实例
        current_active_instance_id = _get_active_instance_for_session(session_id)

        return {
            "status": "success",
            "session_id": session_id,
            "instances": session_instances,
            "active_instance": current_active_instance_id,
            "total_instances": len(session_instances)
        }

    except Exception as e:
        logger.error(f"获取会话实例失败: {e}")
        return {
            "status": "error",
            "error": f"Failed to get session instances: {str(e)}"
        }


@router.get("/qa/chat-history")
async def get_chat_history():
    """获取 chat_history.json 的全部内容"""
    try:
        with open("chat_history.json", "r", encoding="utf-8") as f:
            data = f.read()
        # 直接返回原始内容（字符串），如果需要解析为json对象可用 json.loads(data)
        return Response(content=data, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error(f"读取 chat_history.json 失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to read chat_history.json")


def _get_active_instance_for_session(session_id: str) -> Optional[str]:
    """
    获取会话的活跃实例ID
    会话可能有多个不同模型的实例，我们需要找到最近使用的那个
    """
    all_instances = LLMManager.list_instances()

    # 查找该会话相关的所有实例
    matching_instances = []
    for instance_id, instance_info in all_instances.items():
        if instance_id.startswith(f"{session_id}_"):
            matching_instances.append((instance_id, instance_info["updated_at"]))

    if not matching_instances:
        return None

    # 按照更新时间排序，返回最近使用的实例
    matching_instances.sort(key=lambda x: x[1], reverse=True)
    return matching_instances[0][0]


def _create_instance_id(session_id: str, model_name: str) -> str:
    """创建实例ID"""
    return f"{session_id}_{model_name}"


'''
@router.post("/qa/switch-model", response_model=ModelSwitchResponse)
async def switch_model_in_session(request: ModelSwitchRequest):
    """在会话中切换模型，可选择是否转移记忆"""
    try:
        # 验证新模型是否可用
        available_models = LLMManager.get_available_models()
        if request.new_model_name not in available_models:
            return ModelSwitchResponse(
                status="error",
                error=f"Invalid model_name: {request.new_model_name}"
            )

        # 获取当前活跃的实例
        current_active_instance_id = _get_active_instance_for_session(request.session_id)
        current_instance = LLMManager.get_instance(current_active_instance_id) if current_active_instance_id else None

        if not current_instance:
            return ModelSwitchResponse(
                status="error",
                error=f"No active instance found for session: {request.session_id}"
            )

        previous_model = current_instance.model_name

        # 如果已经是目标模型，无需切换
        if current_instance.model_name == request.new_model_name:
            return ModelSwitchResponse(
                status="success",
                message="Already using the requested model",
                previous_model=previous_model,
                new_model=request.new_model_name,
                memory_transferred=False
            )

        # 构造新实例ID
        new_instance_id = _create_instance_id(request.session_id, request.new_model_name)

        # 获取或创建新实例
        new_instance = LLMManager.get_instance(new_instance_id)
        if not new_instance:
            new_instance = LLMManager.create_instance(
                instance_id=new_instance_id,
                model_name=request.new_model_name,
                temperature=request.temperature,
                max_messages=current_instance.max_messages,
                max_tokens=current_instance.max_tokens
            )

        # 转移记忆（如果需要）
        memory_transferred = False
        if request.transfer_memory:
            new_instance.copy_memory_from(current_instance)
            memory_transferred = True
            logger.info(f"已将记忆从 {current_active_instance_id} 转移到 {new_instance_id}")

        return ModelSwitchResponse(
            status="success",
            message=f"Successfully switched from {previous_model} to {request.new_model_name}",
            previous_model=previous_model,
            new_model=request.new_model_name,
            memory_transferred=memory_transferred
        )

    except Exception as e:
        logger.error(f"模型切换失败: {e}")
        return ModelSwitchResponse(
            status="error",
            error=f"Failed to switch model: {str(e)}"
        )
'''

