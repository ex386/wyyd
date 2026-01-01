import requests 
import json 
import os 
import time 
import re

def get_music(music_id, leval_name, folder):
    music_info = {}
    
    headers = {
        "referer": "https://dm.jfjt.cc/"
    }
    
    get_music_url_payload = {
        "id": music_id,
        "level": leval_name
    }
    
    get_music_info_payload = {
        "id": music_id,
        "level": leval_name,
        "type": "json"
    }
    
    try:
        response_url = requests.post("https://dm.jfjt.cc/Song_V1", data=get_music_url_payload, headers= headers)
        download_result_url = response_url.json()
        if download_result_url.get("status") != 200 or not download_result_url.get("data"):
            print(f"❌ id: {music_id} 获取URL失败")
            print(download_result_url["message"])
            return False
        
        music_info["url"] = download_result_url["data"]["url"]
        music_info["type"] = download_result_url["data"]["type"]
        music_info["quality_name"] = download_result_url["data"]["quality_name"]
        music_info["size"] = download_result_url["data"]["size"]
        
        response_info = requests.post("https://dm.jfjt.cc/Song_V1", data=get_music_info_payload, headers= headers)
        download_result_info = response_info.json()
        
        if download_result_info.get("status") != 200 or not download_result_info.get("data"):
            print(f"❌ id: {music_id} 获取元数据失败")
            print(download_result_info["message"])
            return False
        
        music_info["album"] = download_result_info["data"]["al_name"]
        music_info["singer"] = download_result_info["data"]["ar_name"]
        music_info["name"] = download_result_info["data"]["name"]
        music_info["picimg"] = download_result_info["data"]["pic"]
        
        print("✅音乐获取成功")
        
        safe_name = re.sub(r'[\\/*?:"<>|]', "", music_info.get("name"))
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = os.path.join(folder, f"{safe_name}_{music_id}.lrc")
        
        lyric_data = download_result_info["data"]
        
        with open(filename, 'w', encoding='utf-8') as f:
            
            if lyric_data.get("lyric"):
                f.write("[原始歌词]\n")
                f.write(lyric_data["lyric"])
                f.write("\n\n")
            
            
            if lyric_data.get("tlyric"):
                f.write("[翻译歌词]\n")
                f.write(lyric_data["tlyric"])
                f.write("\n\n")
        
        print("✅歌词写入成功")
        return music_info
        
    except json.JSONDecodeError:
        print(f"❌ id: {music_id} 的响应不是合法JSON")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ id: {music_id} 请求失败，错误: {e}")
        return False
        
def get_playlist_info(playlist_id):
    music_id_list = []
    
    headers = {
        "referer": "https://dm.jfjt.cc/"
    }
    
    try:
        response = requests.get(f"https://dm.jfjt.cc/Playlist?id={playlist_id}", headers= headers)
        download_result = response.json()
        if download_result.get("status") != 200 or not download_result.get("data"):
            print(f"❌ id: {playlist_id} 获取歌单失败")
            print(download_result["message"])
            return False
        
        music_id_list = [track["id"] for track in download_result["data"]["playlist"]["tracks"]]
        print("✅歌单信息获取成功")
        
        return music_id_list
        
    except json.JSONDecodeError:
        print(f"❌ id: {playlist_id} 的响应不是合法JSON")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ id: {playlist_id} 请求失败，错误: {e}")
        return False
        
def get_album_info(album_id):
    music_id_list = []
    
    headers = {
        "referer": "https://dm.jfjt.cc/"
    }
    
    try:
        response = requests.get(f"https://dm.jfjt.cc/Album?id={album_id}", headers= headers)
        download_result = response.json()
        if download_result.get("status") != 200 or not download_result.get("data"):
            print(f"❌ id: {album_id} 获取专辑失败")
            print(download_result["message"])
            return False
        
        music_id_list = [track["id"] for track in download_result["data"]["album"]["songs"]]
        print("✅专辑信息获取成功")
        
        return music_id_list
        
    except json.JSONDecodeError:
        print(f"❌ id: {album_id} 的响应不是合法JSON")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ id: {album_id} 请求失败，错误: {e}")
        return False
        
