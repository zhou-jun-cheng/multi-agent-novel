from init_robot import initRobot
import json
import time
from pathlib import Path
import pickle
from logger_config import get_logger

logger = get_logger('myApp')


class ChapterRobot(initRobot):
    """
    章节规划机器人

    负责在新小说创建时, 由墨章规划整本书的章节结构和出场人物,
    为后续逐章续写提供全局大纲。

    Attributes:
        mozhang_result: 墨章的返回结果
        mozhang_context: 墨章的上下文信息
        cre_path: 新小说需要创建的配置文件模板
    """

    def __init__(self):
        super().__init__()

        # 墨章的结果和上下文
        self.mozhang_result = {}
        self.mozhang_context = {}

        # 新小说需要创建的配置文件
        self.cre_path = {
            'chapterthread.json': {},
            'novel.md': None,
            'overallthread.json': {},
            'personaltrait.json': {},
            'relationships.json': {},
            'summary.json': {},
            'bm25_index.pkl':{}
        }

    def mozhang(self, overallthread):
        """
        调用墨章规划全书章节

        Args:
            overallthread: 小说总体信息(标题、总章数、世界观等)

        Returns:
            tuple: (signal, message)
                - signal=1: 创建失败(文件/系统错误)
                - signal=2: 章数不匹配, 需要重试
                - signal=3: 创建成功
        """
        novel_name = overallthread['title']
        logger.info(f'{novel_name} - 本次任务为创建新的小说')
        logger.info(f'{novel_name} - 墨章开始规划小说, 总章数: {overallthread.get("totalChapters", "未指定")}')

        # 创建小说数据目录
        file_path = Path(__file__).parent / f"robot_infor/{novel_name}"
        file_path.mkdir(parents=True, exist_ok=True)
        logger.info(f'{novel_name} - 墨章创建小说数据目录: robot_infor/{novel_name}')

        # 初始化配置文件
        for filename, default_value in self.cre_path.items():
            test_path = Path(__file__).parent / f"robot_infor/{novel_name}/{filename}"
            if filename == 'overallthread.json':
                super().write_json(test_path, overallthread)
            elif filename == 'bm25_index.pkl':
                with open(test_path, "wb") as f:
                    pickle.dump(default_value, f)
            else:
                super().write_json(test_path, default_value)
            logger.info(f"{novel_name} - 墨章已初始化 {filename} 配置文件")

        # 读取总体大纲作为墨章的上下文
        try:
            test_path = Path(__file__).parent / f"robot_infor/{novel_name}/overallthread.json"
            json_data = super().readJson(test_path)
            self.mozhang_context['overallthread'] = json_data
            logger.info(f"{novel_name} - 墨章读取总体大纲成功")
        except FileNotFoundError:
            logger.error(f'{novel_name} - 墨章读取总体大纲失败, 缺少 overallthread.json 文件')
            return 1, '找不到相关的文件, 初始化小说失败'
        except json.JSONDecodeError:
            logger.error(f'{novel_name} - 墨章读取总体大纲失败, overallthread.json 不是合法的 json 文件')
            return 1, '发现不合适的文件, 初始化小说失败'
        except Exception as e:
            logger.error(f'{novel_name} - 墨章读取总体大纲失败, 未知错误: {e}')
            return 1, '初始化小说出现未知错误, 初始化小说失败'

        # 调用 AI 规划全书章节
        logger.info(f"{novel_name} - [墨章] 开始规划全书章节...")
        self.mozhang_result = super().response_robot(
            self.robot_md_content['墨章'],
            self.mozhang_context['overallthread'],
            '墨章'
        )

        if not self.mozhang_result:
            logger.warning(f'{novel_name} - 墨章返回创作结果失败')
            return 2, '墨章创建的小说章节大纲没有返回结果, 下面即将重新创建'

        # 检查生成的章数是否与用户要求一致
        if len(self.mozhang_result) != overallthread['totalChapters']:
            self.mozhang_context['notes'] = \
                f"上一次生成的章数只有{len(self.mozhang_result)}, " \
                f"请在保持文章总体大纲的前提下, 生成{overallthread['totalChapters']}章, 必须严格执行"
            logger.warning(f'{novel_name} - 墨章章数不匹配: 生成 {len(self.mozhang_result)} 章, 需要 {overallthread["totalChapters"]} 章')
            return 2, '小说章节缺失不足'

        # 保存章节大纲到 chapterthread.json
        try:
            test_path = Path(__file__).parent / f"robot_infor/{novel_name}/chapterthread.json"
            super().write_json(test_path, self.mozhang_result)
            logger.info(f'{novel_name} - 墨章创建的小说章节大纲成功\n')
        except Exception as e:
            logger.error(f'{novel_name} - 墨章创建的小说章节大纲存入文件中出现未知错误: {e}')
            return 1, '创建小说出现未知错误, 创建小说失败'

        logger.info(f"{novel_name} - [墨章] 全书 {overallthread['totalChapters']} 章规划完成!")
        return 3, '小说创建成功, 即将返回首页'


    def create_novel(self):
        """
        创建新小说: 最多重试 5 次, 直到墨章规划成功
        """

        overallthread = {}

        # # ===== 以下为正式版本的用户输入(测试时注释掉) =====
        overallthread['title'] = input("请输入小说标题: ")
        overallthread['totalChapters'] = int(input("请输入小说总章数: "))
        overallthread['author'] = input("请输入小说作者: ")
        overallthread['genre'] = input("请输入小说类型: ")
        overallthread['worldSetting'] = input("请输入小说世界观: ")
        overallthread['mainIdea'] = input("请输入小说主要故事情节: ")
        overallthread['arcs'] = []
        overallthread['notice'] = input("请输入小说的注意事项: ")

        choice = input('是否需要规定卷轴信息(yes表示需要, no表示不需要): ')
        while choice == 'yes':
            arcs_infor = {}
            arcs_infor['卷名'] = input('请输入本卷名(例如:第一卷_青云崛起): ')
            arcs_infor['chapters']  = input('请输入本卷的章节范围(例如:1-25): ')
            arcs_infor['theme']  = input('请输入本卷的主要故事线: ')
            arcs_infor['tone']  = input('请输入本卷的主要情感基调(压抑→希望→热血): ')
            new_choice = input('是否需要添加本卷主要章节信息(yes表示需要, no表示不需要):')
            while new_choice == 'yes':
                keyEvents = {}
                keyEvents['chapter']  = input('请输入章节的章节数(例如: 20): ')
                keyEvents['event']  = input('请输入该章节的章节名(例如: 突破淬体巅峰): ')
                keyEvents['description']  = input('请输入该章节的主要描述:')
                arcs_infor['keyEvents'] = keyEvents
                new_choice = input('是否需要继续添加本卷主要章节信息(yes表示需要, no表示不需要):')
            overallthread['arcs'].append(arcs_infor)
            choice = input('是否需要继续添加新的卷轴信息(yes表示需要, no表示不需要)')

        max_retries = 5
        for attempt in range(max_retries):

            logger.debug(f"第 {attempt + 1}/{max_retries} 次尝试...")

            signal, content = self.mozhang(overallthread)
            if signal == 1:
                logger.error(f"创建失败: {content}")
                break
            elif signal == 2:
                logger.debug(f"{content}, 3秒后重试...")
                time.sleep(3)
                continue
            elif signal == 3:
                logger.debug(f"{content}")
                break
