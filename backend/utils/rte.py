import json
from tenacity import retry, stop_after_attempt, wait_random_exponential
from .langchain_helper import llm_helper
import asyncio

async def extract_triplets(document):
    """
    调用AI模型对单个文档进行关系三元组抽取，返回AI的答案。
    """
    prompt_for_rte = f"""Perform the document-level relation triplet extraction task. Give you the document and pre-defined relation types, you need to extract possible relation triplets. Provide each relation triplet in the following format: (head entity, tail entity, relation type)\n\nThe document:\n{document}. \nYour response must be like: 1.(entity_head, entity_tail, relation);2.(entity_head, entity_tail, relation). \n\n### Response:"""
    messages = [
        {'role': 'system', 'content': 'You are an information extraction assistant.'},
        {'role': 'user', 'content': prompt_for_rte}
    ]
    # 只保留一次提问，temperature=0保证稳定性
    for _ in range(3):
        try:
            response = await llm_helper.get_completion_from_messages(messages)
            return response
        except Exception as e:
            print("LLM API error:", e)
            print("Retrying in 2 seconds...")
            await asyncio.sleep(2)
    print("Failed to get completion from LLM API.")
    return ""

def parse_triplets(ai_response):
    """
    解析AI返回的文本，提取三元组列表。
    只保留 {"h": ..., "t": ..., "r": ...}，h/t/r 都为自然语言。
    适应如下格式：
    1. (queen, Snow-white, parent-child)
    2. (king, queen, spouse)
    ...
    """
    import re
    triplets = []
    if asyncio.iscoroutine(ai_response):
        # 如果传入的是协程对象，需await获取结果
        loop = asyncio.get_event_loop()
        ai_response = loop.run_until_complete(ai_response)
    lines = ai_response.strip().split('\n')
    for line in lines:
        # 去掉编号前缀和多余空格
        line = line.strip()
        # 允许处理"1. (...)"或"(...)"等格式
        line = re.sub(r'^\d+\.\s*', '', line)
        match = re.match(r"[\(\（]([^\(\),，]+)[,，]\s*([^\(\),，]+)[,，]\s*([^\(\),，]+)[\)\）]", line)
        if match:
            h, t, r = match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
            triplets.append({"h": h, "t": t, "r": r})
    return triplets

async def rte_from_text(document, output_path=None):
    """
    对输入文档逐条抽取三元组，保存到 output_path
    """
    results = []

    ai_response = await extract_triplets(document)
    triplets = parse_triplets(ai_response)
    print("Extracted triplets:", triplets)
    for triplet in triplets:
        results.append(triplet)
    # 保存结果
    if output_path != None:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(results)} triplets to {output_path}")
    return results