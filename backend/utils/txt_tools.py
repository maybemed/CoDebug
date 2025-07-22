import json
from typing import List


def node_json2name_list(json_path: str) -> List[str]:
    """
    读取前端传来的 nodes.json 文件，返回所有 node_name（景点名）组成的列表。
    :param json_path: nodes.json 文件路径
    :return: node_name 列表
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        nodes = json.load(f)
    return [node.get('node_name', '') for node in nodes if 'node_name' in node]


def history2txt(history_json_path: str, txt_path: str, session_id: str) -> None:
    """
    读取保存聊天记录的json文件，提取指定session_id会话内容中所有用户发送的信息，写入本地txt文件。
    :param history_json_path: 聊天记录json文件路径
    :param txt_path: 保存的txt文件路径
    :param session_id: 需要提取的会话ID
    """
    with open(history_json_path, 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    user_msgs = []
    session = history_data.get(session_id, [])
    for msg in session:
        if msg.get('role') == 'user':
            user_msgs.append(msg.get('content', '').strip())
    with open(txt_path, 'w', encoding='utf-8') as f:
        for msg in user_msgs:
            f.write(msg + '\n')


def name_list2txt(name_list: List[str], txt_path: str) -> None:
    """
    将景点名列表写入本地 txt 文件。
    :param name_list: 景点名列表
    :param txt_path: 保存的 txt 文件路径
    """
    with open(txt_path, 'w', encoding='utf-8') as f:
        for name in name_list:
            f.write(name.strip() + '\n')


if __name__ == "__main__":
    # 测试 history2txt
    history2txt(r"C:\Users\cly\Desktop\CoDebug_from_Git\CoDebug\chat_history.json", "history_output.txt", "会话1")
    print("history2txt 已保存，内容如下：")
    with open("history_output.txt", "r", encoding="utf-8") as f:
        print(f.read())

    # 测试 node_json2name_list + name_list2txt
    name_list = node_json2name_list("backend/node_test.json")
    name_list2txt(name_list, "name_list_output.txt")
    print("name_list2txt 已保存，内容如下：")
    with open("name_list_output.txt", "r", encoding="utf-8") as f:
        print(f.read())
