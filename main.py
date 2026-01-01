import API_1
import API_2
import os
import json
import re
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen.flac import FLAC, Picture

level_name = ["standard", "exhigh", "lossless", "hires", "jyeffect", "sky", "jymaster"]
settings = {
    "interface": 1,
    "level_name": 1,
    "folder": "Music"
}
def API_1_download(music_id):
    music_url = API_1.get_music_url(music_id,level_name[settings["level_name"]-1],settings["interface"])
    if "mp3" in music_url:
        file_type ="mp3"
    elif "flac" in music_url:
        file_type = "flac"
        
    music_info = API_1.get_music_info(music_id,settings["interface"])
    safe_name = re.sub(r'[\\/*?:"<>|]', "", music_info["name"])
    filename = f"{safe_name}_{music_id}.{file_type}"
    filepath = download(music_url,filename,settings["folder"])
    pngname = f"{safe_name}_{music_id}.png"
    pngpath = download(music_info["picimg"],pngname,settings["folder"])
    write_metadata(file_type,filepath,pngpath,music_info)
    API_1.get_music_lrc(music_id,music_info["name"],settings["interface"],settings["folder"])
    
def API_2_download(music_id):
    music_info = API_2.get_music(music_id,level_name[settings["level_name"]-1],settings["folder"])
            
    safe_name = re.sub(r'[\\/*?:"<>|]', "", music_info["name"])
    filename = f"{safe_name}_{music_id}.{music_info['type']}"
    filepath = download(music_info["url"],filename,settings["folder"])
    pngname = f"{safe_name}_{music_id}.png"
    pngpath = download(music_info["picimg"],pngname,settings["folder"])
    write_metadata(music_info["type"],filepath,pngpath,music_info)
    
def download(url,filename,folder):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        print(f"开始下载: {filename}")
        response = requests.get(url, stream=True, verify=False)
        filepath = os.path.join(folder, filename)
        
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = downloaded / total_size * 100
                            bar = '█' * int(40 * downloaded // total_size) + '▒' * (40 - int(40 * downloaded // total_size))
                            print(f"\r\033[92m下载进度: [{bar}] {progress:.1f}%\033[0m", end="")
            
            print(f"\n✅ {filename}下载完成")
            return filepath
        else:
            print("❌ 下载失败")
            return False
    except Exception as e:
        print(f"❌ 下载错误: {e}")
        return False

def write_metadata(filetype,filepath,pngpath,music_info):
    try:
        if filetype == 'mp3':
            
            audio = MP3(filepath, ID3=ID3)
            
            
            if audio.tags is None:
                audio.tags = ID3()
            
            
            audio.tags.add(TIT2(encoding=3, text=music_info['name']))  
            audio.tags.add(TPE1(encoding=3, text=music_info['singer']))  
            audio.tags.add(TALB(encoding=3, text=music_info['album']))  
            
            
            with open(pngpath, 'rb') as img:
                audio.tags.add(APIC(
                    encoding=3,  
                    mime='image/png',
                    type=3,  
                    desc='Cover',
                    data=img.read()
                ))
            
            
            audio.save()
            
        elif filetype == 'flac':
            
            audio = FLAC(filepath)
            
            
            audio['title'] = [music_info['name']]
            audio['artist'] = [music_info['singer']]
            audio['album'] = [music_info['album']]
            
            
            picture = Picture()
            picture.type = 3  
            picture.mime = 'image/png'
            
            with open(pngpath, 'rb') as f:
                picture.data = f.read()
            
            audio.clear_pictures()  
            audio.add_picture(picture)
            
            
            audio.save()
            
        print(f"成功写入 {filetype.upper()} 文件元数据: {filepath}")
        os.remove(pngpath)
        return True
        
    except Exception as e:
        print(f"写入元数据时出错: {str(e)}")
        raise
        
if os.path.exists("settings.json"):
    with open('settings.json', 'r') as f:
        settings = json.load(f)
else:
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)
        
