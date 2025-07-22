import asyncio
import json
from typing import Dict, List, Any
import httpx

# 测试配置 - 您可以修改这些参数
BASE_URL = "http://localhost:8000"  # 修改为您的API服务地址
API_ENDPOINT = "/api/agent/get_highlight_nodes"

# 测试数据配置 - 您可以根据需要修改这些参数
TEST_SESSION_ID = "test_session_123"
TEST_CHAT_HISTORY = {
  "会话1": [
    {
      "role": "user",
      "content": "你是谁？"
    },
    {
      "role": "assistant",
      "content": "我是你的创意助手，专注于帮助你探索新的想法和可能性。无论是头脑风暴、解决问题，还是寻找灵感，我都能为你提供支持和建议。我们可以一起讨论各种主题，或者深入研究你的创意项目。你有什么想法或问题想要分享吗？"
    }
  ],
  "会话2": [
    {
      "role": "user",
      "content": "你是谁？"
    },
    {
      "role": "assistant",
      "content": "我是一个人工智能助手，旨在提供信息和回答问题。有什么我可以帮助你的吗？"
    }
  ]
}

TEST_NODES = [
    {
        "node_name": "故宫博物院",
        "price": "旺季60元/人（4月1日-10月31日），淡季40元/人（11月1日-次年3月31日），珍宝馆10元/人，钟表馆10元/人",
        "play_time": "3h",
        "attractions": [
            {
                "item_name": "故宫",
                "item_price": "60元",
                "item_play_time": "全天"
            },
            {
                "item_name": "珍宝馆",
                "item_price": "10元",
                "item_play_time": "视参观时间而定"
            },
            {
                "item_name": "钟表馆",
                "item_price": "10元",
                "item_play_time": "视参观时间而定"
            }
        ]
    },
    {
        "node_name": "天安门广场",
        "price": "免费",
        "play_time": "2h-3h",
        "attractions": [
            {
                "item_name": "天安门城楼",
                "item_price": "15元/人",
                "item_play_time": "08:30-16:30（旺季），08:30-17:00（淡季）"
            },
            {
                "item_name": "人民大会堂",
                "item_price": "免费",
                "item_play_time": "不明确"
            },
            {
                "item_name": "毛主席纪念堂",
                "item_price": "免费",
                "item_play_time": "不明确"
            },
            {
                "item_name": "人民英雄纪念碑",
                "item_price": "免费",
                "item_play_time": "不明确"
            }
        ]
    },
    {
        "node_name": "颐和园",
        "price": "旺季30元/张，淡季20元/张（联票旺季60元/张，淡季50元/张）",
        "play_time": "3小时",
        "attractions": [
            {
                "item_name": "颐和园门票",
                "item_price": "30元/张（旺季） 20元/张（淡季）",
                "item_play_time": "3小时"
            },
            {
                "item_name": "颐和园联票",
                "item_price": "60元/张（旺季） 50元/张（淡季）",
                "item_play_time": "3小时"
            },
            {
                "item_name": "德和园",
                "item_price": "5元/张",
                "item_play_time": "1.5小时"
            },
            {
                "item_name": "颐和园博物馆",
                "item_price": "20元/张",
                "item_play_time": "1.5小时"
            },
            {
                "item_name": "佛香阁",
                "item_price": "10元/张",
                "item_play_time": "1.5小时"
            },
            {
                "item_name": "苏州街",
                "item_price": "10元/张",
                "item_play_time": "1.5小时"
            },
            {
                "item_name": "电瓶船",
                "item_price": "80元/小时(4座); 120元/小时(6座)",
                "item_play_time": "1-2小时"
            },
            {
                "item_name": "自驾电瓶船",
                "item_price": "200元/小时",
                "item_play_time": "1小时"
            },
            {
                "item_name": "大船摆渡航线",
                "item_price": "30-40元/人",
                "item_play_time": "30分钟"
            },
            {
                "item_name": "包船服务",
                "item_price": "3000-8000元/小时",
                "item_play_time": "1小时"
            }
        ]
    },
    {
        "node_name": "北海公园",
        "price": "旺季（4月1日-10月31日）门票10元，联票20元；淡季（11月1日-3月31日）门票5元，联票15元",
        "play_time": "3h",
        "attractions": [
            {
                "item_name": "北海公园门票",
                "item_price": "10元/张 (旺季), 5元/张 (淡季)",
                "item_play_time": "4小时"
            },
            {
                "item_name": "北海公园联票",
                "item_price": "20元/张 (旺季), 15元/张 (淡季)",
                "item_play_time": "4小时"
            },
            {
                "item_name": "白塔",
                "item_price": "需另外购票",
                "item_play_time": "未指定"
            },
            {
                "item_name": "九龙壁",
                "item_price": "包含在门票内",
                "item_play_time": "未指定"
            },
            {
                "item_name": "静心斋",
                "item_price": "包含在联票内",
                "item_play_time": "未指定"
            }
        ]
    },
    {
        "node_name": "天坛公园",
        "price": "旺季15元，淡季10元",
        "play_time": "3h",
        "attractions": [
            {
                "item_name": "祈年殿",
                "item_price": "15元",
                "item_play_time": "旺季: 4月1日—10月31日"
            },
            {
                "item_name": "圜丘",
                "item_price": "15元",
                "item_play_time": "旺季: 4月1日—10月31日"
            },
            {
                "item_name": "回音壁",
                "item_price": "15元",
                "item_play_time": "旺季: 4月1日—10月31日"
            },
            {
                "item_name": "斋宫",
                "item_price": "15元",
                "item_play_time": "旺季: 4月1日—10月31日"
            },
            {
                "item_name": "北神厨",
                "item_price": "15元",
                "item_play_time": "旺季: 4月1日—10月31日"
            },
            {
                "item_name": "北宰牲亭",
                "item_price": "15元",
                "item_play_time": "旺季: 4月1日—10月31日"
            }
        ]
    },
    {
        "node_name": "八达岭长城",
        "price": "成人票40元，学生票20元",
        "play_time": "3h",
        "attractions": [
            {
                "item_name": "八达岭长城和天坛私人一日游",
                "item_price": "成人价格低至US$60.00US$54.00（价格因团体规模而异）",
                "item_play_time": "一日游"
            },
            {
                "item_name": "夜游长城",
                "item_price": "未提及",
                "item_play_time": "每周五、周六，开放时间为7时30分至9时30分"
            },
            {
                "item_name": "八达岭长城成人门票",
                "item_price": "40元/人",
                "item_play_time": "未提及"
            },
            {
                "item_name": "八达岭长城学生门票",
                "item_price": "20元/人",
                "item_play_time": "未提及"
            }
        ]
    },
    {
        "node_name": "慕田峪长城",
        "price": "成人票40元，优惠票20元",
        "play_time": "3h-4h",
        "attractions": [
            {
                "item_name": "慕田峪长城",
                "item_price": "40元/人",
                "item_play_time": "全天"
            },
            {
                "item_name": "缆车/索道/滑道单程",
                "item_price": "100元/人",
                "item_play_time": "10分钟"
            },
            {
                "item_name": "缆车/索道/滑道往返",
                "item_price": "140元/人",
                "item_play_time": "20分钟"
            },
            {
                "item_name": "套票（门 + 巴士 + 缆车往返或索道上滑道下）",
                "item_price": "成人200元，长者180元，1.2米以上儿童155元",
                "item_play_time": "全天"
            }
        ]
    },
    {
        "node_name": "圆明园",
        "price": "成人票10元/人次，半价票5元/人次，未成年人免费",
        "play_time": "3小时",
        "attractions": [
            {
                "item_name": "圆明园大门门票",
                "item_price": "10元/人次",
                "item_play_time": "全天"
            },
            {
                "item_name": "西洋楼遗址景区",
                "item_price": "15元/人次",
                "item_play_time": "全天"
            },
            {
                "item_name": "沙盘全景模型展",
                "item_price": "10元/人次",
                "item_play_time": "全天"
            },
            {
                "item_name": "通票",
                "item_price": "25元/人次",
                "item_play_time": "全天"
            }
        ]
    },
    {
        "node_name": "明十三陵",
        "price": "淡季20元，旺季30元（总神道）；淡季20元，旺季30元（明昭陵）；联票98元/人",
        "play_time": "3h-4h",
        "attractions": [
            {
                "item_name": "定陵",
                "item_price": "40元",
                "item_play_time": "3-4小时"
            },
            {
                "item_name": "长陵",
                "item_price": "30元",
                "item_play_time": "3-4小时"
            },
            {
                "item_name": "神路",
                "item_price": "20元",
                "item_play_time": "3-4小时"
            },
            {
                "item_name": "昭陵",
                "item_price": "20元",
                "item_play_time": "3-4小时"
            },
            {
                "item_name": "联票（定陵＋长陵＋神路＋昭陵）",
                "item_price": "98元",
                "item_play_time": "3-4小时"
            },
            {
                "item_name": "康陵",
                "item_price": "10元",
                "item_play_time": "3-4小时"
            },
            {
                "item_name": "永陵",
                "item_price": "20元",
                "item_play_time": "3-4小时"
            },
            {
                "item_name": "思陵",
                "item_price": "20元",
                "item_play_time": "3-4小时"
            }
        ]
    },
    {
        "node_name": "雍和宫",
        "price": "25元（半价票12元）",
        "play_time": "2-3小时",
        "attractions": [
            {
                "item_name": "雍和宫",
                "item_price": "25元（半价票12元）",
                "item_play_time": "冬春季09:00—16:30；夏秋季09:00—17:00"
            },
            {
                "item_name": "大愿祈祷法会",
                "item_price": "免费",
                "item_play_time": "根据节庆安排"
            },
            {
                "item_name": "昭泰门",
                "item_price": "免费",
                "item_play_time": "根据开放时间"
            },
            {
                "item_name": "永佑殿",
                "item_price": "免费",
                "item_play_time": "根据开放时间"
            }
        ]
    },
    {
        "node_name": "南锣鼓巷",
        "price": "免费",
        "play_time": "2h-3h",
        "attractions": [
            {
                "item_name": "文宇奶酪店",
                "item_price": "无",
                "item_play_time": "无"
            },
            {
                "item_name": "过客",
                "item_price": "无",
                "item_play_time": "无"
            },
            {
                "item_name": "原装备户外折扣店",
                "item_price": "专卖店的一半甚至更低",
                "item_play_time": "无"
            },
            {
                "item_name": "FANCY-ME",
                "item_price": "无",
                "item_play_time": "无"
            },
            {
                "item_name": "南锣鼓巷",
                "item_price": "免费",
                "item_play_time": "全天开放"
            }
        ]
    },
    {
        "node_name": "什刹海",
        "price": "免费",
        "play_time": "3小时",
        "attractions": [
            {
                "item_name": "什刹海风景区（后海）",
                "item_price": "免费",
                "item_play_time": "3小时"
            },
            {
                "item_name": "银锭桥",
                "item_price": "免费",
                "item_play_time": "2小时 - 4小时"
            },
            {
                "item_name": "坐摇橹船",
                "item_price": "80元",
                "item_play_time": "约30分钟"
            },
            {
                "item_name": "四人电瓶船",
                "item_price": "240元/小时",
                "item_play_time": "1小时"
            },
            {
                "item_name": "四人脚踏船",
                "item_price": "180元/小时",
                "item_play_time": "1小时"
            },
            {
                "item_name": "六人电瓶船",
                "item_price": "280元/小时",
                "item_play_time": "1小时"
            }
        ]
    }
]


class HighlightNodesTestClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.endpoint = API_ENDPOINT

    async def test_highlight_nodes(self,
                                   chat_history: Dict[str, List[Dict[str, str]]] = None,
                                   session_id: str = None,
                                   nodes: List[Dict[str, Any]] = None):
        """
        测试highlight nodes接口

        Args:
            chat_history: 聊天历史，如果为None则使用默认值
            session_id: 会话ID，如果为None则使用默认值
            nodes: 节点列表，如果为None则使用默认值
        """
        # 使用默认值或传入的参数
        test_data = {
            "chat_history": chat_history or TEST_CHAT_HISTORY,
            "session_id": session_id or TEST_SESSION_ID,
            "nodes": nodes or TEST_NODES
        }


        print(f"测试数据:")
        print(f"Session ID: {test_data['session_id']}")
        print(f"聊天历史会话数: {len(test_data['chat_history'])}")
        print(f"节点数量: {len(test_data['nodes'])}")
        print(f"节点名称: {[node['node_name'] for node in test_data['nodes']]}")
        # print(f"test_data: \n {test_data}")
        print("-" * 50)

        # test_data = json.dumps(test_data, ensure_ascii=False)

        print(f"test_data: \n {test_data}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}{self.endpoint}",
                    json=test_data
                )

                print(f"响应状态码: {response.status_code}")
                print(f"响应内容: {response.text}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 成功! 推荐的景点: {result.get('highlight_nodes', [])}")
                    return result
                else:
                    print(f"❌ 失败! 状态码: {response.status_code}")
                    print(f"错误信息: {response.text}")
                    return None

            except Exception as e:
                print(f"❌ 请求异常: {str(e)}")
                return None


