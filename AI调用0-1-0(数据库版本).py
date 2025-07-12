from flask import Flask, request, jsonify
from datetime import datetime
import json
import requests
import sqlite3

app = Flask(__name__)

# 初始化数据库
def init_db():
    conn = sqlite3.connect('ai_calls.db')
    cursor = cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_calls (
            user_id TEXT PRIMARY KEY,
            remaining_calls INTEGER DEFAULT 5,
            last_call_time TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class AIInterface:
    def __init__(self, config_file):
        self.config = self._load_config(config_file)
        self.services = self.config["ai_services"]
        self.default_service = self.config["default_service"]
        self.workflow = self.config["workflow"]
        self.max_calls_per_user = self.config["api_settings"]["max_calls_per_user"]
        self.admin_key = self.config["api_settings"]["admin_key"]
        self.db_path = 'ai_calls.db'

    def _load_config(self, config_file):
        with open(config_file, "r") as f:
            return json.load(f)

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT remaining_calls, last_call_time FROM user_calls WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if not result:
            # 初始化新用户
            self.init_user(user_id)
            return True, self.max_calls_per_user
        remaining_calls, last_call_time = result
        if remaining_calls <= 0:
            return False, 0
        return True, remaining_calls

    def init_user(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_calls (user_id, remaining_calls, last_call_time)
            VALUES (?, ?, ?)
        ''', (user_id, self.max_calls_per_user, datetime.now()))
        conn.commit()
        conn.close()

    def decrease_user_calls(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_calls SET remaining_calls = remaining_calls - 1, last_call_time = ?
            WHERE user_id = ?
        ''', (datetime.now(), user_id))
        conn.commit()
        conn.close()

    def reset_user_calls(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_calls SET remaining_calls = ?, last_call_time = ?
            WHERE user_id = ?
        ''', (self.max_calls_per_user, datetime.now(), user_id))
        conn.commit()
        conn.close()

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


confs = {
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
        "max_calls_per_user": 5,  # 每个用户的最大调用次数
        "admin_key": "your_admin_key"  # 管理员密钥
    }
}
