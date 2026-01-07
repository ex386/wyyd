import API_1
import API_2
import os
import json
import re
import requests
import sys
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen.flac import FLAC, Picture
from datetime import datetime
from typing import Dict, Any, Optional, List

# ============= 日志系统配置 =============
LOG_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, SUCCESS, WARNING, ERROR
    "to_file": True,
    "log_file": "music_downloader.log",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 3
}

LOG_COLORS = {
    "DEBUG": "\033[90m",     # 灰色
    "INFO": "\033[94m",      # 蓝色
    "SUCCESS": "\033[92m",   # 绿色
    "WARNING": "\033[93m",   # 黄色
    "ERROR": "\033[91m",     # 红色
    "END": "\033[0m"         # 重置颜色
}

# 全局日志函数
def setup_logger():
    """设置日志系统"""
    import logging
    import logging.handlers
    
    logger = logging.getLogger('MusicDownloader')
    logger.setLevel(getattr(logging, LOG_CONFIG['level']))
    
    # 清除现有处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果启用）
    if LOG_CONFIG['to_file']:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                LOG_CONFIG['log_file'],
                maxBytes=LOG_CONFIG['max_file_size'],
                backupCount=LOG_CONFIG['backup_count'],
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"无法创建日志文件: {e}")
    
    return logger

# 创建日志器
logger = setup_logger()

def log(level: str, message: str, module: str = "MAIN"):
    """自定义日志函数"""
    # 过滤级别
    level_priority = {"DEBUG": 0, "INFO": 1, "SUCCESS": 1, "WARNING": 2, "ERROR": 3}
    config_priority = level_priority.get(LOG_CONFIG['level'].upper(), 1)
    msg_priority = level_priority.get(level.upper(), 1)
    
    if msg_priority < config_priority:
        return
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = LOG_COLORS.get(level.upper(), LOG_COLORS["INFO"])
    
    # 构建日志消息
    log_msg = f"[{timestamp}] [{module:8}] {message}"
    
    # 输出到控制台（带颜色）
    if level.upper() == "SUCCESS":
        level_display = "SUCCESS"
    else:
        level_display = level.upper()
    
    colored_msg = f"{color}[{timestamp}] [{module:8}] {message}{LOG_COLORS['END']}"
    print(colored_msg)
    
    # 输出到日志文件（无颜色）
    if LOG_CONFIG['to_file']:
        if level.upper() == "SUCCESS":
            logger.info(f"[{module}] {message}")
        else:
            getattr(logger, level.lower(), logger.info)(f"[{module}] {message}")

def print_header(text: str):
    """打印标题"""
    border = "=" * 60
    print(f"\n{LOG_COLORS['INFO']}{border}")
    print(f"{text.center(60)}")
    print(f"{border}{LOG_COLORS['END']}")

def print_divider():
    """打印分隔线"""
    print(f"{LOG_COLORS['DEBUG']}{'-' * 60}{LOG_COLORS['END']}")

# ============= 配置系统 =============
DEFAULT_SETTINGS = {
    "interface": 1,
    "level_name": 3,  # lossless 默认
    "folder": "Music",
    "max_retries": 3,
    "timeout": 30,
    "verify_ssl": False
}

VALID_SETTINGS = {
    "interface": {
        "type": int,
        "range": [1, 2, 3],
        "description": "接口选择: 1=接口1, 2=接口2, 3=接口3(不支持搜索)"
    },
    "level_name": {
        "type": int,
        "range": [1, 2, 3, 4, 5, 6, 7],
        "description": "音质等级: 1=standard, 2=exhigh, 3=lossless, 4=hires, 5=jyeffect, 6=sky, 7=jymaster"
    },
    "folder": {
        "type": str,
        "description": "下载文件夹路径"
    },
    "max_retries": {
        "type": int,
        "range": [1, 10],
        "description": "最大重试次数"
    },
    "timeout": {
        "type": int,
        "range": [10, 300],
        "description": "请求超时时间(秒)"
    },
    "verify_ssl": {
        "type": bool,
        "description": "是否验证SSL证书"
    }
}