async def run_tests():
    """运行所有测试用例"""
    client = HighlightNodesTestClient()

    print("🚀 开始测试 highlight_nodes 接口")
    print("=" * 60)

    # 测试用例1: 使用默认参数
    print("\n📋 测试用例1: 默认参数测试")
    await client.test_highlight_nodes()

    # 测试用例2: 空聊天历史
    print("\n📋 测试用例2: 空聊天历史测试")
    empty_history = {TEST_SESSION_ID: []}
    await client.test_highlight_nodes(chat_history=empty_history)

    # 测试用例3: 不存在的session_id
    print("\n📋 测试用例3: 不存在的session_id测试")
    await client.test_highlight_nodes(session_id="non_existent_session")

    # 测试用例4: 只有一条用户消息
    print("\n📋 测试用例4: 单条用户消息测试")
    single_message_history = {
        "single_session": [
            {
                "role": "user",
                "content": "我想去故宫看看"
            }
        ]
    }
    await client.test_highlight_nodes(
        chat_history=single_message_history,
        session_id="single_session"
    )

    # 测试用例5: 自定义节点列表
    print("\n📋 测试用例5: 自定义节点列表测试")
    custom_nodes = [
        {
            "node_name": "故宫",
            "price": "60元",
            "play_time": "3小时",
            "attractions": []
        },
        {
            "node_name": "西湖",
            "price": "免费",
            "play_time": "2小时",
            "attractions": []
        }
    ]
    await client.test_highlight_nodes(nodes=custom_nodes)

    # 测试用例6: 复杂聊天场景
    print("\n📋 测试用例6: 复杂聊天场景测试")
    complex_history = {
        "complex_session": [
            {
                "role": "user",
                "content": "我计划在北京待3天，主要想看历史文化景点"
            },
            {
                "role": "assistant",
                "content": "北京有很多历史文化景点，比如故宫、天坛、颐和园等"
            },
            {
                "role": "user",
                "content": "故宫是必须要去的，天坛我也很感兴趣。颐和园怎么样？"
            },
            {
                "role": "assistant",
                "content": "颐和园是清朝的皇家园林，风景优美"
            },
            {
                "role": "user",
                "content": "好的，那我就安排故宫、天坛和颐和园这三个地方"
            }
        ]
    }
    await client.test_highlight_nodes(
        chat_history=complex_history,
        session_id="complex_session"
    )


def sync_test():
    """同步测试函数"""
    asyncio.run(run_tests())


if __name__ == "__main__":
    # 运行测试
    print("开始测试...")
    sync_test()
    print("\n✨ 测试完成!")