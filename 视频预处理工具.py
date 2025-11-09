#!/usr/bin/env python3
"""
视频预处理工具
用于压缩视频文件，减小文件大小，提高处理效率
"""

import os
import subprocess
import shutil
from pathlib import Path

class VideoPreprocessor:
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
    
    def check_ffmpeg(self):
        """检查FFmpeg是否安装"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def compress_video(self, input_path, output_path, quality='medium'):
        """压缩视频文件"""
        if not self.check_ffmpeg():
            print("❌ 未找到FFmpeg，请先安装FFmpeg")
            return False
        
        # 质量设置
        quality_settings = {
            'low': ['-crf', '28', '-preset', 'fast'],
            'medium': ['-crf', '23', '-preset', 'medium'],
            'high': ['-crf', '18', '-preset', 'slow']
        }
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-movflags', '+faststart'
        ] + quality_settings.get(quality, quality_settings['medium']) + [
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        try:
            print(f"正在压缩: {os.path.basename(input_path)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 计算压缩比
                original_size = os.path.getsize(input_path)
                compressed_size = os.path.getsize(output_path)
                ratio = (1 - compressed_size / original_size) * 100
                
                print(f"✅ 压缩完成，压缩率: {ratio:.1f}%")
                print(f"   原始大小: {original_size / 1024 / 1024:.1f}MB")
                print(f"   压缩后: {compressed_size / 1024 / 1024:.1f}MB")
                return True
            else:
                print(f"❌ 压缩失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 压缩异常: {e}")
            return False
    
    def extract_key_frames(self, input_path, output_dir, frame_count=10):
        """提取关键帧"""
        if not self.check_ffmpeg():
            print("❌ 未找到FFmpeg，请先安装FFmpeg")
            return []
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取视频时长
        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', input_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            
            # 计算提取间隔
            interval = duration / frame_count
            
            extracted_frames = []
            for i in range(frame_count):
                timestamp = i * interval
                output_file = os.path.join(output_dir, f"frame_{i+1:03d}.jpg")
                
                cmd = [
                    'ffmpeg', '-i', input_path,
                    '-ss', str(timestamp),
                    '-vframes', '1',
                    '-q:v', '2',
                    '-y',
                    output_file
                ]
                
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode == 0:
                    extracted_frames.append(output_file)
                    print(f"✅ 提取帧 {i+1}/{frame_count}: {os.path.basename(output_file)}")
            
            return extracted_frames
            
        except Exception as e:
            print(f"❌ 提取帧失败: {e}")
            return []
    
    def process_folder(self, input_folder, output_folder, mode='compress', quality='medium'):
        """处理整个文件夹"""
        if not os.path.exists(input_folder):
            print("❌ 输入文件夹不存在")
            return
        
        os.makedirs(output_folder, exist_ok=True)
        
        video_files = []
        for root, dirs, files in os.walk(input_folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.supported_formats):
                    video_files.append(os.path.join(root, file))
        
        print(f"找到 {len(video_files)} 个视频文件")
        
        if mode == 'compress':
            for video_file in video_files:
                relative_path = os.path.relpath(video_file, input_folder)
                output_path = os.path.join(output_folder, relative_path)
                
                # 创建输出目录
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                self.compress_video(video_file, output_path, quality)
        
        elif mode == 'extract_frames':
            for video_file in video_files:
                relative_path = os.path.relpath(video_file, input_folder)
                name_without_ext = os.path.splitext(relative_path)[0]
                frame_dir = os.path.join(output_folder, name_without_ext)
                
                print(f"\n处理视频: {relative_path}")
                self.extract_key_frames(video_file, frame_dir)

def main():
    """主函数"""
    print("🎬 视频预处理工具")
    print("=" * 50)
    
    processor = VideoPreprocessor()
    
    print("选择处理模式:")
    print("1. 压缩视频 (减小文件大小)")
    print("2. 提取关键帧 (生成图片)")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == '1':
        input_folder = input("请输入视频文件夹路径: ").strip()
        output_folder = input("请输入输出文件夹路径: ").strip()
        
        print("选择压缩质量:")
        print("1. 低质量 (文件最小)")
        print("2. 中等质量 (推荐)")
        print("3. 高质量 (文件较大)")
        
        quality_choice = input("请选择 (1/2/3): ").strip()
        quality_map = {'1': 'low', '2': 'medium', '3': 'high'}
        quality = quality_map.get(quality_choice, 'medium')
        
        processor.process_folder(input_folder, output_folder, 'compress', quality)
    
    elif choice == '2':
        input_folder = input("请输入视频文件夹路径: ").strip()
        output_folder = input("请输入输出文件夹路径: ").strip()
        
        processor.process_folder(input_folder, output_folder, 'extract_frames')
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()