level_name = ["standard", "exhigh", "lossless", "hires", "jyeffect", "sky", "jymaster"]

def validate_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """验证并修复设置"""
    validated = DEFAULT_SETTINGS.copy()
    
    for key, value in settings.items():
        if key in VALID_SETTINGS:
            validator = VALID_SETTINGS[key]
            
            # 类型检查
            try:
                if validator["type"] == int:
                    validated_value = int(value)
                elif validator["type"] == bool:
                    if isinstance(value, str):
                        validated_value = value.lower() in ['true', '1', 'yes', 'y']
                    else:
                        validated_value = bool(value)
                elif validator["type"] == str:
                    validated_value = str(value).strip()
                    if not validated_value:
                        raise ValueError(f"{key} 不能为空")
                else:
                    validated_value = value
            except (ValueError, TypeError) as e:
                log("WARNING", f"设置 {key} 的值 '{value}' 无效，使用默认值 {DEFAULT_SETTINGS[key]}: {e}")
                validated_value = DEFAULT_SETTINGS[key]
            
            # 范围检查
            if "range" in validator:
                if validated_value not in validator["range"]:
                    log("WARNING", f"设置 {key} 的值 {validated_value} 超出范围 {validator['range']}，使用默认值 {DEFAULT_SETTINGS[key]}")
                    validated_value = DEFAULT_SETTINGS[key]
            
            validated[key] = validated_value
        else:
            log("WARNING", f"忽略未知设置项: {key}")
    
    # 确保文件夹路径存在
    if not os.path.exists(validated["folder"]):
        try:
            os.makedirs(validated["folder"], exist_ok=True)
            log("INFO", f"创建下载文件夹: {validated['folder']}")
        except Exception as e:
            log("ERROR", f"无法创建文件夹 {validated['folder']}: {e}")
            validated["folder"] = DEFAULT_SETTINGS["folder"]
            os.makedirs(validated["folder"], exist_ok=True)
    
    return validated

def load_settings() -> Dict[str, Any]:
    """加载设置文件"""
    settings_file = "settings.json"
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            
            validated_settings = validate_settings(loaded_settings)
            
            # 如果设置被修复，保存修复后的版本
            if loaded_settings != validated_settings:
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(validated_settings, f, indent=4, ensure_ascii=False)
                log("INFO", "设置文件已修复并保存")
            
            log("SUCCESS", f"设置文件加载成功: {settings_file}")
            return validated_settings
            
        except json.JSONDecodeError as e:
            log("ERROR", f"设置文件格式错误: {e}")
            log("INFO", "使用默认设置")
            return DEFAULT_SETTINGS.copy()
        except Exception as e:
            log("ERROR", f"加载设置文件失败: {e}")
            return DEFAULT_SETTINGS.copy()
    else:
        # 创建默认设置文件
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_SETTINGS, f, indent=4, ensure_ascii=False)
            log("INFO", f"创建默认设置文件: {settings_file}")
        except Exception as e:
            log("ERROR", f"无法创建设置文件: {e}")
        
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]):
    """保存设置到文件"""
    try:
        validated_settings = validate_settings(settings)
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(validated_settings, f, indent=4, ensure_ascii=False)
        log("SUCCESS", "设置已保存")
        return validated_settings
    except Exception as e:
        log("ERROR", f"保存设置失败: {e}")
        return settings

