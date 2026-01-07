import requests 
import json 
import os 
import time 
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

# 日志颜色
LOG_COLORS = {
    "DEBUG": "\033[90m",     # 灰色
    "INFO": "\033[94m",      # 蓝色
    "SUCCESS": "\033[92m",   # 绿色
    "WARNING": "\033[93m",   # 黄色
    "ERROR": "\033[91m",     # 红色
    "END": "\033[0m"         # 重置颜色
}

def log(level: str, message: str, module: str = "API2"):
    """API2日志函数"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = LOG_COLORS.get(level.upper(), LOG_COLORS["INFO"])
    print(f"{color}[{timestamp}] [{module:8}] {message}{LOG_COLORS['END']}")

def get_music(music_id: str, level_name: str, folder: str,
              max_retries: int = 3, timeout: int = 30, verify_ssl: bool = False) -> Optional[Dict[str, Any]]:
    """获取音乐信息和URL"""
    headers = {
        "referer": "https://dm.jfjt.cc/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    url_payload = {"id": music_id, "level": level_name}
    info_payload = {"id": music_id, "level": level_name, "type": "json"}
    
    for attempt in range(max_retries):
        try:
            log("INFO", f"获取音乐信息 (尝试 {attempt+1}/{max_retries}): id={music_id}, 音质={level_name}")
            
            # 获取音乐URL
            response_url = requests.post(
                "https://dm.jfjt.cc/Song_V1", 
                data=url_payload, 
                headers=headers, 
                verify=verify_ssl,
                timeout=timeout
            )
            download_result_url = response_url.json()
            
            if download_result_url.get("status") != 200 or not download_result_url.get("data"):
                log("ERROR", f"获取URL失败: {download_result_url.get('message', '未知错误')}")
                return None
            
            # 获取音乐信息
            response_info = requests.post(
                "https://dm.jfjt.cc/Song_V1", 
                data=info_payload, 
                headers=headers, 
                verify=verify_ssl,
                timeout=timeout
            )
            download_result_info = response_info.json()
            
            if download_result_info.get("status") != 200 or not download_result_info.get("data"):
                log("ERROR", f"获取元数据失败: {download_result_info.get('message', '未知错误')}")
                return None
            
            # 解析数据
            url_data = download_result_url["data"]
            info_data = download_result_info["data"]
            
            music_info = {
                "url": url_data.get("url", ""),
                "type": url_data.get("type", ""),
                "quality_name": url_data.get("quality_name", ""),
                "size": url_data.get("size", 0),
                "album": info_data.get("al_name", "未知专辑"),
                "singer": info_data.get("ar_name", "未知歌手"),
                "name": info_data.get("name", "未知歌曲"),
                "picimg": info_data.get("pic", "")
            }
            
            log("SUCCESS", f"音乐获取成功: {music_info['name']} - {music_info['singer']}")
            
            # 保存歌词
            try:
                safe_name = re.sub(r'[\\/*?:"<>|]', "", music_info.get("name"))
                os.makedirs(folder, exist_ok=True)
                filename = os.path.join(folder, f"{safe_name}_{music_id}.lrc")
                
                with open(filename, 'w', encoding='utf-8') as f:
                    # 原始歌词
                    if info_data.get("lyric"):
                        f.write("[原始歌词]\n")
                        f.write(info_data["lyric"])
                        f.write("\n\n")
                    
                    # 翻译歌词
                    if info_data.get("tlyric"):
                        f.write("[翻译歌词]\n")
                        f.write(info_data["tlyric"])
                        f.write("\n\n")
                
                log("SUCCESS", "歌词写入成功")
                
            except Exception as lrc_error:
                log("WARNING", f"歌词保存失败: {lrc_error}")
            
            return music_info
            
        except requests.exceptions.Timeout:
            log("WARNING", f"请求超时 (尝试 {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(1)
        except requests.exceptions.RequestException as e:
            log("WARNING", f"网络错误: {e} (尝试 {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2)
        except json.JSONDecodeError as e:
            log("ERROR", f"JSON解析失败: {e}")
            return None
        except KeyError as e:
            log("ERROR", f"数据格式错误: {e}")
            return None
        except Exception as e:
            log("ERROR", f"未知错误: {e}")
            return None
    
    log("ERROR", "获取音乐信息失败，已达最大重试次数")
    return None

def get_playlist_info(playlist_id: str, 
                      max_retries: int = 3, timeout: int = 30, verify_ssl: bool = False) -> Optional[List[str]]:
    """获取歌单信息"""
    headers = {
        "referer": "https://dm.jfjt.cc/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    url = f"https://dm.jfjt.cc/Playlist?id={playlist_id}"
    music_id_list = []
    
    for attempt in range(max_retries):
        try:
            log("INFO", f"获取歌单信息 (尝试 {attempt+1}/{max_retries}): id={playlist_id}")
            
            response = requests.get(url, headers=headers, verify=verify_ssl, timeout=timeout)
            download_result = response.json()
            
            if download_result.get("status") != 200 or not download_result.get("data"):
                log("ERROR", f"获取歌单失败: {download_result.get('message', '未知错误')}")
                return None
            
            playlist_data = download_result["data"].get("playlist", {})
            tracks = playlist_data.get("tracks", [])
            music_id_list = [str(track.get("id", "")) for track in tracks if track.get("id")]
            
            log("SUCCESS", f"歌单信息获取成功: {len(music_id_list)} 首歌曲")
            return music_id_list
            
        except requests.exceptions.Timeout:
            log("WARNING", f"请求超时 (尝试 {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(1)
        except requests.exceptions.RequestException as e:
            log("WARNING", f"网络错误: {e} (尝试 {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2)
        except json.JSONDecodeError as e:
            log("ERROR", f"JSON解析失败: {e}")
            return None
        except KeyError as e:
            log("ERROR", f"数据格式错误: {e}")
            return None
        except Exception as e:
            log("ERROR", f"未知错误: {e}")
            return None
    
    log("ERROR", "获取歌单信息失败，已达最大重试次数")
    return None

def get_album_info(album_id: str, 
                   max_retries: int = 3, timeout: int = 30, verify_ssl: bool = False) -> Optional[List[str]]:
    """获取专辑信息"""
    headers = {
        "referer": "https://dm.jfjt.cc/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    url = f"https://dm.jfjt.cc/Album?id={album_id}"
    music_id_list = []
    
    for attempt in range(max_retries):
        try:
            log("INFO", f"获取专辑信息 (尝试 {attempt+1}/{max_retries}): id={album_id}")
            
            response = requests.get(url, headers=headers, verify=verify_ssl, timeout=timeout)
            download_result = response.json()
            
            if download_result.get("status") != 200 or not download_result.get("data"):
                log("ERROR", f"获取专辑失败: {download_result.get('message', '未知错误')}")
                return None
            
            album_data = download_result["data"].get("album", {})
            songs = album_data.get("songs", [])
            music_id_list = [str(song.get("id", "")) for song in songs if song.get("id")]
            
            log("SUCCESS", f"专辑信息获取成功: {len(music_id_list)} 首歌曲")
            return music_id_list
            
        except requests.exceptions.Timeout:
            log("WARNING", f"请求超时 (尝试 {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(1)
        except requests.exceptions.RequestException as e:
            log("WARNING", f"网络错误: {e} (尝试 {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2)
        except json.JSONDecodeError as e:
            log("ERROR", f"JSON解析失败: {e}")
            return None
        except KeyError as e:
            log("ERROR", f"数据格式错误: {e}")
            return None
        except Exception as e:
            log("ERROR", f"未知错误: {e}")
            return None
    
    log("ERROR", "获取专辑信息失败，已达最大重试次数")
    return None