from app.config.setting import Settings


class TaskService:
    """
        这里是主要逻辑了，实现几个方法就行了应该是
    """

    def __init__(self, config: Settings):
        self.config = config

    def run(self):
        """
            主逻辑
            input： 目标url
            return： 前端需要的返回值，msg: 状态信息（成功/自定义失败原因），状态码（请见common/constant和response，可以参考喂ai），docs？：报告文档
        """
        pass

    def dify_workflow(self):
        """
            调用dify工作流
        """
        pass

    def create_report(self):
        """
            生成报告(这个你可以使用模板，写一个规定好格式的docs文件，然后进行关键字替换，这样既保证了字体统一，也保证了格式的确定性和自定义的简单，具体的关键词替换和设定，要ai帮你）
        """
        pass

    def save_task(self):
        """
            保存任务数据到数据库
        """
        pass
