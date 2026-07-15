from bm25_index import BM25NovelIndex


class memory():
    """
    功能:写小说的时候获取最相关的五个章节  完整小说的时候就将当前章节的总结内容进行分词存储进入pkl
    """
    def __init__(self, novel_path: str):
        self.memory = []
        self.bm25Novel = BM25NovelIndex(novel_path)  # 初始化的时候就已经_load了

    def gain_relate(self, query):
        """  
        获取最相关的五个章节
        """
        return self.bm25Novel.search(query, top_k=5)

    def save_memory(self, chapter_number ,chapter_content):
        """
        存储当前章节总结的jieba分词进入pkl
        """
        self.bm25Novel.index_chapter(chapter_number, chapter_content)
        self.bm25Novel.save()