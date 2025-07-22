# from typing import Dict,Any
#
# from backend.config.settings import settings
# import requests
#
# def upload_file():
#
#
# def call_workflow_with_files_upload(api_key: str,
#                                     api_url :str,
#                                     file1_path: str,
#                                     file2_path: str,
#                                     user_id: str = "default_user") -> Dict[str, Any]:
#     """
#     通过文件上传方式调用工作流（如果API支持文件上传）
#
#     Args:
#         file1_path: 第一个txt文件路径
#         file2_path: 第二个txt文件路径
#         user_id: 用户ID
#
#     Returns:
#         API响应结果
#     """
#     try:
#         # 准备文件上传
#         files = {
#             'file1': open(file1_path, 'rb'),
#             'file2': open(file2_path, 'rb')
#         }
#
#         inputs=[
#             {
#                 'type':'TXT',
#                 'transfer_method':'local_file',
#                 'upload_file_id': 'file1',
#             }
#         ]
#
#         data = {
#             'user': user_id,
#             'response_mode': 'blocking',
#             "inputs":inputs
#             # 'transfer_method':'local_file',
#         }
#
#         # 修改headers，移除Content-Type让requests自动设置
#         upload_headers = {
#             'Authorization': f'Bearer {api_key}'
#         }
#
#         response = requests.post(
#             f"{api_url}/workflows/run",
#             headers=upload_headers,
#             files=files,
#             data=data,
#             timeout=300
#         )
#
#         response.raise_for_status()
#         return response.json()
#
#     except Exception as e:
#         return {"error": f"文件上传失败: {str(e)}"}
#     finally:
#         # 确保文件被关闭
#         for file in files.values():
#             if hasattr(file, 'close'):
#                 file.close()
#
# if __name__ == '__main__':
#     api_key="app-XZ4MGxMhsWHGYNNVADmSdWTO"
#     api_url = "http://localhost/v1"
#     file1_path = "test_messages.txt"
#     file2_path = "test_nodes_list.txt"
#     resp = call_workflow_with_files_upload(api_key, api_url, file1_path, file2_path)
#     print(resp)


import requests
import json
import os
from typing import Dict, Any, Optional, List


class DifyFileUploadClient:
    def __init__(self, base_url: str = "http://localhost/v1", api_key: str = ""):
        """
        初始化Dify客户端（支持文件上传）

        Args:
            base_url: Dify API的基础URL
            api_key: API密钥
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}'
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
                                         file1_param_name: str = "file1",
                                         file2_param_name: str = "file2",
                                         user: str = "maybemed",
                                         additional_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
                file1_param_name: file1_input,  # 注意：文件类型需要是列表
                file2_param_name: file2_input
            }

            # 添加额外输入参数
            if additional_inputs:
                inputs.update(additional_inputs)

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

            return response.json()

        except Exception as e:
            return {"error": f"执行异常: {str(e)}"}

def main():
    """
    使用示例
    """
    # 配置信息
    API_KEY = "app-XZ4MGxMhsWHGYNNVADmSdWTO"  # 替换为你的API密钥
    BASE_URL = "http://localhost/v1"

    # 文件路径
    FILE1_PATH = "test_messages.txt"  # 根据你的实际文件路径修改
    FILE2_PATH = "test_nodes_list.txt"  # 根据你的实际文件路径修改

    # 创建客户端
    client = DifyFileUploadClient(BASE_URL, API_KEY)

    print("=== 测试文件上传修复版 ===")

    # 测试单独上传文件
    upload_result1 = client.upload_file(FILE1_PATH)
    if "error" not in upload_result1:
        print(f"✅ 文件1上传成功，ID: {upload_result1.get('id')}")
        print(f"文件信息: {json.dumps(upload_result1, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 文件1上传失败: {upload_result1['error']}")
        return

    upload_result2 = client.upload_file(FILE2_PATH)
    if "error" not in upload_result2:
        print(f"✅ 文件2上传成功，ID: {upload_result2.get('id')}")
        print(f"文件信息: {json.dumps(upload_result2, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 文件2上传失败: {upload_result2['error']}")
        return

    print("\n=== 执行工作流 ===")

    # 使用简化版自动尝试不同参数
    result = client.run_workflow_simple(FILE1_PATH, FILE2_PATH, "maybemed")

    # 处理结果
    if "error" in result:
        print(f"❌ 最终执行失败: {result['error']}")
    else:
        print("✅ 执行成功!")

        # 提取输出结果
        if "data" in result and "outputs" in result["data"]:
            outputs = result["data"]["outputs"]
            print(f"输出结果: {outputs}")

            # 保存结果到文件
            with open("result.json", "w", encoding="utf-8") as f:
                json.dump(outputs, f, indent=2, ensure_ascii=False)
            print("结果已保存到 result.json")

        # 显示执行信息
        data = result.get("data", {})
        print(f"执行状态: {data.get('status')}")
        print(f"执行时间: {data.get('elapsed_time')}秒")
        print(f"使用Token: {data.get('total_tokens')}")


if __name__ == "__main__":
    # 配置信息
    API_KEY = "app-XZ4MGxMhsWHGYNNVADmSdWTO"  # 替换为你的API密钥
    BASE_URL = "http://localhost/v1"

    # 文件路径
    FILE1_PATH = "test_messages.txt"  # 根据你的实际文件路径修改
    FILE2_PATH = "test_nodes_list.txt"  # 根据你的实际文件路径修改

    # 创建客户端
    client = DifyFileUploadClient(BASE_URL, API_KEY)

    resp=client.run_workflow_with_uploaded_files(FILE1_PATH, FILE2_PATH, "messages", "nodes_list", "maybemed")
    print(resp)