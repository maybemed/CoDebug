import json

from lark.tools import encoding

from backend.utils.graph_data_func import process_edges,validate_nodes


# 使用示例和测试
def test_validate_nodes():
    """测试函数"""
    with open('nodes.json', 'r', encoding='utf-8') as f:
        # 读取测试数据
        test_nodes = json.load(f)

        result = validate_nodes(test_nodes)
        print(f"原始数据长度: {len(test_nodes)}")
        print(f"验证后数据长度: {len(result)}")

        for i, node in enumerate(result):
            print(f"Node {i + 1}: {node['node_name']}")

        return result


# 如果需要运行测试
if __name__ == "__main__":
    r = json.dumps(test_validate_nodes(), ensure_ascii=False, indent=4)
    print(r)