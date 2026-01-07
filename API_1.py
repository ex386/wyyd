import requests 
import json 
import os 
import time 
import re
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime
from typing import Dict, Any, Optional, List

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 日志颜色
LOG_COLORS = {
    "DEBUG": "\033[90m",     # 灰色
    "INFO": "\033[94m",      # 蓝色
    "SUCCESS": "\033[92m",   # 绿色
    "WARNING": "\033[93m",   # 黄色
    "ERROR": "\033[91m",     # 红色
    "END": "\033[0m"         # 重置颜色
}

def log(level: str, message: str, module: str = "API1"):
    """API1日志函数"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = LOG_COLORS.get(level.upper(), LOG_COLORS["INFO"])
    print(f"{color}[{timestamp}] [{module:8}] {message}{LOG_COLORS['END']}")

def get_music_url(music_id: str, level_name: str, interface: int, 
                  max_retries: int = 3, timeout: int = 30, verify_ssl: bool = False) -> Optional[str]:
    """获取音乐下载URL"""
    url = f"https://wyapi-{interface}.toubiec.cn/api/music/url"
    payload = {"id": music_id, "level": level_name}
    
    for attempt in range(max_retries):
        try:
            log("INFO", f"获取音乐URL (尝试 {attempt+1}/{max_retries}): id={music_id}, 音质={level_name}")
            
            response = requests.post(url, data=payload, verify=verify_ssl, timeout=timeout)
            download_result = response.json()
            
            if download_result.get("code") != 200 or not download_result.get("data"):
                log("ERROR", f"获取下载链接失败: {download_result.get('msg', '未知错误')}")
                return None
            
            music_url = download_result["data"][0]["url"]
            log("SUCCESS", "获取下载链接成功")
            return music_url
            
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
        except Exception as e:
            log("ERROR", f"未知错误: {e}")
            return None
    
    log("ERROR", "获取音乐URL失败，已达最大重试次数")
    return None

def get_music_info(music_id: str, interface: int, 
                   max_retries: int = 3, timeout: int = 30, verify_ssl: bool = False) -> Optional[Dict[str, Any]]:
    """获取音乐信息"""
    url = f"https://wyapi-{interface}.toubiec.cn/api/music/detail"
    payload = {"id": music_id}
    music_info = {}
    
    for attempt in range(max_retries):
        try:
            log("INFO", f"获取音乐信息 (尝试 {attempt+1}/{max_retries}): id={music_id}")
            
            response = requests.post(url, data=payload, verify=verify_ssl, timeout=timeout)
            download_result = response.json()
            
            if download_result.get("code") != 200 or not download_result.get("data"):
                log("ERROR", f"获取元数据失败: {download_result.get('msg', '未知错误')}")
                return None
            
            data = download_result["data"]
            music_info["name"] = data.get("name", "未知歌曲")
            music_info["album"] = data.get("album", "未知专辑")
            music_info["singer"] = data.get("singer", "未知歌手")
            music_info["picimg"] = data.get("picimg", "")
            
            if not music_info["picimg"]:
                log("WARNING", "未获取到封面图片URL")
            
            log("SUCCESS", f"元数据获取成功: {music_info['name']} - {music_info['singer']}")
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
        except Exception as e:
            log("ERROR", f"未知错误: {e}")
            return None
    
    log("ERROR", "获取音乐信息失败，已达最大重试次数")
    return None

def get_album_info(album_id: str, interface: int, 
                   max_retries: int = 3, timeout: int = 30, verify_ssl: bool = False) -> Optional[List[str]]:
    """获取专辑信息"""
    url = f"https://wyapi-{interface}.toubiec.cn/api/music/album"
    payload = {"id": album_id}
    music_id_list = []
    
    for attempt in range(max_retries):
        try:
            log("INFO", f"获取专辑信息 (尝试 {attempt+1}/{max_retries}): id={album_id}")
            
            response = requests.post(url, data=payload, verify=verify_ssl, timeout=timeout)
            download_result = response.json()
            
            if download_result.get("code") != 200 or not download_result.get("data"):
                log("ERROR", f"获取专辑信息失败: {download_result.get('msg', '未知错误')}")
                return None
            
            tracks = download_result["data"].get("tracks", [])
            music_id_list = [str(track["id"]) for track in tracks if "id" in track]
            
            log("SUCCESS", f"获取到专辑信息: {len(music_id_list)} 首歌曲")
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

def get_playlist_info(playlist_id: str, interface: int, 
                      max_retries: int = 3, timeout: int = 30, verify_ssl: bool = False) -> Optional[List[str]]:
    """获取歌单信息"""
    url = f"https://wyapi-{interface}.toubiec.cn/api/music/playlist"
    payload = {"id": playlist_id}
    music_id_list = []
    
    for attempt in range(max_retries):
        try:
            log("INFO", f"获取歌单信息 (尝试 {attempt+1}/{max_retries}): id={playlist_id}")
            
            response = requests.post(url, data=payload, verify=verify_ssl, timeout=timeout)
            download_result = response.json()
            
            if download_result.get("code") != 200 or not download_result.get("data"):
                log("ERROR", f"获取歌单信息失败: {download_result.get('msg', '未知错误')}")
                return None
            
            tracks = download_result["data"].get("tracks", [])
            music_id_list = [str(track["id"]) for track in tracks if "id" in track]
            
            log("SUCCESS", f"获取到歌单信息: {len(music_id_list)} 首歌曲")
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

def get_music_lrc(music_id: str, music_name: str, interface: int, folder: str,
                  max_retries: int = 3, timeout: int = 30, verify_ssl: bool = False) -> bool:
    """获取音乐歌词"""
    url = f"https://wyapi-{interface}.toubiec.cn/api/music/lyric"
    payload = {"id": music_id}
    
    for attempt in range(max_retries):
        try:
            log("INFO", f"获取歌词 (尝试 {attempt+1}/{max_retries}): id={music_id}")
            
            response = requests.post(url, data=payload, verify=verify_ssl, timeout=timeout)
            download_result = response.json()
            
            if download_result.get("code") != 200 or not download_result.get("data"):
                log("ERROR", f"获取歌词失败: {download_result.get('msg', '未知错误')}")
                return False
            
            lyric_data = download_result["data"]
            safe_name = re.sub(r'[\\/*?:"<>|]', "", music_name)
            
            # 确保文件夹存在
            os.makedirs(folder, exist_ok=True)
            
            filename = os.path.join(folder, f"{safe_name}_{music_id}.lrc")
            
            with open(filename, 'w', encoding='utf-8') as f:
                # 原始歌词
                if lyric_data.get("lrc"):
                    f.write("[原始歌词]\n")
                    f.write(lyric_data["lrc"])
                    f.write("\n\n")
                
                # 翻译歌词
                if lyric_data.get("tlyric"):
                    f.write("[翻译歌词]\n")
                    f.write(lyric_data["tlyric"])
                    f.write("\n\n")
                
                # 罗马音歌词
                if lyric_data.get("romalrc"):
                    f.write("[罗马音歌词]\n")
                    f.write(lyric_data["romalrc"])
                    f.write("\n\n")
                
                # KTV歌词
                if lyric_data.get("klyric"):
                    f.write("[KTV歌词]\n")
                    f.write(lyric_data["klyric"])
                    f.write("\n\n")
            
            log("SUCCESS", "歌词写入成功")
            return True
            
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
            return False
        except IOError as e:
            log("ERROR", f"文件写入失败: {e}")
            return False
        except Exception as e:
            log("ERROR", f"未知错误: {e}")
            return False
    
    log("ERROR", "获取歌词失败，已达最大重试次数")
    return False

def search_music(key: str, page: int, interface: int,
                 max_retries: int = 3, timeout: int = 30, verify_ssl: bool = False) -> Optional[List]:
    """搜索音乐"""
    url = f"https://wyapi-{interface}.toubiec.cn/api/music/search"
    payload = {"keywords": key, "page": page}
    music_id_list = []
    
    for attempt in range(max_retries):
        try:
            log("INFO", f"搜索音乐 (尝试 {attempt+1}/{max_retries}): 关键词={key}, 页码={page}")
            
            response = requests.post(url, data=payload, verify=verify_ssl, timeout=timeout)
            download_result = response.json()
            
            if download_result.get("code") != 200 or not download_result.get("data"):
                log("ERROR", f"搜索失败: {download_result.get('msg', '未知错误')}")
                return None
            
            data = download_result["data"]
            songs = data.get("songs", [])
            
            # 检查是否有下一页
            next_page_payload = {"keywords": key, "page": page + 1}
            response_next = requests.post(url, data=next_page_payload, verify=verify_ssl, timeout=timeout)
            result_next = response_next.json()
            
            has_next_page = False
            if result_next.get("code") == 200 and result_next.get("data", {}).get("songs"):
                has_next_page = True
            
            # 构建结果列表
            music_id_list.append(has_next_page)  # 第一个元素表示是否有下一页
            music_id_list.append(data.get("total", 0))  # 第二个元素表示总结果数
            
            # 显示搜索结果
            print(f"\n{LOG_COLORS['INFO']}搜索结果 (第 {page} 页，共 {data.get('total', 0)} 条):{LOG_COLORS['END']}")
            print("-" * 80)
            
            for i, song in enumerate(songs):
                song_name = song.get("name", "未知歌曲")
                artists = song.get("artists", "未知歌手")
                album = song.get("album", "未知专辑")
                song_id = song.get("id", "")
                
                music_id_list.append(str(song_id))
                
                print(f"{i+1:3d}. {song_name[:30]:30} - {artists[:20]:20} - {album[:20]:20} (ID: {song_id})")
            
            print("-" * 80)
            
            log("SUCCESS", f"搜索成功: 找到 {len(songs)} 条结果")
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
        except Exception as e:
            log("ERROR", f"未知错误: {e}")
            return None
    
    log("ERROR", "搜索音乐失败，已达最大重试次数")
    return None