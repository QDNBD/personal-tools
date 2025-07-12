from flask import Flask, request, jsonify
from datetime import datetime
import json
import requests
import os

app = Flask(__name__)

class AIInterface:
    def __init__(self, config_file):
        self.config = self._load_config(config_file)
        self.services = self.config["ai_services"]
        self.default_service = self.config["default_service"]
        self.workflow = self.config["workflow"]
        self.max_calls_per_user = self.config["api_settings"]["max_calls_per_user"]
        self.admin_key = self.config["api_settings"]["admin_key"]
        self.user_calls_file = "user_calls.json"

        # 初始化用户调用次数文件
        if not os.path.exists(self.user_calls_file):
            self._init_user_calls_file()

    def _load_config(self, config_file):
        with open(config_file, "r") as f:
            return json.load(f)

    def _init_user_calls_file(self):
        # 初始化用户调用次数文件
        initial_data = {
            "users": {},
            "admin_key": self.admin_key
        }
        with open(self.user_calls_file, "w") as f:
            json.dump(initial_data, f)

    def _get_service_config(self, service_name):
        if service_name in self.services:
            return self.services[service_name]
        else:
            raise ValueError(f"Service '{service_name}' not found in configuration.")

    def _call_openai(self, prompt, config):
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
        if workflow_name not in self.workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found in configuration.")
        workflow = self.workflow[workflow_name]
        output = None
        for step in workflow["steps"]:
            service = step["service"]
            prompt = step["prompt"]
            prompt = prompt.format(**input_params)
            response = self.call_ai(prompt, service)
            input_params.update({step["output_key"]: response})
            output = response
        return output

    def check_user_calls(self, user_id):
        # 读取用户调用次数文件
        with open(self.user_calls_file, "r") as f:
            user_data = json.load(f)
            users = user_data.get("users", {})
            admin_key = user_data.get("admin_key", "")

        if user_id not in users:
            # 初始化新用户
            self.init_user(user_id)
            return True, self.max_calls_per_user

        remaining_calls = users[user_id].get("remaining_calls", 0)
        if remaining_calls <= 0:
            return False, 0
        return True, remaining_calls

    def init_user(self, user_id):
        # 初始化新用户
        user_data = {
            "user_id": user_id,
            "remaining_calls": self.max_calls_per_user,
            "last_call_time": datetime.now().isoformat()
        }

        # 更新用户调用次数文件
        with open(self.user_calls_file, "r") as f:
            data = json.load(f)
            data["users"][user_id] = user_data

        with open(self.user_calls_file, "w") as f:
            json.dump(data, f)

    def decrease_user_calls(self, user_id):
        # 更新用户调用次数文件
        with open(self.user_calls_file, "r") as f:
            data = json.load(f)
            users = data.get("users", {})
            if user_id in users:
                users[user_id]["remaining_calls"] -= 1
                users[user_id]["last_call_time"] = datetime.now().isoformat()

        with open(self.user_calls_file, "w") as f:
            json.dump(data, f)

    def reset_user_calls(self, user_id):
        # 重置用户调用次数
        with open(self.user_calls_file, "r") as f:
            data = json.load(f)
            users = data.get("users", {})
            if user_id in users:
                users[user_id]["remaining_calls"] = self.max_calls_per_user
                users[user_id]["last_call_time"] = datetime.now().isoformat()

        with open(self.user_calls_file, "w") as f:
            json.dump(data, f)

@app.route('/api/v1/execute_workflow', methods=['POST'])
def execute_workflow():
    data = request.get_json()
    user_id = data.get('user_id')
    workflow_name = data.get('workflow_name')
    input_params = data.get('input_params', {})

    ai = AIInterface('ai_config.json')
    can_call, remaining = ai.check_user_calls(user_id)
    if not can_call:
        return jsonify({"error": "API call limit exceeded. Please contact admin to reset calls."}), 429

    try:
        response = ai.execute_workflow(workflow_name, input_params)
        ai.decrease_user_calls(user_id)
        return jsonify({"result": response, "remaining_calls": remaining - 1})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/reset_calls', methods=['POST'])
def reset_calls():
    data = request.get_json()
    user_id = data.get('user_id')
    admin_key = data.get('admin_key')

    ai = AIInterface('ai_config.json')
    if admin_key != ai.admin_key:
        return jsonify({"error": "Invalid admin key."}), 403

    ai.reset_user_calls(user_id)
    return jsonify({"message": "API call limit reset successfully."})

if __name__ == "__main__":
    app.run(debug=True)


{
    "users": {
        "user123": {
            "remaining_calls": 5,
            "last_call_time": "2025-02-28T10:00:00"
        },
        "another_user": {
            "remaining_calls": 5,
            "last_call_time": "2025-02-28T10:00:00"
        }
    },
    "admin_key": "your_admin_key"
}


{
    "ai_services": {
        "openai": {
            "api_key": "your_openai_api_key",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "doukao_ai": {
            "api_key": "your_doukao_api_key",
            "api_url": "https://api.doukao.com/v1/ppt/generate",
            "model": "doukao-ppt",
            "temperature": 0.5,
            "max_tokens": 2000
        }
    },
    "default_service": "openai",
    "workflow": {
        "ppt_generation": {
            "steps": [
                {
                    "service": "openai",
                    "prompt": "Generate a PPT outline for the following topic: {topic}",
                    "output_key": "outline"
                },
                {
                    "service": "doukao_ai",
                    "prompt": "Create a PPT based on the following outline: {outline}",
                    "output_key": "ppt_result"
                }
            ]
        }
    },
    "api_settings": {
        "max_calls_per_user": 5,
        "admin_key": "your_admin_key"
    }
}

# 运行
python3 ai_api_server.py

测试 API 服务
初始化用户：

bash
curl -X POST http://localhost:5000/api/v1/reset_calls \
-H "Content-Type: application/json" \
-d '{"user_id": "user123", "admin_key": "your_admin_key"}'
调用工作流：

bash
curl -X POST http://localhost:5000/api/v1/execute_workflow \
-H "Content-Type: application/json" \
-d '{"user_id": "user123", "workflow_name": "ppt_generation", "input_params": {"topic": "人工智能的发展"}}'
检查调用次数：

bash
curl -X POST http://localhost:5000/api/v1/reset_calls \
-H "Content-Type: application/json" \
-d '{"user_id": "user123", "admin_key": "your_admin_key"}'