while True:
    print("-" * 50)
    if os.path.exists("settings.json"):
        with open('settings.json', 'r') as f:
            settings = json.load(f)
    else:
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
    if settings["interface"] != 3:
        mode = input("请输入模式：\n0.修改设置\n1.单曲解析\n2.批量解析\n3.歌单解析\n4.专辑解析\n5.歌曲搜索\n")
    elif settings["interface"] == 3:
        mode = input("请输入模式：\n0.修改设置\n1.单曲解析\n2.批量解析\n3.歌单解析\n4.专辑解析\n")
        
    if mode == "0":
        while True:
            edit = input("请输入需要修改的项：\n0.退出修改\n1.接口\n2.音质\n3.下载文件夹\n")
            if edit == "0":
                break
            elif edit == "1":
                interface = input(f"当前接口为{settings['interface']}\n请输入需要修改的接口：\n0.取消修改\n1.接口1\n2.接口2\n3.接口3（不支持搜索）\n")
                if interface == "0":
                    pass
                elif int(interface) >= 1 <= 3:
                    settings["interface"] = int(interface)
                else:
                    print("无效值")
            elif edit == "2":
                level_name = input(f"当前音质为{level_name[settings['level_name']]}，请输入要更改成的音质序号：\n1.standard：标准音质\n2.exhigh：极高音质\n3.lossless：无损音质\n4.hires：Hi-Res音质\n5.jyeffect：高清环绕声\n6.sky：沉浸环绕声\n7.jymaster：超清母带\n")
                if level_name == "0":
                    pass
                elif int(level_name) >= 1 <= 7:
                    settings["level_name"] == int(level_name)
                else:
                    print("无效值")
            elif edit == "3":
               path = input(f"当前路径为{settings['folder']}，请输入要更改成的文件夹名称：")
               if path == "0":
                   pass
               else:
                   settings["folder"] = path
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=4)
    elif mode == "1":
        while True:
            music_id = input("请输入歌曲ID或URL，输入0退出该模式：")
            if music_id == "0":
                break
            if "=" in music_id:
                music_id = music_id.split("=")[1]
            
            if settings["interface"] != 3:
                API_1_download(music_id)
                
            else:
                API_2_download(music_id)
            
    elif mode == "2":
        while True:
            music_id_list = input("请输入歌曲ID，以空格分割，输入0退出该模式：")
            if music_id_list == "0":
                break
            music_id_list = music_id_list.split(" ")
            
            if settings["interface"] != 3:
                if music_id_list:
                    for music_id in music_id_list:
                        API_1_download(music_id)
                
            else:
                if music_id_list:
                    for music_id in music_id_list:
                        API_2_download(music_id)
                    
    elif mode == "3":
        while True:
            playlist_id = input("请输入歌单ID或链接，输入0退出该模式：")
            if playlist_id == "0":
                break
            if "=" in playlist_id:
                playlist_id = playlist_id.split("=")[1]
            
            if settings["interface"] != 3:
                music_id_list = API_1.get_playlist_info(playlist_id,settings["interface"])
                if music_id_list != False:
                    for music_id in music_id_list:
                        API_1_download(music_id)
                
            else:
                music_id_list = API_2.get_playlist_info(playlist_id)
                if music_id_list != False:
                    for music_id in music_id_list:
                        API_2_download(music_id)
                        
    elif mode == "4":
        while True:
            album_id = input("请输入专辑ID或链接，输入0退出该模式：")
            if album_id == "0":
                break
            if "=" in album_id:
                album_id = album_id.split("=")[1]
            
            if settings["interface"] != 3:
                music_id_list = API_1.get_album_info(album_id,settings["interface"])
                if music_id_list != False:
                    for music_id in music_id_list:
                        API_1_download(music_id)
                
            else:
                music_id_list = API_2.get_album_info(album_id)
                if music_id_list != False:
                    for music_id in music_id_list:
                        API_2_download(music_id)
    elif mode == "5":
        print("未完成")
                    
    else:
        print("无效模式")
