# 该类负责机器人的创建与使用
from pathlib import Path
from init_robot import initRobot
from memory import memory
from logger_config import get_logger

logger = get_logger('myApp')

class Robot(initRobot):
    """
    主机器人 — 章节续写工作流

    继承 initRobot, 管理 8 个 AI 机器人的协作流程:
    墨云(策划) → 墨建(评审) → 墨笔(写作) → 审核组 → 墨结(总结)

    Attributes:
        novel_name: 当前小说名称
        outline_robot: 所有机器人的结果和上下文
        target_score: 审核目标得分(默认 80)
        chapter_num: 当前章节编号
        exam_panel: 审核组成员列表
        exam_field: 审核维度字段名
    """

    def __init__(self):
        super().__init__()
        self.first_signal = True

        # 小说名称
        self.novel_name = None

        # 机器人状态: result(返回结果), context(上下文), score(审核得分)
        self.outline_robot = {
            "墨云": {"result": {}, "context": {}},
            "墨笔": {"result": {}, "context": {}},
            "墨建": {"result": {}, "context": {}, "score": 0},
            "司命": {"result": {}, "context": {}, "score": 0},
            "墨文": {"result": {}, "context": {}, "score": 0},
            "知人": {"result": {}, "context": {}, "score": 0},
            "律动": {"result": {}, "context": {}, "score": 0},
            "墨结": {"result": {}, "context": {}},
        }

        # 审核目标得分
        self.target_score = 80

        # 当前章节编号
        self.chapter_num = 0

        # 审核组: 四名审核员及其对应的改进建议字段
        self.exam_panel = ["司命", "墨文", "知人", "律动"]
        self.exam_field = [
            "plotIimprovePoint", "proseImprovePoint",
            "charImprovePoint", "rhythmImprovePoint"
        ]

        # 初始化记忆组
        self.memory_agent = None

        # 存储前后章节以及相关章节的字典
        self.chapter_dict = {}

    @property
    def novel_file(self):
        """
        获取当前小说的所有数据文件路径

        Returns:
            dict: 包含 summary, chapterthread, personaltrait,
                  relationships, all_novel 的 Path 映射
        """
        base = Path(__file__).parent / f"robot_infor/{self.novel_name}"
        return {
            "total_path": base,
            "summary_path": base / "summary.json",
            "chapterthread_path": base / "chapterthread.json",
            "personaltrait_path": base / "personaltrait.json",
            "relationships_path": base / "relationships.json",
            "all_novel": base / "novel.md",
        }

    def novel_infor(self):
        """
        加载小说上下文信息到指定机器人的 context 中

        包括:
        - 前两章正文内容
        - 后两章的章节大纲
        - 当前章节出场人物及性格

        Args:
            context: 目标机器人的上下文字典
        """
        # 加载前两章正文
        self.memory_agent = memory(self.novel_file['total_path'])
        summary_json_data = super().readJson(self.novel_file['summary_path'])
        self.chapter_num = len(summary_json_data)

        logger.info(f'{self.novel_name} - 本次任务为续写小说')
        logger.info(f'{self.novel_name} - 已总结章节数量: {self.chapter_num}')

        before_text = list(summary_json_data.values())
        self.chapter_dict['before_main_text'] = {}
        if self.chapter_num == 0:
            self.chapter_dict['before_main_text']['one_text'] = '本章之前的第一章无内容'
            self.chapter_dict['before_main_text']['two_text'] = '本章之前的第二章无内容'
        elif self.chapter_num == 1:
            self.chapter_dict['before_main_text']['one_text'] = before_text[0]
            self.chapter_dict['before_main_text']['two_text'] = '本章之前的第二章无内容'
        else:
            self.chapter_dict['before_main_text']['one_text'] = before_text[self.chapter_num - 1]
            self.chapter_dict['before_main_text']['two_text'] = before_text[self.chapter_num - 2]

        # 加载后两章大纲
        json_data = super().readJson(self.novel_file['chapterthread_path'])
        chapter_keys = list(json_data.keys())
        total_chapters = len(json_data)

        logger.info(f'{self.novel_name} - 后续大纲章节数量: {total_chapters}')

        if total_chapters - self.chapter_num >= 2:
            self.chapter_dict['after_chapter_ouline'] = {
                'one_text': {chapter_keys[self.chapter_num + 1]: json_data[chapter_keys[self.chapter_num + 1]]},
                'two_text': {chapter_keys[self.chapter_num + 2]: json_data[chapter_keys[self.chapter_num + 2]]},
            }
        elif total_chapters - self.chapter_num == 1:
            self.chapter_dict['after_chapter_ouline'] = {
                'one_text': {chapter_keys[self.chapter_num + 1]: json_data[chapter_keys[self.chapter_num + 1]]},
                'two_text': {'本章之后的第二章章节大纲无内容': []},
            }
        else:
            self.chapter_dict['after_chapter_ouline'] = {
                'one_text': {'本章之后的第一章章节大纲无内容': []},
                'two_text': {'本章之后的第二章章节大纲无内容': []},
            }

        # 运行BM25加载当前章节前相关信息章节信息
        if chapter_keys and self.chapter_num < len(chapter_keys):
            result = self.memory_agent.gain_relate(chapter_keys[self.chapter_num])
            for i in result:
                i['summary'] = summary_json_data.get(str(i['chapter_num']), '本章没有查询到总结')
            logger.info(f'{self.novel_name} - BM25召回相关章节: {[r["chapter_num"] for r in result]}')
        else:
            logger.info(f'{self.novel_name} - 首次创作, 无历史章节可召回')
            result = []

        # 将信息加入到各个机器人字典中
        robots = ['墨云', '墨笔', '墨建', '司命']
        for i in robots:
            self.outline_robot[i]['context']['before_main_text'] = self.chapter_dict['before_main_text']
            self.outline_robot[i]['context']['after_chapter_ouline'] = self.chapter_dict['after_chapter_ouline']
            self.outline_robot[i]['context']['relevant_chapter'] = result

        # 首次运行时加载当前章节大纲和出场人物(仅墨云需要)
        if self.first_signal:
            self.first_signal = False
            if chapter_keys and self.chapter_num < len(chapter_keys):
                self.outline_robot['墨云']['now_chapter_outline'] = {
                    chapter_keys[self.chapter_num]: json_data[chapter_keys[self.chapter_num]]
                }
                now_personaltrait = json_data[chapter_keys[self.chapter_num]]
                traits_data = super().readJson(self.novel_file['personaltrait_path'])
                self.outline_robot['墨云']['now_personaltrait'] = {}
                for char_name in now_personaltrait:
                    self.outline_robot['墨云']['now_personaltrait'][char_name] = traits_data.get(char_name, {})
            else:
                logger.warning(f'{self.novel_name} - 首次运行但 chapterthread 为空')

    def mojie_end(self):
        """
        为墨结准备上下文: 章节正文、历史总结、出场人物及人物关系
        """
        self.outline_robot['墨结']['context']['chapter_outline'] = \
            self.outline_robot['墨笔']['result'].get('chapter_outline', '正文没有')
        self.outline_robot['墨结']['context']['prior_summary'] = \
            self.outline_robot['墨结']['result'].get('chapter_outline_summary', '之前还未写过任何内容')
        self.outline_robot['墨结']['context']['characters'] = \
            self.outline_robot['墨云']['result'].get('chapter_outline').get('characters')
        self.outline_robot['墨结']['context']['personalRelationships'] = {}

        # 加载当前出场人物的关系数据
        relationships_data = super().readJson(self.novel_file['relationships_path'])
        characters = self.outline_robot['墨云']['result'].get('chapter_outline').get('characters')
        for char_name in characters:
            self.outline_robot['墨结']['context']['personalRelationships'][char_name] = \
                relationships_data.get(char_name, {})

    def moyun(self):
        """
        墨云(策划者): 生成当前章节的章节大纲
        """

        # 调用 AI 生成大纲
        self.outline_robot['墨云']['result'] = super().response_robot(
            self.robot_md_content['墨云'],
            self.outline_robot['墨云']['context'],
            '墨云'
        )

        # 如果结果生成失败就重新生成
        if not self.outline_robot['墨云']['result'] or \
                'chapter_outline' not in self.outline_robot['墨云']['result']:
            self.test_signal = '墨云'
            self.outline_robot['墨云']['context']['comment'] = \
                "生成大纲失败或者没有关键字段chapter_outline, 请重新生成"
            logger.error(f'{self.novel_name} - 墨云生成结果缺少关键字段, 下面将重新生成')
            return

        # 将大纲传递给墨建进行评审
        self.outline_robot['墨建']['context']['chapter_outline'] = \
            self.outline_robot['墨云']['result'].get('chapter_outline')
        self.outline_robot['墨建']['context']['priorScore'] = \
            self.outline_robot['墨建'].get('score', 60)

        outline = self.outline_robot['墨云']['result'].get('chapter_outline', {})
        logger.info(f'{self.novel_name} - 墨云完成, 大纲标题: {outline.get("chapter_title", "无")}, 提交墨建评审')
        self.test_signal = '墨建'

    def mojian(self):
        """
        墨建(评审者): 评审大纲质量, 决定进入写作还是打回重写
        """

        # 调用 AI 评审
        self.outline_robot['墨建']['result'] = super().response_robot(
            self.robot_md_content['墨建'],
            self.outline_robot['墨建']['context'],
            '墨建'
        )

        if not self.outline_robot['墨建']['result']:
            self.test_signal = '墨建'
            logger.error(f'{self.novel_name} - 墨建返回结果为空, 下面将重新生成')
            return

        # 获取评审得分
        self.outline_robot['墨建']['score'] = \
            float(self.outline_robot['墨建']['result'].get('score', 0))

        # 根据得分决定下一步
        if self.outline_robot['墨建']['score'] <= 80:
            logger.warning(f'{self.novel_name} - 墨建评分: {self.outline_robot["墨建"]["score"]}, 低于80分, 打回墨云重写')
            # 打回重写: 将建议反馈给墨云
            self.outline_robot['墨云']['context']['before_chapter_outline'] = \
                self.outline_robot['墨云']['result'].get('chapter_outline', '之前还未写过任何内容')
            self.outline_robot['墨云']['context']['strengths'] = \
                self.outline_robot['墨建']['result'].get('strengths', [])
            self.outline_robot['墨云']['context']['issues'] = \
                self.outline_robot['墨建']['result'].get('issues', [])
            self.outline_robot['墨云']['context']['suggestions'] = \
                self.outline_robot['墨建']['result'].get('suggestions', [])
            self.test_signal = '墨云'
        else:
            logger.info(f'{self.novel_name} - 墨建评分: {self.outline_robot["墨建"]["score"]}, 审核通过, 交给墨笔生成正文')
            self.test_signal = '墨笔'

    def mobi(self):
        """
        墨笔(写手): 根据大纲撰写 2200+ 字正文
        """

        # 注入大纲
        self.outline_robot['墨笔']['context']['chapter_outline'] = \
            self.outline_robot['墨云']['result'].get('chapter_outline')

        # 调用 AI 撰写正文
        self.outline_robot['墨笔']['result'] = super().response_robot(
            self.robot_md_content['墨笔'],
            self.outline_robot['墨笔']['context'],
            '墨笔'
        )

        # 查看墨笔返回的结果是否正确
        if not self.outline_robot['墨笔']['result'] or \
                'chapter_outline' not in self.outline_robot['墨笔']['result']:
            self.test_signal = '墨笔'
            self.outline_robot['墨笔']['context']['comment'] = \
                "生成正文失败或者缺少关键字段chapter_outline, 请重新生成"
            logger.error(f'{self.novel_name} - 墨笔生成正文失败或缺少关键字段, 下面将重新生成')
            return

        # 检查字数是否达标
        text = self.outline_robot['墨笔']['result'].get('chapter_outline', '')
        if len(text) <= 2200:
            self.outline_robot['墨笔']['context']['prior_chapter_outline'] = text
            self.outline_robot['墨笔']['context']['comment'] = \
                f"字数只有{len(text)}, 请在保持文章质量以及满足大纲的前提下, 提高字数到2200字以上"
            self.test_signal = '墨笔'
            logger.error(f'{self.novel_name} - 墨笔正文字数不足2200字(当前{len(text)}字), 下面将重新生成')
            return

        # 正文通过: 初始化审核组上下文
        for reviewer in self.exam_panel:
            self.outline_robot[reviewer]['context']['chapter_outline'] = text
            # 首次审核默认 70 分
            self.outline_robot[reviewer]['context']['proirWeightedScore'] = \
                self.outline_robot[reviewer]['context'].get('proirWeightedScore', '70')

        logger.info(f'{self.novel_name} - 墨笔正文生成完成, {len(text)}字, 交给审核组审查')
        self.test_signal = '审核组'

    def novel_exam(self):
        """
        审核组: 四维审查(剧情/文笔/人物/节奏)
        """
        self.outline_robot['知人']['context']['now_personaltrait'] = \
            self.outline_robot['墨云']['result']['chapter_outline'].get(
                'now_personaltrait', '没有任何人物性格')

        i = 0
        while i < len(self.exam_panel):
            self.outline_robot[self.exam_panel[i]]['result'] = super().response_robot(
                self.robot_md_content[self.exam_panel[i]],
                self.outline_robot[self.exam_panel[i]]['context'],
                self.exam_panel[i]
            )

            # 这里设置为continue是为了在某个审核出错的时候又去审核他
            if not self.outline_robot[self.exam_panel[i]]['result']:
                logger.error(f'{self.novel_name} - {self.exam_panel[i]} 审核失败, 下面将打回重新审核')
                continue

            i += 1

        # 记录各审核员得分
        for reviewer in self.exam_panel:
            self.outline_robot[reviewer]['score'] = \
                float(self.outline_robot[reviewer]['result'].get('weightedScore', 0))
            logger.info(f'{self.novel_name} - {reviewer} 得分: {self.outline_robot[reviewer]["score"]}')
            self.outline_robot[reviewer]['context']['proirWeightedScore'] = \
                self.outline_robot[reviewer]['score']

        # 全部通过则进入总结阶段, 否则打回重写
        if all(self.outline_robot[r]['score'] > self.target_score for r in self.exam_panel):
            logger.info(f'{self.novel_name} - 四维审核全部通过, 进入总结阶段')
            self.test_signal = '墨结'
        else:
            # 将四维建议反馈给墨笔
            self.outline_robot['墨笔']['context']['prior_chapter_outline'] = \
                self.outline_robot['墨笔']['result'].get('chapter_outline', '之前还未写过任何内容')
            for reviewer, field in zip(self.exam_panel, self.exam_field):
                self.outline_robot['墨笔']['context'][field] = \
                    self.outline_robot[reviewer]['result'].get(field)

            failed = [r for r in self.exam_panel if self.outline_robot[r]['score'] <= self.target_score]
            logger.warning(f'{self.novel_name} - 审核未通过, 未达标审核员: {failed}, 打回墨笔重写')
            self.test_signal = '墨笔'

    def novel_end(self):
        """
        墨结完成后: 保存正文、更新人物关系、写入章节总结
        """
        # 检查总结字数是否超标
        summary = self.outline_robot['墨结']['result'].get('chapter_outline_summary', '')
        if len(summary) > 800:
            self.outline_robot['墨结']['context']['notes'] = \
                f"你上一次的总结字数为{len(summary)}, 超过阈值800, 请减少字数"
            logger.warning(f'{self.novel_name} - 墨结总结第{self.chapter_num+1}章字数超标({len(summary)}字>800字)')
            self.test_signal = '墨结'
            return

        # 存入新的人物性格
        traits_data = super().readJson(self.novel_file['personaltrait_path'])
        new_traits = self.outline_robot['墨云']['result'].get(
            'chapter_outline', {}).get('now_personaltrait', {})
        for key, value in new_traits.items():
            traits_data[key] = value
        super().write_json(self.novel_file['personaltrait_path'], traits_data)

        # 追加小说正文
        with open(self.novel_file['all_novel'], 'a', encoding='utf-8') as f:
            f.write("\n")
            f.write(f"### 第{self.chapter_num + 1}章\n")
            f.write(self.outline_robot['墨笔']['result'].get('chapter_outline'))

        # 更新人物关系
        relationships_data = super().readJson(self.novel_file['relationships_path'])
        new_relationships = self.outline_robot['墨结']['result'].get('newPersonalRelationships', {})
        for key, value in new_relationships.items():
            relationships_data[key.strip()] = value
        super().write_json(self.novel_file['relationships_path'], relationships_data)

        # 写入章节总结
        summary_data = super().readJson(self.novel_file['summary_path'])
        summary_data[f'{self.chapter_num + 1}'] = \
            self.outline_robot['墨结']['result'].get('chapter_outline_summary', '无')
        super().write_json(self.novel_file['summary_path'], summary_data)

        # 将章节总结写入json与pkl文件中
        self.memory_agent.save_memory(self.chapter_num + 1, self.outline_robot['墨笔']['result'].get('chapter_outline'))

        logger.info(f'{self.novel_name} - 第{self.chapter_num+1}章完成, 已保存正文、总结、人物关系、BM25索引')
        self.test_signal = '结束'

    def mojie(self):
        """
        墨结(总结者): 生成章节总结、人物关系更新
        """
        self.mojie_end()
        self.outline_robot['墨结']['result'] = super().response_robot(
            self.robot_md_content['墨结'],
            self.outline_robot['墨结']['context'],
            '墨结'
        )
        self.novel_end()

    def UseRobot(self):
        """
        主循环: 根据状态机信号依次调用各机器人
        """
        logger.info(f"开始创作小说: {self.novel_name}, 目标得分: {self.target_score}")
        # 初始化前后章节以及相关章节
        self.novel_infor()
        try:
            while True:
                if self.test_signal == '墨云':
                    logger.debug('状态切换 → 墨云（策划大纲）')
                    self.moyun()
                elif self.test_signal == '墨笔':
                    logger.debug('状态切换 → 墨笔（撰写正文）')
                    self.mobi()
                elif self.test_signal == '墨建':
                    logger.debug('状态切换 → 墨建（评审大纲）')
                    self.mojian()
                elif self.test_signal == '审核组':
                    logger.debug('状态切换 → 审核组（四维审查）')
                    self.novel_exam()
                elif self.test_signal == '墨结':
                    logger.debug('状态切换 → 墨结（总结存档）')
                    self.mojie()
                elif self.test_signal == '结束':
                    logger.info(f"第 {self.chapter_num + 1} 章创作完成！")
                    break
        except Exception:
            pass
