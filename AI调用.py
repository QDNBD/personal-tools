import json
import requests
import argparse


configs = {
    "ai_services": {
        "openai": {
            "api_key": "your_openai_api_key",  # OpenAI的API密钥
            "api_url": "https:#api.openai.com/v1/chat/completions",
            # OpenAI的API地址
            "model": "gpt-3.5-turbo",  # 使用的模型
            "temperature": 0.7,  # 模型输出的随机性，值越小越确定
            "max_tokens": 1000  # 最大返回的token数
        },
        "doukao_ai": {
            "api_key": "your_doukao_api_key",  # 豆包AI的API密钥
            "api_url": "https:#api.doukao.com/v1/ppt/generate",  # 豆包AI的API地址
            "model": "doukao-ppt",  # 使用的模型
            "temperature": 0.5,  # 模型输出的随机性，值越小越确定
            "max_tokens": 2000  # 最大返回的token数
        }
    },
    "default_service": "openai",  # 默认使用的AI服务
    "workflow": {
        "ppt_generation": {
            "steps": [
                {
                    "service": "openai",  # 第一步使用的AI服务
                    "prompt": "Generate a PPT outline for the following topic: {topic}",
                    # 输入提示，{topic}是占位符
                    "output_key": "outline"  # 第一步的输出保存到input_params中的键名
                },
                {
                    "service": "doukao_ai",  # 第二步使用的AI服务
                    "prompt": "Create a PPT based on the following outline: {outline}",
                    # 输入提示，{outline}是占位符
                    "output_key": "ppt_result"  # 第二步的输出保存到input_params中的键名
                }
            ]
        }
    }
}

class AIInterface:
    def __init__(self, config_file):
        """
        初始化AIInterface类，加载配置文件。

        Args:
            config_file (str): 配置文件的路径
        """
        self.config = self._load_config(config_file)
        self.services = self.config["ai_services"]
        self.default_service = self.config["default_service"]
        self.workflow = self.config["workflow"]

    def _load_config(self, config_file):
        """
        读取并加载配置文件。

        Args:
            config_file (str): 配置文件的路径

        Returns:
            dict: 加载的配置文件内容
        """
        # with open(config_file, "r") as f:
        #     return json.load(f)
        return configs

    def _get_service_config(self, service_name):
        """
        获取指定AI服务的配置信息。

        Args:
            service_name (str): AI服务的名称

        Returns:
            dict: 服务的配置信息

        Raises:
            ValueError: 如果服务名称在配置文件中不存在
        """
        if service_name in self.services:
            return self.services[service_name]
        else:
            raise ValueError(
                f"Service '{service_name}' not found in configuration.")

    def _call_openai(self, prompt, config):
        """
        调用OpenAI的API。

        Args:
            prompt (str): 输入的提示
            config (dict): OpenAI服务的配置信息

        Returns:
            str: OpenAI返回的响应内容
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}"
        }
        data = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"]
        }
        response = requests.post(config["api_url"], headers=headers, json=data)
        return response.json()["choices"][0]["message"]["content"]

    def _call_doukao_ai(self, prompt, config):
        """
        调用豆包AI的API。

        Args:
            prompt (str): 输入的提示
            config (dict): 豆包AI服务的配置信息

        Returns:
            str: 豆包AI返回的响应内容
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}"
        }
        data = {
            "text": prompt,
            "model": config["model"],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"]
        }
        response = requests.post(config["api_url"], headers=headers, json=data)
        return response.json()["result"]

    def call_ai(self, prompt, service_name=None):
        """
        根据指定的AI服务名称调用相应的API。

        Args:
            prompt (str): 输入的提示
            service_name (str, optional): 要调用的AI服务名称。如果不指定，则使用默认服务

        Returns:
            str: AI服务返回的响应内容

        Raises:
            ValueError: 如果指定的服务名称不支持
        """
        if service_name is None:
            service_name = self.default_service
        service_config = self._get_service_config(service_name)
        if service_name == "openai":
            return self._call_openai(prompt, service_config)
        elif service_name == "doukao_ai":
            return self._call_doukao_ai(prompt, service_config)
        else:
            raise ValueError(f"Unsupported service '{service_name}'.")

    def execute_workflow(self, workflow_name, input_params):
        """
        执行定义的工作流，依次调用每个步骤的AI服务。

        Args:
            workflow_name (str): 要执行的工作流名称
            input_params (dict): 工作流的初始输入参数

        Returns:
            str: 工作流最后一个步骤的响应内容

        Raises:
            ValueError: 如果工作流名称在配置文件中不存在
        """
        if workflow_name not in self.workflow:
            raise ValueError(
                f"Workflow '{workflow_name}' not found in configuration.")
        workflow = self.workflow[workflow_name]
        output = None
        for step in workflow["steps"]:
            service = step["service"]
            prompt = step["prompt"]
            # 替换占位符
            prompt = prompt.format(**input_params)
            # 调用AI服务
            response = self.call_ai(prompt, service)
            # 更新输出参数
            input_params.update({step["output_key"]: response})
            output = response
        return output





def main():
    """
    主函数，处理命令行参数并执行AI接口调用。
    """
    parser = argparse.ArgumentParser(description="AI Interface with Workflow")
    parser.add_argument("--workflow", type=str,
                        help="Workflow to execute (e.g., ppt_generation)")
    parser.add_argument("--input", type=json.loads,
                        help="Input parameters as JSON")
    parser.add_argument("--config", type=str, default="ai_config.json",
                        help="Path to configuration file")
    args = parser.parse_args()

    ai = AIInterface(args.config)
    if args.workflow:
        if args.input:
            input_params = args.input
        else:
            input_params = {}
        response = ai.execute_workflow(args.workflow, input_params)
        print("Final AI Response:")
        print(response)
    else:
        # 如果不使用工作流，可以保留之前的单个AI调用功能
        pass


if __name__ == "__main__":
    main()
