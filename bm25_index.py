"""
BM25 小说检索索引

用法:
    idx = BM25NovelIndex(novel_path)
    idx.index_chapter(1, "正文内容...", outline_data)
    results = idx.search("周君 青云城 比武", top_k=5)
"""

import pickle
from pathlib import Path
import jieba
from rank_bm25 import BM25Okapi


class BM25NovelIndex:
    """小说 BM25 检索索引"""

    def __init__(self, novel_path: Path):
        """
        Args:
            novel_path: 小说数据目录路径 (robot_infor/{小说名})
        """
        self.novel_path = novel_path
        self.corpus = []       # 每章分词后的列表
        self.chapter_ids = []  # 对应章节编号
        self.bm25 = None
        self._load()

    # ========= 索引操作 =========

    def index_chapter(self, chapter_num: int, text: str, outline: dict = None):
        """每写完一章就调用这个方法, 将分词内容存起来"""

        if chapter_num in self.chapter_ids:
            return  # 已索引，跳过
        doc = self._tokenize(text, outline)  # 将正文与大纲关键词一起用jieba分词, 得到一个词列表

        # 将分词结果与章节编号对应存起来, corpus[0]对应第一章的词列表
        self.corpus.append(doc)

        self.chapter_ids.append(chapter_num)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        拿关键词从已知索引的章节找到最相关的

        Returns:
            [{"chapter_num": 1, "score": 3.2}, ...]
        """

        # 还没有建索引直接返回空
        if not self.bm25 or not self.corpus:
            return []


        # 将查询的字符串进行jieba分词  如"周君 战斗 天天酷跑"  => ["周君", "战斗", "天天酷跑"]
        query_tokens = self._tokenize_text(query)

        # BM25算法核心 算出每章和这个查询的相关分数 分数越高越相关
        scores = self.bm25.get_scores(query_tokens)

        # 将分数从高到低进行排序 提取出来最相关的章节  如下[(0, 3.2), (3, 2.8), (5, 1.1), ...]  元组第一个是章节 第二个是相关程度
        top = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]


        # 此处返回为一个字典 但是返回的字段要求score大于零
        return [
            {
                "chapter_num": self.chapter_ids[i],
                "score": round(float(score), 2),
            }
            for i, score in top
            if score > 0
        ]

    # ========= 持久化 =========

    def save(self):
        """保存索引到磁盘"""

        index_path = self.novel_path / "bm25_index.pkl"  # 存放章节编号和分词结果

        with open(index_path, "wb") as f:
            pickle.dump({
                "corpus": self.corpus,
                "chapter_ids": self.chapter_ids,
            }, f)

    def _load(self):
        """从磁盘加载索引"""

        index_path = self.novel_path / "bm25_index.pkl"

        # 如果pkl文件不存在，尝试从summary.json恢复
        if not index_path.exists():
            import json
            summary_path = self.novel_path / "summary.json"
            if summary_path.exists():
                with open(summary_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    for index, value in result.items():
                        self.index_chapter(int(index), value)
                    self.save()

        if index_path.exists():
            with open(index_path, "rb") as f:

                # 用pickle恢复完整数据
                data = pickle.load(f)

                # 获取分词列表
                self.corpus = data.get('corpus', [])

                # 获取章节编号
                self.chapter_ids = data.get('chapter_ids', [])

        #  有数据就重构BM25索引
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)

    # ========= 内部方法 =========

    def _tokenize(self, text: str, outline: dict = None) -> list[str]:
        """文本分词 + 大纲关键词注入"""

        # 使用jieba对文本进行分词
        tokens = self._tokenize_text(text)

        if outline:
            # 注入大纲关键词提升权重（重复加入 = 提高 BM25 分数）
            for key in ["characters", "setting", "core_event"]:
                val = outline.get(key, [])  # 获取各个主要的信息
                if isinstance(val, list):  # 如果是列表
                    for item in val:
                        tokens.extend(self._tokenize_text(str(item)))
                elif isinstance(val, str):  # 如果是字符串
                    tokens.extend(self._tokenize_text(val))
        return tokens

    @staticmethod
    def _tokenize_text(text: str) -> list[str]:
        """用 jieba 分词"""
        return list(jieba.cut(text))
