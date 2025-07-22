import requests
import json
import os
from typing import Dict, Any, Optional, List
from backend.config.settings import settings
from backend.utils.txt_tools import *


class DifyHighlightNodesClient:
    def __init__(self, base_url: str = "http://localhost/v1"):
        """
        初始化Dify客户端（支持文件上传）

        Args:
            base_url: Dify API的基础URL
            api_key: API密钥
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = settings.HIGHLIGHT_NODES_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.api_key}'
        }

    def upload_file(self, file_path: str, user: str = "maybemed") -> Dict[str, Any]:
        """
        上传文件到Dify服务器

        Args:
            file_path: 本地文件路径
            user: 用户标识

        Returns:
            上传结果，包含文件ID
        """
        upload_url = f"{self.base_url}/files/upload"

        try:
            # 准备文件上传
            with open(file_path, 'rb') as file:
                files = {
                    'file': (os.path.basename(file_path), file, self._get_content_type(file_path))
                }

                data = {
                    'user': user
                }

                # 发送上传请求
                response = requests.post(
                    upload_url,
                    headers=self.headers,
                    files=files,
                    data=data,
                    timeout=300
                )

                print(f"文件上传响应状态: {response.status_code}")

                # 修复：201和200都是成功状态
                if response.status_code not in [200, 201]:
                    return {
                        "error": f"文件上传失败: HTTP {response.status_code} - {response.text}",
                        "status_code": response.status_code
                    }

                result = response.json()
                print(f"文件上传成功，文件ID: {result.get('id', 'N/A')}")
                return result

        except FileNotFoundError:
            return {"error": f"文件未找到: {file_path}"}
        except Exception as e:
            return {"error": f"文件上传异常: {str(e)}"}

    def _get_content_type(self, file_path: str) -> str:
        """
        根据文件扩展名获取Content-Type

        Args:
            file_path: 文件路径

        Returns:
            Content-Type字符串
        """
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.csv': 'text/csv',
            '.html': 'text/html',
            '.json': 'application/json'
        }
        return content_types.get(ext, 'application/octet-stream')

    def create_file_input(self, file_path: str, user: str = "maybemed") -> Dict[str, Any]:
        """
        创建文件输入对象（上传文件并获取ID）

        Args:
            file_path: 文件路径
            user: 用户标识

        Returns:
            文件输入对象或错误信息
        """
        # 先上传文件
        upload_result = self.upload_file(file_path, user)

        if "error" in upload_result:
            return upload_result

        # 获取文件ID
        file_id = upload_result.get('id')
        if not file_id:
            return {"error": "上传成功但未获取到文件ID"}

        # 确定文件类型
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in ['.txt', '.md', '.pdf', '.docx', '.xlsx', '.csv', '.html']:
            file_type = "document"
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
            file_type = "image"
        elif file_ext in ['.mp3', '.m4a', '.wav', '.webm', '.amr']:
            file_type = "audio"
        elif file_ext in ['.mp4', '.mov', '.mpeg', '.mpga']:
            file_type = "video"
        else:
            file_type = "custom"

        # 返回文件输入对象
        return {
            "type": file_type,
            "transfer_method": "local_file",
            "upload_file_id": file_id
        }

    def run_workflow_with_uploaded_files(self,
                                         file1_path: str,
                                         file2_path: str,
                                         file1_param_name: str = "messages",
                                         file2_param_name: str = "nodes_list",
                                         user: str = "maybemed") -> Dict[str, Any]:
        """
        使用文件上传方式执行工作流

        Args:
            file1_path: 第一个文件路径
            file2_path: 第二个文件路径
            file1_param_name: 第一个文件参数名
            file2_param_name: 第二个文件参数名
            user: 用户标识
            additional_inputs: 额外输入参数

        Returns:
            工作流执行结果
        """
        try:
            print("正在上传文件...")

            # 创建文件输入对象
            file1_input = self.create_file_input(file1_path, user)
            if "error" in file1_input:
                return {"error": f"第一个文件处理失败: {file1_input['error']}"}

            file2_input = self.create_file_input(file2_path, user)
            if "error" in file2_input:
                return {"error": f"第二个文件处理失败: {file2_input['error']}"}

            # 构建输入参数
            inputs = {
                file1_param_name: file1_input,
                file2_param_name: file2_input
            }

            # # 添加额外输入参数
            # if additional_inputs:
            #     inputs.update(additional_inputs)

            # 构建请求数据
            payload = {
                "inputs": inputs,
                "response_mode": "blocking",
                "user": user
            }

            print(f"发送工作流请求...")
            print(f"文件1 ID: {file1_input['upload_file_id']}")
            print(f"文件2 ID: {file2_input['upload_file_id']}")
            print(f"输入参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            # 发送工作流请求
            response = requests.post(
                f"{self.base_url}/workflows/run",
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=300
            )

            print(f"工作流响应状态: {response.status_code}")

            if response.status_code != 200:
                print(f"工作流响应内容: {response.text}")
                return {
                    "error": f"工作流执行失败: HTTP {response.status_code} - {response.text}",
                    "status_code": response.status_code
                }

            # print(f"工作流执行成功，完整的响应内容: {response}")

            return response.json()

        except Exception as e:
            return {"error": f"执行异常: {str(e)}"}