import json
from pathlib import Path
from robots import Robot
from chapter_robots import ChapterRobot


class user_input(Robot, ChapterRobot):
    """
    用户交互入口

    负责:
    - 显示项目信息(ZJ logo, 作者联系方式)
    - 接收用户选择(续写 / 新写)
    - 收集小说信息并启动创作流程
    """

    def __init__(self):
        super().__init__()

    def print_zj_inverted(self):
        """
        打印 ZJ 反色 ASCII logo

        使用 1/0 矩阵定义字母形状, 1 为挖空(空格), 0 为背景(星号),
        在星号背景上反色显示 ZJ 两个字母。
        """
        width = 50

        # Z 字母的 5x5 点阵 (1=字母区域, 0=背景)
        z = [
            "11111", "00001", "00010", "00100", "11111"
        ]

        # J 字母的 5x5 点阵
        j = [
            "11111", "00010", "00010", "10010", "01100"
        ]

        letters = [z, j]

        for i in range(5):
            # 拼接 Z 和 J 的点阵, 中间隔 5 个空格
            current_row = "     ".join([letters[k][i] for k in range(2)])

            # 计算左右星号填充数, 使 logo 居中
            padding = (width - len(current_row)) // 2

            line = "*" * padding

            # 核心转换: 1 → 空格(字母), 0 → 星号(背景)
            for char in current_row:
                line += " " if char == '1' else "*"

            line += "*" * (width - len(line))
            print(line)

    def title(self):
        """
        打印项目标题栏和作者信息
        """
        print(50 * '=')
        self.print_zj_inverted()
        print(50 * '=')
        print('本项目纯属个人学习,请勿商业用途,项目作者: 周君(ZJ)')
        print(50 * '=')
        print('更多项目请移步到网址: https://www.zhoujun.online')
        print(50 * '=')
        print('对项目有反馈?有新的项目想法?添加作者QQ: 3106045822')
        print('您的每一份支持将是作者无限更新的动力')
        print(50 * '=')

    def inquire(self):
        """
        用户交互主循环

        接收用户输入, 选择续写已有小说或开始全新创作。
        """
        while True:
            choice = input("续写小说还是写新的小说(续写小说请填入yes,写新的小说请填入no):")
            if choice == 'yes':
                self.novel_name = input("请输入小说名称:")
                super().UseRobot()
                break
            elif choice == 'no':
                super().create_novel()
                break
            else:
                print('输入错误,请重新输入')

    def update(self):
        """
        显示标题并启动用户交互
        """
        self.title()
        self.inquire()


# 启动入口
user_in = user_input()
user_in.update()
