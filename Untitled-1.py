import requests
import json
import time

# Spotify API 认证信息（请替换为您的 CLIENT_ID 和 CLIENT_SECRET）
CLIENT_ID = "618dc1d561664b3883dc34f734105f34"
CLIENT_SECRET = "a90e50001cd348899590d5592b91b0a3"

# Spotify API 认证 URL
TOKEN_URL = "https://accounts.spotify.com/api/token"

def get_access_token():
    """
    获取新的 Spotify API 访问令牌（Access Token）
    """
    response = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    response_data = response.json()
    return response_data["access_token"], response_data["expires_in"]

# 获取 Access Token
access_token, expires_in = get_access_token()
print(f"✅ 获取新 Access Token: {access_token}")
print(f"⌛ 令牌有效期: {expires_in} 秒")

# 设置查询参数
search_url = "https://api.spotify.com/v1/search"
params = {"q": "bob", "type": "artist", "limit": 2}

def search_spotify():
    """
    使用当前 Access Token 查询 Spotify API
    """
    global access_token  # 确保可以更新全局变量
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(search_url, headers=headers, params=params)
    
    # 处理 Token 过期的情况
    if response.status_code == 401:  # 401 表示 Token 过期
        print("⚠️ Access Token 过期，正在刷新...")
        access_token, _ = get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(search_url, headers=headers, params=params)

    return response.json()

# 发送 API 请求
data = search_spotify()

# 输出查询结果
print("\n🎵 **搜索到的艺术家:**\n")
for artist in data['artists']['items']:
    name = artist['name']
    genres = ", ".join(artist['genres']) if artist['genres'] else "无风格数据"
    spotify_url = artist['external_urls']['spotify']
    
    print(f"🎤 **{name}**")
    print(f"🎶 风格: {genres}")
    print(f"🔗 Spotify: {spotify_url}\n")