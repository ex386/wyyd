import requests 
import json 
import os 
import time 
import re
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3. disable_warnings(InsecureRequestWarning) 
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen.flac import FLAC, Picture

def get_music_url(music_id, leval_name, interface):
    
    get_music_url_payload = {
        "id": music_id,
        "level": leval_name
    }
    
    try:
        response = requests.post(f"https://wyapi-{interface}.toubiec.cn/api/music/url", data=get_music_url_payload, verify=False)
        download_result = response.json()
        
        if download_result.get("code") != 200 or not download_result.get("data"):
            print(f"❌ id: {music_id} 获取下载链接失败")
            return False
            
        music_url = download_result["data"][0]["url"]
        print("✅ 获取到下载链接")
        return music_url
        
    except json.JSONDecodeError:
        print(f"❌ id: {music_id} 的响应不是合法JSON")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ id: {music_id} 请求失败，错误: {e}")
        return False
        
def get_music_info(music_id, interface):
    get_music_info_payload = {
        "id": music_id,
    }
    music_info = {}
    try:
        response = requests.post(f"https://wyapi-{interface}.toubiec.cn/api/music/detail", data=get_music_info_payload, verify=False)
        download_result = response.json()
        
        if download_result.get("code") != 200 or not download_result.get("data"):
            print(f"❌ id: {music_id} 获取元数据失败")
            print(download_result["msg"])
            return False
            
        music_info["name"] = download_result["data"]["name"]
        music_info["album"] = download_result["data"]["album"]
        music_info["singer"] = download_result["data"]["singer"]
        music_info["picimg"] = download_result["data"]["picimg"]
        
        print("✅ 元数据获取成功")
        return music_info
        
    except json.JSONDecodeError:
        print(f"❌ id: {music_id} 的响应不是合法JSON")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ id: {music_id} 请求失败，错误: {e}")
        return False
        
def get_album_info(album_id, interface):
    music_id_list = []
    get_album_info_payload = {
        "id": album_id,
    }
    
    try:
        response = requests.post(f"https://wyapi-{interface}.toubiec.cn/api/music/album", data=get_album_info_payload, verify=False)
        download_result = response.json()
        
        if download_result.get("code") != 200 or not download_result.get("data"):
            print(f"❌ id: {album_id} 获取专辑信息失败")
            print(download_result["msg"])
            return False
            
        music_id_list = [track["id"] for track in download_result["data"]["tracks"]]
        print("✅ 获取到专辑信息")
        return music_id_list
        
    except json.JSONDecodeError:
        print(f"❌ id: {album_id} 的响应不是合法JSON")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ id: {album_id} 请求失败，错误: {e}")
        return False
        
def get_playlist_info(playlist_id, interface):
    music_id_list = []
    get_playlist_info_payload = {
        "id": playlist_id,
    }
    
    try:
        response = requests.post(f"https://wyapi-{interface}.toubiec.cn/api/music/playlist", data=get_playlist_info_payload, verify=False)
        download_result = response.json()
        
        if download_result.get("code") != 200 or not download_result.get("data"):
            print(f"❌ id: {playlist_id} 获取歌单信息失败")
            print(download_result["msg"])
            return False
            
        music_id_list = [track["id"] for track in download_result["data"]["tracks"]]
        print("✅ 获取到歌单信息")
        return music_id_list
        
    except json.JSONDecodeError:
        print(f"❌ id: {playlist_id} 的响应不是合法JSON")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ id: {playlist_id} 请求失败，错误: {e}")
        return False
        
def get_music_lrc(music_id, music_name, interface, folder):
    get_music_lrc_payload = {
        "id": music_id,
    }
    
    try:
        response = requests.post(f"https://wyapi-{interface}.toubiec.cn/api/music/lyric", data=get_music_lrc_payload, verify=False)
        download_result = response.json()
        
        if download_result.get("code") != 200 or not download_result.get("data"):
            print(f"❌ id: {music_id} 获取歌曲歌词失败")
            print(download_result["msg"])
            return False
            
        lyric_data = download_result["data"]
        safe_name = re.sub(r'[\\/*?:"<>|]', "", music_name)
        
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = os.path.join(folder, f"{safe_name}_{music_id}.lrc")
        
        
        with open(filename, 'w', encoding='utf-8') as f:
            
            if lyric_data.get("lrc"):
                f.write("[原始歌词]\n")
                f.write(lyric_data["lrc"])
                f.write("\n\n")
            
            
            if lyric_data.get("tlyric"):
                f.write("[翻译歌词]\n")
                f.write(lyric_data["tlyric"])
                f.write("\n\n")
            
            
            if lyric_data.get("romalrc"):
                f.write("[罗马音歌词]\n")
                f.write(lyric_data["romalrc"])
                f.write("\n\n")
            
            
            if lyric_data.get("klyric"):
                f.write("[KTV歌词]\n")
                f.write(lyric_data["klyric"])
                f.write("\n\n")
        
        print("✅ 歌词写入成功")
    except requests.exceptions.RequestException as e:
        print(f"❌ id: {music_id} 请求失败: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ id: {music_id} JSON解析失败: {e}")
        return False
    except KeyError as e:
        print(f"❌ id: {music_id} 数据格式错误，缺少字段: {e}")
        return False
    except Exception as e:
        print(f"❌ id: {music_id} 未知错误: {e}")
        return False
        
def search_music(key, page, interface):
    music_id_list = []
    search_music_payload = {
        "keywords": key,
        "page": page,
    }
    
    search_next_music_payload = {
        "keywords": key,
        "page": page + 1,
    }
    
    try:
        response = requests.post(f"https://wyapi-{interface}.toubiec.cn/api/music/search", data=search_music_payload, verify=False)
        download_result = response.json()
        
        response_next = requests.post(f"https://wyapi-{interface}.toubiec.cn/api/music/search", data=search_next_music_payload, verify=False)
        download_result_next = response_next.json()
        
        if download_result_next["data"]["total"] == 0:
            music_id_list.append(False)
        else:
            music_id_list.append(True)
            
        if download_result.get("code") != 200 or not download_result.get("data"):
            print(f"❌ key: {key} 搜索失败")
            print(download_result["msg"])
            return False
        music_id_list.append(download_result["data"]["total"])
        for i, song in enumerate(download_result["data"]["songs"]):
            print(f"{i+1}. {song['name']} - {song['artists']} - {song['album']}")
            music_id_list.append(song["id"]) 
        return music_id_list
        
    except json.JSONDecodeError:
        print(f"❌ key: {key} 的响应不是合法JSON")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ key: {key} 请求失败，错误: {e}")
        return False
        
