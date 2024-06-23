import os
import requests

# 从环境变量获取用户数据
app_urls = os.getenv("APP_URLS").split(",")
app_names = os.getenv("APP_NAMES").split(",")
api_keys = os.getenv("API_KEYS").split(",")

# 确保每个列表的长度相同
assert len(app_urls) == len(app_names) == len(api_keys), "所有列表的长度必须相同"

# 创建用户字典
users = {
    app_name: {
        "app_url": app_url,
        "app_name": app_name,
        "api_key": api_key,
    }
    for app_url, app_name, api_key in zip(app_urls, app_names, api_keys)
}

base_url = 'https://app.koyeb.com/v1/apps'   # 这个不要动

# 从环境变量获取 Telegram 变量，不填则默认不用
tgbot_token = os.getenv("TGBOT_TOKEN")    # 填写Telegram bot token
tgchat_id = os.getenv("TGCHAT_ID")    # 填写Telegram chat id

# 发送tg消息
def send_telegram_message(tgbot_token, tgchat_id, send_message):
    if tgbot_token and tgchat_id and send_message:
        response = requests.post(
            f'https://api.telegram.org/bot{tgbot_token}/sendMessage',
            json={"chat_id": tgchat_id, "text": send_message}
        )
        return response.status_code == 200

# 检查app的域名状态是否正常
def check_app_status(app_url):
    try:
        response = requests.get(app_url)
        return response.status_code == 200
    except requests.RequestException as e:
        return False

# 恢复app
def resume_app(api_key, app_name):
    api_headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(base_url, headers=api_headers)
    if response.status_code == 200:
        apps = response.json().get('apps', [])
        for app in apps:
            if app['name'] == app_name:
                app_id = app['id']
                app_status = app['status']
                # 如果 App 状态不是 HEALTHY，则尝试恢复
                if app_status != 'HEALTHY':
                    resume_url = f'{base_url}/{app_id}/resume'
                    resume_response = requests.post(resume_url, headers=api_headers)
                    if resume_response.status_code == 200:
                        send_message = "Koyeb app is successfully resumed !"
                        send_telegram_message(tgbot_token, tgchat_id, send_message)
                        return True
                    else:
                        print(f"Failed to resume app: {resume_response.status_code}")
                else:
                    send_message = "Koyeb app is healthy,no need to do anything."
                    # 状态正常，默认注释不发送消息，需要使用去掉注释即可
                   # send_telegram_message(tgbot_token, tgchat_id, send_message)
                return False
        else:
            print(f"App named {app_name} not found.")
            return False
    else:
        print(f"Failed to fetch apps: {response.status_code}")
        return False

def main():
    # 对每个用户检查应用状态
    for user, user_data in users.items():
        app_url = user_data["app_url"]
        app_name = user_data["app_name"]
        api_key = user_data["api_key"]
        if not check_app_status(app_url):
            print(f"Koyeb app of {user} 状态异常,正在恢复")
            resume_app(api_key, app_name)
        else:
            print(f"Koyeb app of {user} 状态正常,无需操作")

if __name__ == "__main__":
    main()