# ============= 下载函数 =============
def API_1_download(music_id: str, settings: Dict[str, Any]) -> bool:
    """使用API1下载音乐"""
    log("INFO", f"开始处理歌曲 (接口1): {music_id}")
    
    # 获取音乐URL
    music_url = API_1.get_music_url(
        music_id, 
        level_name[settings["level_name"]-1], 
        settings["interface"],
        max_retries=settings["max_retries"],
        timeout=settings["timeout"],
        verify_ssl=settings["verify_ssl"]
    )
    
    if not music_url:
        log("ERROR", f"获取下载链接失败: {music_id}")
        return False
    
    # 确定文件类型
    if "mp3" in music_url:
        file_type = "mp3"
    elif "flac" in music_url:
        file_type = "flac"
    else:
        file_type = "unknown"
        log("WARNING", f"未知文件类型，URL: {music_url[:100]}...")
    
    # 获取音乐信息
    music_info = API_1.get_music_info(
        music_id, 
        settings["interface"],
        max_retries=settings["max_retries"],
        timeout=settings["timeout"],
        verify_ssl=settings["verify_ssl"]
    )
    
    if not music_info:
        log("ERROR", f"获取歌曲信息失败: {music_id}")
        return False
    
    # 处理文件名
    safe_name = re.sub(r'[\\/*?:"<>|]', "", music_info["name"])
    filename = f"{safe_name}_{music_id}.{file_type}"
    log("DEBUG", f"文件名: {filename}")
    
    # 下载音频文件
    filepath = download(
        music_url, 
        filename, 
        settings["folder"],
        max_retries=settings["max_retries"],
        timeout=settings["timeout"]
    )
    
    if not filepath:
        return False
    
    # 下载封面图片
    pngname = f"{safe_name}_{music_id}.png"
    pngpath = download(
        music_info["picimg"], 
        pngname, 
        settings["folder"],
        max_retries=settings["max_retries"],
        timeout=settings["timeout"]
    )
    
    # 写入元数据
    if write_metadata(file_type, filepath, pngpath, music_info):
        log("SUCCESS", f"歌曲处理完成: {music_info['name']}")
    else:
        log("ERROR", f"写入元数据失败: {music_info['name']}")
        return False
    
    # 下载歌词
    API_1.get_music_lrc(
        music_id, 
        music_info["name"], 
        settings["interface"], 
        settings["folder"],
        max_retries=settings["max_retries"],
        timeout=settings["timeout"],
        verify_ssl=settings["verify_ssl"]
    )
    
    return True

def API_2_download(music_id: str, settings: Dict[str, Any]) -> bool:
    """使用API2下载音乐"""
    log("INFO", f"开始处理歌曲 (接口2): {music_id}")
    
    # 获取音乐信息（API2整合了信息获取）
    music_info = API_2.get_music(
        music_id, 
        level_name[settings["level_name"]-1], 
        settings["folder"],
        max_retries=settings["max_retries"],
        timeout=settings["timeout"],
        verify_ssl=settings["verify_ssl"]
    )
    
    if not music_info:
        log("ERROR", f"获取歌曲信息失败: {music_id}")
        return False
    
    # 处理文件名
    safe_name = re.sub(r'[\\/*?:"<>|]', "", music_info["name"])
    filename = f"{safe_name}_{music_id}.{music_info['type']}"
    log("DEBUG", f"文件名: {filename}")
    
    # 下载音频文件
    filepath = download(
        music_info["url"], 
        filename, 
        settings["folder"],
        max_retries=settings["max_retries"],
        timeout=settings["timeout"]
    )
    
    if not filepath:
        return False
    
    # 下载封面图片
    pngname = f"{safe_name}_{music_id}.png"
    pngpath = download(
        music_info["picimg"], 
        pngname, 
        settings["folder"],
        max_retries=settings["max_retries"],
        timeout=settings["timeout"]
    )
    
    # 写入元数据
    if write_metadata(music_info["type"], filepath, pngpath, music_info):
        log("SUCCESS", f"歌曲处理完成: {music_info['name']}")
        return True
    
    return False

