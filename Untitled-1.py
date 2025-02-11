import requests # type: ignore

# Spotify API 凭据（用你的 client_id 和 client_secret 替换）
CLIENT_ID = "618dc1d561664b3883dc34f734105f34"
CLIENT_SECRET = "a90e50001cd348899590d5592b91b0a3"

# Spotify API Token URL
TOKEN_URL = "https://accounts.spotify.com/api/token"

# 获取新的 access token
def get_access_token():
    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
    )
    
    if response.status_code == 200:
        token_info = response.json()
        return token_info["access_token"]
    else:
        print("Error getting access token:", response.json())
        return None

# 更新 access token
ACCESS_TOKEN = get_access_token()

# 发送请求
if ACCESS_TOKEN:
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    search_url = "https://api.spotify.com/v1/search"
    params = {"q": "bob", "type": "artist", "limit": 2}

    response = requests.get(search_url, headers=headers, params=params)

    print(response.json())  # 打印返回的数据
else:
    print("Failed to get access token.")