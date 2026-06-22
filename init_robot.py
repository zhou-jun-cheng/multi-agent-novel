from pathlib import Path
from openai import OpenAI
import os
import json
import threading


class initRobot:
    """
    机器人基类

    负责管理所有 AI 机器人的系统提示词、调用 DeepSeek API、
    以及提供通用的文件读写方法。

    Attributes:
        robot_md: 机器人名称到 md 文件路径的映射
        robot_md_content: 机器人名称到系统提示词内容的映射
        client: DeepSeek OpenAI 客户端实例
        test_signal: 状态机信号, 控制下一个执行的机器人
    """

    def __init__(self):
        # 机器人系统提示词文件路径
        self.robot_md = {
            "墨云": Path(__file__).parent / "robot_infor/moyun.md",
            "墨笔": Path(__file__).parent / "robot_infor/mobi.md",
            "墨建": Path(__file__).parent / "robot_infor/mojian.md",
            "司命": Path(__file__).parent / "robot_infor/siming.md",
            "墨文": Path(__file__).parent / "robot_infor/mowen.md",
            "知人": Path(__file__).parent / "robot_infor/zhiren.md",
            "律动": Path(__file__).parent / "robot_infor/ludong.md",
            "墨章": Path(__file__).parent / "robot_infor/mozhang.md",
            "墨结": Path(__file__).parent / "robot_infor/mojie.md",
        }

        # 机器人系统提示词内容缓存
        self.robot_md_content = {
            "墨云": "", "墨笔": "", "墨建": "", "司命": "", "墨文": "",
            "知人": "", "律动": "", "墨章": "", "墨结": ""
        }

        # DeepSeek API 客户端
        self.client = OpenAI(
            api_key=os.environ.get('API_KEY'),
            base_url="https://api.deepseek.com"
        )

        # 状态机初始信号
        self.test_signal = '墨云'

        # 加载所有机器人提示词
        self.robot_md_fun()

    def extract_system_prompt(self, md_content):
        """
        从 md 文件中提取系统提示词

        提取 "## 系统提示词" 标记之后的内容,
        如果未找到标记则返回全文。

        Args:
            md_content: md 文件的完整文本内容

        Returns:
            str: 提取后的系统提示词文本
        """
        marker = "## 系统提示词"

        if marker not in md_content:
            return md_content.strip()

        # 分割后取标记之后的内容
        parts = md_content.split(marker, 1)
        return parts[1].strip()

    def robot_md_fun(self):
        """
        读取所有机器人的 md 文件并提取系统提示词

        遍历 robot_md 字典, 读取每个文件内容,
        调用 extract_system_prompt 提取提示词,
        存入 robot_md_content 字典。
        """
        for name, path_md in self.robot_md.items():
            with open(path_md, 'r', encoding='utf-8') as f:
                self.robot_md_content[name] = self.extract_system_prompt(f.read())

    def CreateRobot(self, robot_md, context):
        """
        调用 DeepSeek API 获取机器人回复  因此这个API回复相当快 便于测试 此处可以换位其他API或者本地模型

        Args:
            robot_md: 机器人的系统提示词
            context: 本次请求的上下文(用户输入)

        Returns:
            str: API 返回的原始文本内容
        """
        # context 如果是 dict 就转成 JSON 字符串
        if isinstance(context, dict):

            #  此处需要在服务器上面修改
            context = json.dumps(context, ensure_ascii=False)

        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": robot_md},
                {"role": "user", "content": context}
            ],
            response_format={'type': 'json_object'},
        )
        return response.choices[0].message.content

    def readJson(self, path):
        """
        读取 JSON 文件

        Args:
            path: JSON 文件路径

        Returns:
            dict: 解析后的字典, 文件不存在或格式错误时返回空字典
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, Exception):
            return {}

    def write_json(self, path, json_data):
        """
        写入 JSON 文件

        Args:
            path: 目标文件路径
            json_data: 要写入的字典数据

        Returns:
            bool: 写入成功返回 True, 失败返回 False
        """
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
                return True
        except Exception:
            return False

    def response_robot(self, robot_md_content, robot_context, robot_name):
        """
        调用 AI 并解析返回结果为 JSON

        Args:
            robot_md_content: 机器人的系统提示词
            robot_context: 本次请求的上下文字典
            robot_name: 机器人名称, 用于日志输出

        Returns:
            dict|bool: 解析后的 JSON 字典, 失败时返回 False
        """
        print(f"\n{'='*50}")
        print(f"🤖 [{robot_name}] 开始执行...")

        # 调用 AI 获取回复
        try:
            result = self.CreateRobot(robot_md_content, robot_context)
        except Exception as e:
            print(f"❌ [{robot_name}] 调用AI失败:{e}")
            return False

        # 将返回的文本解析为 JSON
        try:
            result = json.loads(result)
        except Exception:
            robot_context['comment'] = '请务必保证返回的格式为json格式'
            print(f"❌ [{robot_name}] JSON解析失败")
            return False

        # 打印关键结果摘要
        self._print_result(robot_name, result)
        return result

    def _print_result(self, robot_name, result):
        """
        格式化打印机器人输出结果摘要

        Args:
            robot_name: 机器人名称
            result: AI 返回的 JSON 字典
        """
        if not isinstance(result, dict):
            print(f"✅ [{robot_name}] 返回: {result}")
            return

        # 根据不同机器人打印关键信息
        if robot_name == '墨云':
            outline = result.get('chapter_outline', {})
            print(f"✅ [{robot_name}] 大纲标题: {outline.get('chapter_title', '无')}")
            print(f"   核心事件: {outline.get('core_event', '无')}")
            if outline.get('characters'):
                print(f"   出场人物: {', '.join(outline['characters'])}")

        elif robot_name == '墨建':
            print(f"✅ [{robot_name}] 评分: {result.get('score', '无')}")
            if result.get('issues'):
                print(f"   问题: {result.get('issues')}")

        elif robot_name == '墨笔':
            text = result.get('chapter_outline', '')
            print(f"✅ [{robot_name}] 正文字数: {len(text)} 字")

        elif robot_name == '墨章':
            count = len(result) if isinstance(result, dict) else '无'
            print(f"✅ [{robot_name}] 规划章节数: {count}")

        elif robot_name in ['司命', '墨文', '知人', '律动']:
            score = result.get('weightedScore', '无')
            print(f"✅ [{robot_name}] 得分: {score}")

        elif robot_name == '墨结':
            summary = result.get('chapter_outline_summary', '')
            print(f"✅ [{robot_name}] 总结字数: {len(summary)} 字")

        else:
            print(f"✅ [{robot_name}] 返回字段: {list(result.keys())}")