def download(url: str, filename: str, folder: str, max_retries: int = 3, timeout: int = 30) -> Optional[str]:
    """下载文件"""
    for attempt in range(max_retries):
        try:
            # 确保文件夹存在
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
                log("DEBUG", f"创建文件夹: {folder}")
            
            log("INFO", f"开始下载 ({attempt+1}/{max_retries}): {filename}")
            log("DEBUG", f"下载URL: {url[:80]}...")
            
            # 发送请求
            response = requests.get(
                url, 
                stream=True, 
                verify=False,
                timeout=timeout
            )
            
            filepath = os.path.join(folder, filename)
            
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                start_time = datetime.now()
                
                # 检查文件是否已存在（部分下载）
                if os.path.exists(filepath):
                    existing_size = os.path.getsize(filepath)
                    if 0 < existing_size < total_size:
                        log("INFO", f"发现部分下载的文件，继续下载...")
                        downloaded = existing_size
                        headers = {'Range': f'bytes={existing_size}-'}
                        response = requests.get(url, headers=headers, stream=True, verify=False, timeout=timeout)
                        mode = 'ab'
                    else:
                        mode = 'wb'
                else:
                    mode = 'wb'
                
                with open(filepath, mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            f.flush()
                            downloaded += len(chunk)
                            
                            # 显示进度
                            if total_size > 0:
                                progress = downloaded / total_size * 100
                                elapsed = (datetime.now() - start_time).total_seconds()
                                
                                # 计算速度
                                if elapsed > 0:
                                    speed = downloaded / elapsed / 1024  # KB/s
                                    speed_text = f"{speed:.1f}KB/s"
                                else:
                                    speed_text = "计算中..."
                                
                                # 进度条
                                bar_length = 40
                                filled = int(bar_length * downloaded // total_size)
                                bar = '█' * filled + '▒' * (bar_length - filled)
                                
                                # 进度信息
                                size_mb = downloaded / 1024 / 1024
                                total_mb = total_size / 1024 / 1024
                                
                                print(f"\r{LOG_COLORS['INFO']}[下载] [{bar}] {progress:6.1f}% ({size_mb:.1f}/{total_mb:.1f}MB) @ {speed_text}{LOG_COLORS['END']}", end="")
                
                elapsed = (datetime.now() - start_time).total_seconds()
                log("SUCCESS", f"下载完成: {filename} ({downloaded/1024/1024:.1f}MB, {elapsed:.1f}s)")
                return filepath
                
            else:
                log("WARNING", f"下载失败，状态码: {response.status_code} (尝试 {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                
        except requests.exceptions.Timeout:
            log("WARNING", f"下载超时 (尝试 {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
        except requests.exceptions.RequestException as e:
            log("WARNING", f"网络错误: {e} (尝试 {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
        except Exception as e:
            log("ERROR", f"下载错误: {e}")
            break
    
    log("ERROR", f"下载失败: {filename}")
    return None

def write_metadata(filetype: str, filepath: str, pngpath: Optional[str], music_info: Dict[str, Any]) -> bool:
    """写入音频文件元数据"""
    try:
        if not os.path.exists(filepath):
            log("ERROR", f"音频文件不存在: {filepath}")
            return False
        
        log("INFO", f"写入元数据: {os.path.basename(filepath)}")
        
        if filetype.lower() == 'mp3':
            try:
                audio = MP3(filepath, ID3=ID3)
                
                if audio.tags is None:
                    audio.tags = ID3()
                    log("DEBUG", "创建新的ID3标签")
                
                # 写入文本标签
                audio.tags.add(TIT2(encoding=3, text=music_info.get('name', '未知歌曲')))
                audio.tags.add(TPE1(encoding=3, text=music_info.get('singer', '未知歌手')))
                audio.tags.add(TALB(encoding=3, text=music_info.get('album', '未知专辑')))
                log("DEBUG", f"添加文本标签: {music_info.get('name', '未知歌曲')}")
                
                # 写入封面图片
                if pngpath and os.path.exists(pngpath):
                    try:
                        with open(pngpath, 'rb') as img:
                            audio.tags.add(APIC(
                                encoding=3,
                                mime='image/png',
                                type=3,
                                desc='Cover',
                                data=img.read()
                            ))
                        log("DEBUG", "添加封面图片")
                    except Exception as img_error:
                        log("WARNING", f"添加封面图片失败: {img_error}")
                
                audio.save()
                log("SUCCESS", "MP3元数据写入成功")
                
            except Exception as mp3_error:
                log("ERROR", f"处理MP3文件失败: {mp3_error}")
                return False
                
        elif filetype.lower() == 'flac':
            try:
                audio = FLAC(filepath)
                
                # 写入文本标签
                audio['title'] = [music_info.get('name', '未知歌曲')]
                audio['artist'] = [music_info.get('singer', '未知歌手')]
                audio['album'] = [music_info.get('album', '未知专辑')]
                log("DEBUG", f"添加文本标签: {music_info.get('name', '未知歌曲')}")
                
                # 写入封面图片
                if pngpath and os.path.exists(pngpath):
                    try:
                        picture = Picture()
                        picture.type = 3
                        picture.mime = 'image/png'
                        
                        with open(pngpath, 'rb') as f:
                            picture.data = f.read()
                        
                        audio.clear_pictures()
                        audio.add_picture(picture)
                        log("DEBUG", "添加封面图片")
                    except Exception as img_error:
                        log("WARNING", f"添加封面图片失败: {img_error}")
                
                audio.save()
                log("SUCCESS", "FLAC元数据写入成功")
                
            except Exception as flac_error:
                log("ERROR", f"处理FLAC文件失败: {flac_error}")
                return False
        else:
            log("WARNING", f"不支持的文件类型: {filetype}")
            return False
        
        # 清理临时图片文件
        if pngpath and os.path.exists(pngpath):
            try:
                os.remove(pngpath)
                log("DEBUG", f"清理临时文件: {os.path.basename(pngpath)}")
            except Exception as cleanup_error:
                log("WARNING", f"清理临时文件失败: {cleanup_error}")
        
        return True
        
    except Exception as e:
        log("ERROR", f"写入元数据时出错: {e}")
        return False

# ============= 主程序 =============
def main():
    """主程序入口"""
    print_header("音乐下载器 v1.0")
    
    # 加载设置
    

def edit_settings(current_settings: Dict[str, Any]) -> Dict[str, Any]:
    """修改设置"""
    print_header("修改设置")
    
    while True:
        print(f"\n{LOG_COLORS['INFO']}当前设置:{LOG_COLORS['END']}")
        for key, value in current_settings.items():
            if key in VALID_SETTINGS:
                desc = VALID_SETTINGS[key]["description"]
                print(f"  {key}: {value} ({desc})")
        
        print(f"\n{LOG_COLORS['INFO']}请选择要修改的项:{LOG_COLORS['END']}")
        print(" 0. 保存并返回")
        for i, key in enumerate(VALID_SETTINGS.keys(), 1):
            print(f" {i}. {key}")
        
        choice = input(f"{LOG_COLORS['INFO']}输入选择: {LOG_COLORS['END']}").strip()
        
        if choice == "0":
            return save_settings(current_settings)
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(VALID_SETTINGS):
                key = list(VALID_SETTINGS.keys())[choice_num - 1]
                validator = VALID_SETTINGS[key]
                
                print(f"\n修改 {key}:")
                print(f"当前值: {current_settings.get(key, '未设置')}")
                print(f"描述: {validator['description']}")
                
                if "range" in validator:
                    print(f"有效范围: {validator['range']}")
                
                new_value = input(f"{LOG_COLORS['INFO']}输入新值: {LOG_COLORS['END']}").strip()
                
                # 验证和转换值
                try:
                    if validator["type"] == int:
                        converted_value = int(new_value)
                    elif validator["type"] == bool:
                        converted_value = new_value.lower() in ['true', '1', 'yes', 'y', '是']
                    else:
                        converted_value = new_value
                    
                    # 范围检查
                    if "range" in validator:
                        if converted_value not in validator["range"]:
                            log("ERROR", f"值 {converted_value} 超出范围 {validator['range']}")
                            continue
                    
                    current_settings[key] = converted_value
                    log("SUCCESS", f"{key} 已修改为: {converted_value}")
                    
                except ValueError:
                    log("ERROR", f"无效的值: {new_value}")
                    continue
                    
            else:
                log("ERROR", "无效的选择")
        except ValueError:
            log("ERROR", "请输入数字")

def single_download(settings: Dict[str, Any]):
    """单曲下载"""
    print_header("单曲下载")
    
    while True:
        music_id = input(f"{LOG_COLORS['INFO']}请输入歌曲ID或URL (输入0返回):{LOG_COLORS['END']} ").strip()
        
        if music_id == "0":
            break
        
        if not music_id:
            log("WARNING", "输入不能为空")
            continue
        
        # 从URL中提取ID
        if "=" in music_id:
            parts = music_id.split("=")
            if len(parts) > 1:
                music_id = parts[-1]
                log("DEBUG", f"从URL提取ID: {music_id}")
        
        # 下载歌曲
        success = False
        if settings["interface"] != 3:
            success = API_1_download(music_id, settings)
        else:
            success = API_2_download(music_id, settings)
        
        if success:
            log("SUCCESS", "单曲下载完成")
        else:
            log("ERROR", "单曲下载失败")
        
        print_divider()

def batch_download(settings: Dict[str, Any]):
    """批量下载"""
    print_header("批量下载")
    
    while True:
        music_id_list = input(f"{LOG_COLORS['INFO']}请输入歌曲ID，用空格分隔 (输入0返回):{LOG_COLORS['END']} ").strip()
        
        if music_id_list == "0":
            break
        
        if not music_id_list:
            log("WARNING", "输入不能为空")
            continue
        
        music_ids = [mid.strip() for mid in music_id_list.split() if mid.strip()]
        
        if not music_ids:
            log("WARNING", "未检测到有效的歌曲ID")
            continue
        
        log("INFO", f"开始批量下载 {len(music_ids)} 首歌曲")
        
        success_count = 0
        for i, music_id in enumerate(music_ids, 1):
            log("INFO", f"处理第 {i}/{len(music_ids)} 首歌曲: {music_id}")
            
            if settings["interface"] != 3:
                if API_1_download(music_id, settings):
                    success_count += 1
            else:
                if API_2_download(music_id, settings):
                    success_count += 1
        
        log("SUCCESS", f"批量下载完成: 成功 {success_count}/{len(music_ids)} 首")
        print_divider()

def playlist_download(settings: Dict[str, Any]):
    """歌单下载"""
    print_header("歌单下载")
    
    while True:
        playlist_id = input(f"{LOG_COLORS['INFO']}请输入歌单ID或链接 (输入0返回):{LOG_COLORS['END']} ").strip()
        
        if playlist_id == "0":
            break
        
        if not playlist_id:
            log("WARNING", "输入不能为空")
            continue
        
        # 从URL中提取ID
        if "=" in playlist_id:
            parts = playlist_id.split("=")
            if len(parts) > 1:
                playlist_id = parts[-1]
                log("DEBUG", f"从URL提取歌单ID: {playlist_id}")
        
        # 获取歌单信息
        music_id_list = []
        if settings["interface"] != 3:
            music_id_list = API_1.get_playlist_info(
                playlist_id, 
                settings["interface"],
                max_retries=settings["max_retries"],
                timeout=settings["timeout"],
                verify_ssl=settings["verify_ssl"]
            )
        else:
            music_id_list = API_2.get_playlist_info(
                playlist_id,
                max_retries=settings["max_retries"],
                timeout=settings["timeout"],
                verify_ssl=settings["verify_ssl"]
            )
        
        if not music_id_list:
            log("ERROR", "获取歌单信息失败")
            continue
        
        log("INFO", f"歌单包含 {len(music_id_list)} 首歌曲")
        
        # 询问用户是否下载
        confirm = input(f"{LOG_COLORS['WARNING']}是否下载这 {len(music_id_list)} 首歌曲? (y/n): {LOG_COLORS['END']}").strip().lower()
        
        if confirm not in ['y', 'yes', '是']:
            log("INFO", "已取消下载")
            continue
        
        # 下载歌曲
        success_count = 0
        for i, music_id in enumerate(music_id_list, 1):
            log("INFO", f"处理第 {i}/{len(music_id_list)} 首歌曲")
            
            if settings["interface"] != 3:
                if API_1_download(music_id, settings):
                    success_count += 1
            else:
                if API_2_download(music_id, settings):
                    success_count += 1
        
        log("SUCCESS", f"歌单下载完成: 成功 {success_count}/{len(music_id_list)} 首")
        print_divider()

def album_download(settings: Dict[str, Any]):
    """专辑下载"""
    print_header("专辑下载")
    
    while True:
        album_id = input(f"{LOG_COLORS['INFO']}请输入专辑ID或链接 (输入0返回):{LOG_COLORS['END']} ").strip()
        
        if album_id == "0":
            break
        
        if not album_id:
            log("WARNING", "输入不能为空")
            continue
        
        # 从URL中提取ID
        if "=" in album_id:
            parts = album_id.split("=")
            if len(parts) > 1:
                album_id = parts[-1]
                log("DEBUG", f"从URL提取专辑ID: {album_id}")
        
        # 获取专辑信息
        music_id_list = []
        if settings["interface"] != 3:
            music_id_list = API_1.get_album_info(
                album_id, 
                settings["interface"],
                max_retries=settings["max_retries"],
                timeout=settings["timeout"],
                verify_ssl=settings["verify_ssl"]
            )
        else:
            music_id_list = API_2.get_album_info(
                album_id,
                max_retries=settings["max_retries"],
                timeout=settings["timeout"],
                verify_ssl=settings["verify_ssl"]
            )
        
        if not music_id_list:
            log("ERROR", "获取专辑信息失败")
            continue
        
        log("INFO", f"专辑包含 {len(music_id_list)} 首歌曲")
        
        # 询问用户是否下载
        confirm = input(f"{LOG_COLORS['WARNING']}是否下载这 {len(music_id_list)} 首歌曲? (y/n): {LOG_COLORS['END']}").strip().lower()
        
        if confirm not in ['y', 'yes', '是']:
            log("INFO", "已取消下载")
            continue
        
        # 下载歌曲
        success_count = 0
        for i, music_id in enumerate(music_id_list, 1):
            log("INFO", f"处理第 {i}/{len(music_id_list)} 首歌曲")
            
            if settings["interface"] != 3:
                if API_1_download(music_id, settings):
                    success_count += 1
            else:
                if API_2_download(music_id, settings):
                    success_count += 1
        
        log("SUCCESS", f"专辑下载完成: 成功 {success_count}/{len(music_id_list)} 首")
        print_divider()

def search_download(settings: Dict[str, Any]):
    """搜索下载"""
    print_header("搜索下载")
    
    key = input(f"{LOG_COLORS['INFO']}请输入搜索关键词:{LOG_COLORS['END']} ").strip()
    
    if not key:
        log("WARNING", "搜索关键词不能为空")
        return
    
    page = 1
    
    while True:
        log("INFO", f"搜索: '{key}' (第 {page} 页)")
        
        music_id_list = API_1.search_music(
            key, 
            page, 
            settings["interface"],
            max_retries=settings["max_retries"],
            timeout=settings["timeout"],
            verify_ssl=settings["verify_ssl"]
        )
        
        if not music_id_list:
            log("WARNING", "搜索结果为空")
            break
        
        print_divider()
        
        # 显示操作说明
        print(f"{LOG_COLORS['DEBUG']}操作说明: 输入歌曲序号下载，多个用空格分隔")
        print(f"           r=下一页, l=上一页, 0=返回{LOG_COLORS['END']}")
        print_divider()
        
        user_input = input(f"{LOG_COLORS['INFO']}请输入操作:{LOG_COLORS['END']} ").strip()
        
        if user_input.lower() == "r":
            if len(music_id_list) > 0 and music_id_list[0]:
                page += 1
            else:
                log("WARNING", "已经是最后一页")
            continue
        elif user_input.lower() == "l":
            if page > 1:
                page -= 1
            continue
        elif user_input == "0":
            break
        elif user_input:
            id_list = user_input.split()
            success_count = 0
            
            for music_id in id_list:
                if music_id.strip():
                    if API_1_download(music_id.strip(), settings):
                        success_count += 1
            
            log("SUCCESS", f"搜索下载完成: 成功 {success_count}/{len(id_list)} 首")
        else:
            log("WARNING", "请输入有效的指令或序号")

def view_logs():
    """查看日志"""
    print_header("查看日志")
    
    if not os.path.exists(LOG_CONFIG['log_file']):
        log("WARNING", "日志文件不存在")
        return
    
    try:
        with open(LOG_CONFIG['log_file'], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            log("INFO", "日志文件为空")
            return
        
        # 显示最后50行
        print(f"\n{LOG_COLORS['INFO']}显示最后50行日志:{LOG_COLORS['END']}")
        print_divider()
        
        for line in lines[-50:]:
            print(line.strip())
        
        print_divider()
        print(f"{LOG_COLORS['INFO']}日志文件: {LOG_CONFIG['log_file']}")
        print(f"总行数: {len(lines)}{LOG_COLORS['END']}")
        
        # 操作选项
        print(f"\n{LOG_COLORS['INFO']}操作选项:{LOG_COLORS['END']}")
        print(" 1. 查看完整日志")
        print(" 2. 清空日志")
        print(" 0. 返回")
        
        choice = input(f"{LOG_COLORS['INFO']}输入选择: {LOG_COLORS['END']}").strip()
        
        if choice == "1":
            print_header("完整日志")
            for line in lines:
                print(line.strip())
        elif choice == "2":
            confirm = input(f"{LOG_COLORS['WARNING']}确认清空日志? (y/n): {LOG_COLORS['END']}").strip().lower()
            if confirm in ['y', 'yes', '是']:
                with open(LOG_CONFIG['log_file'], 'w', encoding='utf-8') as f:
                    pass
                log("SUCCESS", "日志已清空")
                
    except Exception as e:
        log("ERROR", f"读取日志文件失败: {e}")

try:
    settings = load_settings()
    
    # 显示欢迎信息
    log("INFO", f"接口: {settings['interface']}, 音质: {level_name[settings['level_name']-1]}, 文件夹: {settings['folder']}")
    log("INFO", f"最大重试: {settings['max_retries']}, 超时: {settings['timeout']}秒")
    
    # 主循环
    while True:
        print_header("主菜单")
        
        # 根据接口显示不同菜单
        if settings["interface"] != 3:
            menu_text = f"{LOG_COLORS['INFO']}请选择模式:{LOG_COLORS['END']}\n" \
                       " 0. 修改设置\n" \
                       " 1. 单曲下载\n" \
                       " 2. 批量下载\n" \
                       " 3. 歌单下载\n" \
                       " 4. 专辑下载\n" \
                       " 5. 搜索下载\n" \
                       " 6. 查看日志\n" \
                       f"{LOG_COLORS['INFO']}exit. 退出程序{LOG_COLORS['END']}\n" \
                       f"{LOG_COLORS['INFO']}输入选择: {LOG_COLORS['END']}"
        else:
            menu_text = f"{LOG_COLORS['INFO']}请选择模式:{LOG_COLORS['END']}\n" \
                       " 0. 修改设置\n" \
                       " 1. 单曲下载\n" \
                       " 2. 批量下载\n" \
                       " 3. 歌单下载\n" \
                       " 4. 专辑下载\n" \
                       " 5. 查看日志\n" \
                       f"{LOG_COLORS['INFO']}exit. 退出程序{LOG_COLORS['END']}\n" \
                       f"{LOG_COLORS['INFO']}输入选择: {LOG_COLORS['END']}"
        
        mode = input(menu_text).strip()
        
        if mode == "0":
            settings = edit_settings(settings)
        elif mode == "1":
            single_download(settings)
        elif mode == "2":
            batch_download(settings)
        elif mode == "3":
            playlist_download(settings)
        elif mode == "4":
            album_download(settings)
        elif mode == "5" and settings["interface"] != 3:
            search_download(settings)
        elif mode == "5" and settings["interface"] == 3:
            view_logs()
        elif mode == "6" and settings["interface"] != 3:
            view_logs()
        elif mode.lower() == "exit":
            log("INFO", "感谢使用，再见！")
            break
        else:
            log("ERROR", "无效的选择，请重新输入")()
except KeyboardInterrupt:
    log("INFO", "\n程序被用户中断")
except Exception as e:
    log("ERROR", f"程序运行错误: {e}")
    import traceback
    traceback.print_exc()