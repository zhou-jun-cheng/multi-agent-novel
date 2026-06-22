from init_robot import initRobot
import json
import time
from pathlib import Path
from pathlib import Path


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
        print(f"\n{'='*50}")
        print(f"📖 墨章开始规划小说: {novel_name}")
        print(f"   总章数: {overallthread.get('totalChapters', '未指定')}")
        print(f"{'='*50}")

        # 创建小说数据目录
        file_path = Path(__file__).parent / f"robot_infor/{novel_name}"
        file_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 已创建数据目录: robot_infor/{novel_name}/")

        # 初始化配置文件
        for filename, default_value in self.cre_path.items():
            test_path = Path(__file__).parent / f"robot_infor/{novel_name}/{filename}"
            if filename == 'overallthread.json':
                # 总体大纲需要写入用户输入的 overallthread 数据
                super().write_json(test_path, overallthread)
            else:
                super().write_json(test_path, default_value)
        print(f"✅ 已初始化 {len(self.cre_path)} 个配置文件")

        # 读取总体大纲作为墨章的上下文
        try:
            test_path = Path(__file__).parent / f"robot_infor/{novel_name}/overallthread.json"
            json_data = super().readJson(test_path)
            self.mozhang_context['overallthread'] = json_data
        except FileNotFoundError:
            print('❌ 错误: overallthread.json 文件不存在!')
            return 1, '找不到相关的文件, 初始化小说失败'
        except json.JSONDecodeError:
            print('❌ 错误: overallthread.json 文件格式不是合法 JSON!')
            return 1, '发现不合适的文件, 初始化小说失败'
        except Exception as e:
            print(f"❌ 读取配置文件出现未知错误: {e}")
            return 1, '初始化小说出现未知错误, 初始化小说失败'

        # 调用 AI 规划全书章节
        print(f"\n🤖 [墨章] 开始规划全书章节...")
        self.mozhang_result = super().response_robot(
            self.robot_md_content['墨章'],
            self.mozhang_context['overallthread'],
            '墨章'
        )

        print('--------------------')

        print(self.mozhang_result)

        print('--------------------')




        if not self.mozhang_result:
            print(f"❌ [墨章] 生成失败")
            return False, '创建小说出现未知错误, 初始化小说失败'

        # 检查生成的章数是否与用户要求一致
        if len(self.mozhang_result) != overallthread['totalChapters']:
            self.mozhang_context['notes'] = \
                f"上一次生成的章数只有{len(self.mozhang_result)}, " \
                f"请在保持文章总体大纲的前提下, 生成{overallthread['totalChapters']}章, 必须严格执行"
            print(f"⚠️  [墨章] 章数不匹配: 生成 {len(self.mozhang_result)} 章, "
                  f"需要 {overallthread['totalChapters']} 章")
            return 2, '小说章节缺失不足'
        


        print('*'*50)        

        # 保存章节大纲到 chapterthread.json
        try:
            test_path = Path(__file__).parent / f"robot_infor/{novel_name}/chapterthread.json"
            super().write_json(test_path, self.mozhang_result)
        except Exception as e:
            print(f"❌ 存储文件出现未知错误: {e}")
            return 1, '创建小说出现未知错误, 创建小说失败'

        print(f"✅ [墨章] 全书 {overallthread['totalChapters']} 章规划完成!")
        return 3, '小说创建成功, 即将返回首页'


    def create_novel(self):
        """
        创建新小说: 最多重试 5 次, 直到墨章规划成功
        """

        # ===== 测试用固定数据 =====
        overallthread = {
            'title': '周君的故事',
            'totalChapters': 50,
            'author': '周君',
            'genre': '玄幻',
            'worldSetting': '青云大陆，以武为尊，天下分裂，急需一位强者出来主持公道',
            'mainIdea': '周君20岁以前被世人骂为废物，但是偶然觉醒青云决，最终统一天下1的故事',
            'arcs': [
                {
                    '卷名': '第一卷-青云崛起',
                    'chapters': '1-25',
                    'theme': '周君偶然觉醒青云决，并在世界第一比武获得第一名的故事',
                    'tone': '压抑-希望',
                    'keyEvents': {
                        'chapter': '20',
                        'event': '周君初登决赛',
                        'description': '周君在世界第一比武登上决赛，令世界其他帮派都惊愕不已，因为周君毫无背景'
                    }
                }
            ],
            'notice': '无'
        }

        # ===== 以下为正式版本的用户输入(测试时注释掉) =====
        # overallthread['title'] = input("请输入小说标题: ")
        # overallthread['totalChapters'] = int(input("请输入小说总章数: "))
        # overallthread['author'] = input("请输入小说作者: ")
        # overallthread['genre'] = input("请输入小说类型: ")
        # overallthread['worldSetting'] = input("请输入小说世界观: ")
        # overallthread['mainIdea'] = input("请输入小说主要故事情节: ")
        # overallthread['arcs'] = []
        # overallthread['notice'] = input("请输入小说的注意事项: ")

        # choice = input('是否需要规定卷轴信息(yes表示需要, no表示不需要): ')
        # while choice == 'yes':
        #     arcs_infor = {}
        #     arcs_infor['卷名'] = input('请输入本卷名(例如:第一卷_青云崛起): ')
        #     arcs_infor['chapters']  = input('请输入本卷的章节范围(例如:1-25): ')
        #     arcs_infor['theme']  = input('请输入本卷的主要故事线: ')
        #     arcs_infor['tone']  = input('请输入本卷的主要情感基调(压抑→希望→热血): ')
        #     new_choice = input('是否需要添加本卷主要章节信息(yes表示需要, no表示不需要):')
        #     while new_choice == 'yes':
        #         keyEvents = {}
        #         keyEvents['chapter']  = input('请输入章节的章节数(例如: 20): ')
        #         keyEvents['event']  = input('请输入该章节的章节名(例如: 突破淬体巅峰): ')
        #         keyEvents['description']  = input('请输入该章节的主要描述:')
        #         arcs_infor['keyEvents'] = keyEvents
        #         new_choice = input('是否需要继续添加本卷主要章节信息(yes表示需要, no表示不需要):')
        #     overallthread['arcs'].append(arcs_infor)
        #     choice = input('是否需要继续添加新的卷轴信息(yes表示需要, no表示不需要)')



        max_retries = 5
        for attempt in range(max_retries):


            print(f"\n🔄 第 {attempt + 1}/{max_retries} 次尝试...")
            print('*'*50)
            print(self.mozhang_context)
            print('*'*50)
            print('下面输出墨章')
            print(self.robot_md_content['墨章'])
            print('+'*50)


            signal, content = self.mozhang(overallthread)
            if signal == 1:
                # 创建失败, 停止重试
                print(f"❌ {content}")
                break
            elif signal == 2:
                # 章数不匹配, 等待后重试
                print(f"⚠️  {content}, 3秒后重试...")
                time.sleep(3)   
                continue
            elif signal == 3:
                # 创建成功
                print(f"✅ {content}")
                break
