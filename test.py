import jieba
from rank_bm25 import BM25Okapi
from memory import memory
from pathlib import Path
from bm25_index import BM25NovelIndex
import json

# text = "话总说不清楚, 陪你放肆的年少"

# result = list(jieba.cut(text))
# print(result)

# test_documents = [
#     "自然语言处理是人工智能信息领域的一个分支。",
#     "BM25是一种用于信息检索的排名算法。",
#     "jieba是一个中文数据分词库。",
#     "信息检索涉及从大量数据中检索相关信息。"
# ]

# # print(list(doc for doc in test_documents))

# # 将分词结果存储为列表，可以重复使用
# tokenized_docs = [jieba.lcut(doc) for doc in test_documents]

# # 查看分词结果（可选）
# print(tokenized_docs)

# # 构建BM25
# bm25 = BM25Okapi(tokenized_docs)

# # 后续可以多次使用tokenized_docs
# test_query = jieba.lcut("自然语言处理 分词")
# result = bm25.get_scores(test_query)
# print(result)


path = Path(__file__).parent / "robot_infor" / "旁观者"
# bm25Novel = BM25NovelIndex(path)
# with open(path / "summary.json", 'r', encoding='utf-8') as f:
#     result = json.load(f)

# bm25Novel.index_chapter(1, result['第1章'])

# bm25Novel.save()

memory_agent = memory(path)

query = "陆云 九幽启明 鞋印"


result = memory_agent.gain_relate(query)

print(result)