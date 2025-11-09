"""
多模型管理器
支持多种大模型API的统一调用接口
"""

import base64
import io
import requests
import time
import threading
from PIL import Image
from config import MODEL_TYPE, MODEL_CONFIG

class ModelManager:
    def __init__(self):
        self.model_type = MODEL_TYPE
        self.config = MODEL_CONFIG.get(self.model_type, {})
        self.model = None
        self.moondream_model = None  # 专门用于目标检测
        self.cuda_available = False
        
        # 请求限流机制
        self._rate_limit_lock = threading.Lock()  # 线程锁，确保线程安全
        self._last_request_time = {}  # 记录每种API类型上次请求时间
        self._request_interval = {
            'qwen': 5.0,      # 通义千问：每5秒最多1次请求（更保守，避免触发频率限制）
            'openai': 1.0,    # OpenAI：每1秒最多1次请求
            'claude': 1.5,    # Claude：每1.5秒最多1次请求
            'gemini': 1.0,    # Gemini：每1秒最多1次请求
            'default': 5.0    # 默认：每5秒最多1次请求
        }
        
        self._check_cuda_availability()
        self._initialize_model()
        self._initialize_moondream()
    
    def _initialize_model(self):
        """初始化指定的模型"""
        try:
            if self.model_type == "moondream":
                import moondream as md
                self.model = md.vl(api_key=self.config["api_key"])
                print(f"✓ {self.model_type} 模型初始化成功")
                
            elif self.model_type == "openai":
                import openai
                self.client = openai.OpenAI(
                    api_key=self.config["api_key"],
                    base_url=self.config.get("base_url", "https://api.openai.com/v1")
                )
                print(f"✓ {self.model_type} 模型初始化成功")
                
            elif self.model_type == "claude":
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.config["api_key"])
                print(f"✓ {self.model_type} 模型初始化成功")
                
            elif self.model_type == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.config["api_key"])
                self.model = genai.GenerativeModel(self.config["model"])
                print(f"✓ {self.model_type} 模型初始化成功")
                
            elif self.model_type == "qwen":
                import dashscope
                dashscope.api_key = self.config["api_key"]
                self.model = "qwen"  # 设置模型标识
                print(f"✓ {self.model_type} 模型初始化成功")
                
            else:
                raise ValueError(f"不支持的模型类型: {self.model_type}")
                
        except Exception as e:
            print(f"❌ {self.model_type} 模型初始化失败: {e}")
            self.model = None
    
    def _check_cuda_availability(self):
        """检测CUDA是否可用"""
        try:
            import torch
            self.cuda_available = torch.cuda.is_available()
            if self.cuda_available:
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                print(f"✅ CUDA检测: 发现 {gpu_count} 个GPU - {gpu_name}")
            else:
                print("⚠️  CUDA检测: 未发现可用GPU，将使用CPU处理")
        except ImportError:
            print("⚠️  CUDA检测: 未安装PyTorch，将使用CPU处理")
            self.cuda_available = False
        except Exception as e:
            print(f"⚠️  CUDA检测失败: {e}，将使用CPU处理")
            self.cuda_available = False
        
        return self.cuda_available

    def _initialize_moondream(self):
        """初始化Moondream模型（专门用于目标检测）"""
        try:
            import moondream as md
            self.moondream_model = md.vl(api_key=MODEL_CONFIG["moondream"]["api_key"])
            print(f"✓ Moondream 目标检测模型初始化成功")
        except Exception as e:
            print(f"❌ Moondream 目标检测模型初始化失败: {e}")
            self.moondream_model = None
    
    def _wait_for_rate_limit(self, api_type='default'):
        """
        请求限流：确保API调用之间有足够的间隔，避免触发频率限制
        
        Args:
            api_type: API类型 ('qwen', 'openai', 'claude', 'gemini', 'default')
        """
        with self._rate_limit_lock:
            current_time = time.time()
            interval = self._request_interval.get(api_type, self._request_interval['default'])
            
            # 获取该API类型上次请求时间
            last_time = self._last_request_time.get(api_type, 0)
            
            # 计算需要等待的时间
            elapsed = current_time - last_time
            if elapsed < interval:
                wait_time = interval - elapsed
                print(f"⏳ 请求限流：距离上次{api_type} API调用仅过了{elapsed:.2f}秒，等待{wait_time:.2f}秒后继续...")
                time.sleep(wait_time)
            
            # 更新最后请求时间
            self._last_request_time[api_type] = time.time()
    
    def _image_to_base64(self, image):
        """将PIL图像转换为base64字符串"""
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str
    
    def _video_to_base64(self, video_path):
        """将视频文件转换为base64字符串，确保Base64编码后<10MB（通义千问限制）"""
        import os
        
        # 检查文件大小
        file_size = os.path.getsize(video_path)
        size_mb = file_size / 1024 / 1024
        
        # Base64编码会增加约33%的大小
        # 计算Base64编码后的大小
        base64_size_mb = size_mb * 1.33
        
        compressed_path = None
        original_video_path = video_path
        
        # 如果Base64编码后会超过10MB，需要压缩
        if base64_size_mb > 10:
            print(f"⚠️  视频文件({size_mb:.1f}MB)，Base64编码后将达到{base64_size_mb:.1f}MB")
            print(f"📋 通义千问官方限制：Base64编码视频必须<10MB")
            print(f"🔄 自动压缩视频以符合官方限制...")
            
            compressed_path = self._compress_video(video_path)
            if compressed_path:
                compressed_size = os.path.getsize(compressed_path)
                compressed_size_mb = compressed_size / 1024 / 1024
                compressed_base64_size_mb = compressed_size_mb * 1.33
                
                # 检查压缩后是否满足要求
                if compressed_base64_size_mb < 10:
                    video_path = compressed_path
                    print(f"✅ 压缩完成，新大小: {compressed_size_mb:.1f}MB (Base64后: {compressed_base64_size_mb:.2f}MB < 10MB)")
                else:
                    print(f"⚠️  压缩后Base64仍为{compressed_base64_size_mb:.2f}MB，需要进一步压缩...")
                    # 尝试更激进的压缩
                    video_path = compressed_path  # 先使用这个，如果还不行会在API调用时失败
                    print(f"🔄 继续处理，如果API失败请手动压缩视频")
            else:
                print(f"❌ 压缩失败，建议：")
                print(f"   1) 手动压缩视频到<7.5MB（Base64后<10MB）")
                print(f"   2) 或使用公网URL方式（支持<2GB）")
                print(f"   3) 或切换到其他模型（如Claude/OpenAI）")
                print(f"⚠️  尝试使用原文件，可能会因文件过大而失败...")
        else:
            print(f"✅ 视频文件大小: {size_mb:.1f}MB (Base64后: {base64_size_mb:.2f}MB < 10MB)，无需压缩")
        
        try:
            with open(video_path, 'rb') as video_file:
                video_bytes = video_file.read()
                video_str = base64.b64encode(video_bytes).decode()
            
            # 最终验证Base64大小
            final_base64_size_mb = len(video_str) / 1024 / 1024
            if final_base64_size_mb > 10:
                print(f"⚠️  警告：Base64编码后大小为{final_base64_size_mb:.2f}MB，超过10MB限制，API可能会拒绝")
            else:
                print(f"✅ Base64编码后大小: {final_base64_size_mb:.2f}MB，符合要求")
            
            return video_str
        finally:
            # 清理压缩后的临时文件
            if compressed_path and compressed_path != original_video_path and os.path.exists(compressed_path):
                try:
                    os.unlink(compressed_path)
                    print(f"🧹 已清理临时压缩文件: {os.path.basename(compressed_path)}")
                except Exception as e:
                    print(f"⚠️  清理临时文件失败: {e}")
    
    def _compress_video(self, video_path):
        """压缩视频文件以减少处理时间，支持CUDA加速"""
        compressed_path = None
        try:
            import subprocess
            import os
            from config import TEMP_DIR
            
            # 创建临时压缩文件 - 使用配置的临时目录
            temp_dir = TEMP_DIR
            compressed_path = os.path.join(temp_dir, f"compressed_{os.path.basename(video_path)}")
            
            # 目标：压缩到<7MB，这样Base64后<9.3MB，留出安全边距
            original_size = os.path.getsize(video_path)
            target_size_mb = 7.0  # 7MB（Base64后约9.3MB）
            target_size = target_size_mb * 1024 * 1024
            
            original_size_mb = original_size / 1024 / 1024
            print(f"📊 压缩目标：从 {original_size_mb:.1f}MB 压缩到 <{target_size_mb}MB（Base64后<10MB）")
            
            # 根据原始大小和Base64编码后的预期大小调整压缩参数
            # 更精确地根据文件大小计算压缩参数
            if original_size > 100 * 1024 * 1024:  # >100MB，需要大幅压缩
                scale = "320:240"  # 很小的分辨率
                bitrate = "150k"   # 很低的码率
                fps = "8"          # 很低的帧率
            elif original_size > 50 * 1024 * 1024:  # >50MB
                scale = "480:360"
                bitrate = "250k"
                fps = "10"
            elif original_size > 20 * 1024 * 1024:  # >20MB
                scale = "640:480"
                bitrate = "400k"
                fps = "12"
            else:  # 10-20MB
                scale = "854:480"  # 稍高的分辨率
                bitrate = "600k"
                fps = "15"
            
            # 检查CUDA可用性并选择编码器
            cuda_available = self._check_cuda_availability()
            video_codec = 'h264_nvenc' if cuda_available else 'libx264'
            
            # 首先尝试使用配置的ffmpeg路径
            try:
                from config import FFMPEG_PATH
                if os.path.exists(FFMPEG_PATH):
                    ffmpeg_path = FFMPEG_PATH
                    print(f"✅ 使用配置的ffmpeg路径: {ffmpeg_path}")
                else:
                    raise FileNotFoundError("配置的ffmpeg路径不存在")
            except Exception:
                # 回退到imageio-ffmpeg
                try:
                    import imageio_ffmpeg
                    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                    print(f"✅ 使用imageio-ffmpeg路径: {ffmpeg_path}")
                except Exception:
                    ffmpeg_path = 'ffmpeg'  # 回退到系统ffmpeg
                    print("⚠️  未找到imageio-ffmpeg，尝试系统ffmpeg")
            
            # 使用ffmpeg压缩视频，支持CUDA加速
            cmd = [
                ffmpeg_path, '-i', video_path,
                '-vf', f'scale={scale}',  # 动态分辨率
                '-b:v', bitrate,          # 动态码率
                '-r', fps,                # 动态帧率
                '-c:v', video_codec,     # 使用CUDA加速的编码器（如果可用）
                '-preset', 'fast',        # 快速编码
                '-y',                     # 覆盖输出文件
                compressed_path
            ]
            
            print(f"压缩参数: 分辨率={scale}, 码率={bitrate}, 帧率={fps}")
            if cuda_available:
                print("✅ 检测到CUDA，使用GPU加速视频压缩")
            else:
                print("⚠️  未检测到CUDA，使用CPU压缩")
            
            # 执行压缩命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and os.path.exists(compressed_path):
                compressed_size = os.path.getsize(compressed_path)
                compressed_size_mb = compressed_size / 1024 / 1024
                compressed_base64_size_mb = compressed_size_mb * 1.33
                
                if compressed_base64_size_mb < 10:
                    print(f"✅ 压缩成功: {compressed_size_mb:.1f}MB (Base64后: {compressed_base64_size_mb:.2f}MB < 10MB)")
                    return compressed_path
                else:
                    print(f"⚠️  压缩后Base64仍为{compressed_base64_size_mb:.2f}MB，超过10MB限制")
                    print(f"🔄 尝试更激进的压缩参数...")
                    # 使用更激进的压缩参数重新压缩（从原始文件重新压缩）
                    return self._aggressive_compress(video_path, compressed_path)
            else:
                print(f"ffmpeg压缩失败: {result.stderr}")
                return self._compress_video_python(video_path, compressed_path)
                
        except Exception as e:
            print(f"ffmpeg压缩出错: {e}")
            return self._compress_video_python(video_path, compressed_path)
    
    def _aggressive_compress(self, video_path, compressed_path):
        """更激进的压缩策略"""
        try:
            import subprocess
            import os
            
            # 首先尝试使用配置的ffmpeg路径
            try:
                from config import FFMPEG_PATH
                if os.path.exists(FFMPEG_PATH):
                    ffmpeg_path = FFMPEG_PATH
                    print(f"✅ 使用配置的ffmpeg路径: {ffmpeg_path}")
                else:
                    raise FileNotFoundError("配置的ffmpeg路径不存在")
            except Exception:
                # 回退到imageio-ffmpeg
                try:
                    import imageio_ffmpeg
                    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                    print(f"✅ 使用imageio-ffmpeg路径: {ffmpeg_path}")
                except Exception:
                    ffmpeg_path = 'ffmpeg'  # 回退到系统ffmpeg
                    print("⚠️  未找到imageio-ffmpeg，尝试系统ffmpeg")
            
            # 更激进的压缩参数 (确保Base64后<10MB)
            cmd = [
                ffmpeg_path, '-i', video_path,
                '-vf', 'scale=240:180',  # 极小的分辨率
                '-b:v', '150k',          # 极低的码率
                '-r', '8',               # 极低的帧率
                '-c:v', 'libx264',
                '-preset', 'ultrafast',  # 最快编码
                '-crf', '32',            # 极高压缩率
                '-y',
                compressed_path
            ]
            
            print("使用激进压缩策略...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and os.path.exists(compressed_path):
                compressed_size = os.path.getsize(compressed_path)
                compressed_size_mb = compressed_size / 1024 / 1024
                compressed_base64_size_mb = compressed_size_mb * 1.33
                print(f"激进压缩完成: {compressed_size_mb:.1f}MB (Base64后: {compressed_base64_size_mb:.2f}MB)")
                
                # 检查Base64编码后是否仍然大于10MB
                if compressed_base64_size_mb >= 10:
                    print(f"⚠️  激进压缩后Base64仍为{compressed_base64_size_mb:.2f}MB >= 10MB，尝试超激进压缩")
                    return self._ultra_aggressive_compress(video_path, compressed_path)
                
                return compressed_path
            else:
                print(f"激进压缩失败: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"激进压缩出错: {e}")
            return None
    
    def _ultra_aggressive_compress(self, video_path, compressed_path):
        """超激进压缩策略 - 确保5分半1080p视频也能压缩到10MB以下"""
        try:
            import subprocess
            import os
            
            # 首先尝试使用配置的ffmpeg路径
            try:
                from config import FFMPEG_PATH
                if os.path.exists(FFMPEG_PATH):
                    ffmpeg_path = FFMPEG_PATH
                    print(f"✅ 使用配置的ffmpeg路径: {ffmpeg_path}")
                else:
                    raise FileNotFoundError("配置的ffmpeg路径不存在")
            except Exception:
                # 回退到imageio-ffmpeg
                try:
                    import imageio_ffmpeg
                    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                    print(f"✅ 使用imageio-ffmpeg路径: {ffmpeg_path}")
                except Exception:
                    ffmpeg_path = 'ffmpeg'  # 回退到系统ffmpeg
                    print("⚠️  未找到imageio-ffmpeg，尝试系统ffmpeg")
            
            # 生成新的压缩文件路径，避免覆盖之前的文件
            base_name = os.path.splitext(compressed_path)[0]
            ultra_compressed_path = f"{base_name}_ultra.mp4"
            
            # 超激进压缩参数 - 针对5分半1080p视频优化
            cmd = [
                ffmpeg_path, '-i', video_path,
                '-vf', 'scale=160:120',          # 极低分辨率
                '-b:v', '80k',                  # 极低码率
                '-r', '5',                      # 极低帧率（5fps）
                '-c:v', 'libx264',
                '-preset', 'ultrafast',         # 最快编码
                '-crf', '38',                   # 超高压缩率
                '-t', '330',                    # 限制视频长度为5分30秒
                '-y',
                ultra_compressed_path
            ]
            
            print("使用超激进压缩策略...")
            print("压缩参数: 160x120分辨率, 80k码率, 5fps帧率, CRF38, 限制5分30秒")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)  # 15分钟超时
            
            if result.returncode == 0 and os.path.exists(ultra_compressed_path):
                compressed_size = os.path.getsize(ultra_compressed_path)
                print(f"超激进压缩完成: {compressed_size/1024/1024:.1f}MB")
                
                # 检查是否仍然大于目标大小（7.5MB）
                target_size = 7.5 * 1024 * 1024  # 7.5MB
                if compressed_size > target_size:
                    print(f"⚠️  超激进压缩后仍较大: {compressed_size/1024/1024:.1f}MB > 7.5MB")
                    print("尝试终极压缩策略...")
                    return self._final_aggressive_compress(video_path, ultra_compressed_path)
                
                return ultra_compressed_path
            else:
                print(f"超激进压缩失败: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"超激进压缩出错: {e}")
            return None
    
    def _final_aggressive_compress(self, video_path, compressed_path):
        """终极压缩策略 - 最后的手段"""
        try:
            import subprocess
            import os
            
            # 首先尝试使用配置的ffmpeg路径
            try:
                from config import FFMPEG_PATH
                if os.path.exists(FFMPEG_PATH):
                    ffmpeg_path = FFMPEG_PATH
                    print(f"✅ 使用配置的ffmpeg路径: {ffmpeg_path}")
                else:
                    raise FileNotFoundError("配置的ffmpeg路径不存在")
            except Exception:
                # 回退到imageio-ffmpeg
                try:
                    import imageio_ffmpeg
                    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                    print(f"✅ 使用imageio-ffmpeg路径: {ffmpeg_path}")
                except Exception:
                    ffmpeg_path = 'ffmpeg'  # 回退到系统ffmpeg
                    print("⚠️  未找到imageio-ffmpeg，尝试系统ffmpeg")
            
            # 生成最终的压缩文件路径
            base_name = os.path.splitext(compressed_path)[0]
            final_compressed_path = f"{base_name}_final.mp4"
            
            # 终极压缩参数 - 最大程度压缩
            cmd = [
                ffmpeg_path, '-i', video_path,
                '-vf', 'scale=120:90',          # 最低分辨率
                '-b:v', '50k',                  # 最低码率
                '-r', '3',                      # 最低帧率（3fps）
                '-c:v', 'libx264',
                '-preset', 'ultrafast',         # 最快编码
                '-crf', '45',                   # 最大压缩率
                '-t', '180',                    # 限制视频长度为3分钟
                '-y',
                final_compressed_path
            ]
            
            print("使用终极压缩策略...")
            print("压缩参数: 120x90分辨率, 50k码率, 3fps帧率, CRF45, 限制3分钟")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)  # 20分钟超时
            
            if result.returncode == 0 and os.path.exists(final_compressed_path):
                compressed_size = os.path.getsize(final_compressed_path)
                print(f"终极压缩完成: {compressed_size/1024/1024:.1f}MB")
                
                # 检查是否仍然大于目标大小（7.5MB）
                target_size = 7.5 * 1024 * 1024  # 7.5MB
                if compressed_size > target_size:
                    print(f"❌ 所有压缩策略均失败，文件仍过大: {compressed_size/1024/1024:.1f}MB")
                    print("建议: 1. 检查视频内容 2. 考虑分段处理 3. 使用更高压缩率的编码器")
                    return None
                
                return final_compressed_path
            else:
                print(f"终极压缩失败: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"终极压缩出错: {e}")
            return None
    
    def _compress_video_python(self, video_path, compressed_path):
        """使用ffmpeg-python压缩视频"""
        try:
            import ffmpeg
            import os
            
            # 使用ffmpeg-python压缩
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.filter(stream, 'scale', 640, 480)
            stream = ffmpeg.output(stream, compressed_path, vcodec='libx264', b='500k', r=15)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            if os.path.exists(compressed_path):
                return compressed_path
            else:
                print("ffmpeg-python压缩失败")
                return None
                
        except Exception as e:
            print(f"ffmpeg-python压缩出错: {e}")
            return None
    
    def query(self, image, question):
        """统一的查询接口"""
        if not self.model and not hasattr(self, 'client'):
            return {"answer": "模型未初始化", "error": "模型未初始化"}
        
        try:
            if self.model_type == "moondream":
                return self._query_moondream(image, question)
            elif self.model_type == "openai":
                return self._query_openai(image, question)
            elif self.model_type == "claude":
                return self._query_claude(image, question)
            elif self.model_type == "gemini":
                return self._query_gemini(image, question)
            elif self.model_type == "qwen":
                return self._query_qwen(image, question)
        except Exception as e:
            return {"answer": f"查询失败: {str(e)}", "error": str(e)}
    
    def query_video(self, video_path, question):
        """直接处理视频文件的接口"""
        if not self.model and not hasattr(self, 'client'):
            return {"answer": "模型未初始化", "error": "模型未初始化"}
        
        try:
            # 检查视频文件是否存在
            import os
            if not os.path.exists(video_path):
                return {"answer": "视频文件不存在", "error": "视频文件不存在"}
            
            # 检查文件大小（仅记录，不限制）
            file_size = os.path.getsize(video_path)
            print(f"处理视频文件: {video_path}, 大小: {file_size/1024/1024:.1f}MB")
            
            # 根据模型类型调用相应的视频查询方法
            if self.model_type == "moondream":
                return self._query_moondream_video(video_path, question)
            elif self.model_type == "openai":
                return self._query_openai_video(video_path, question)
            elif self.model_type == "claude":
                return self._query_claude_video(video_path, question)
            elif self.model_type == "gemini":
                return self._query_gemini_video(video_path, question)
            elif self.model_type == "qwen":
                return self._query_qwen_video(video_path, question)
            else:
                return {"answer": f"{self.model_type} 不支持视频查询", "error": "不支持的模型类型"}
        except Exception as e:
            return {"answer": f"视频查询失败: {str(e)}", "error": str(e)}
    
    def get_video_support_info(self):
        """获取各模型对视频的支持信息"""
        return {
            "moondream": {"supported": False, "note": "仅支持图像"},
            "openai": {"supported": True, "note": "GPT-4V支持视频，推荐使用"},
            "claude": {"supported": True, "note": "Claude-3.5支持视频，推荐使用"},
            "gemini": {"supported": True, "note": "Gemini-1.5支持视频"},
            "qwen": {"supported": False, "note": "通义千问可能不支持视频，建议使用其他模型"}
        }
    
    def _query_moondream(self, image, question):
        """Moondream查询"""
        result = self.model.query(image, question)
        return {"answer": result.get('answer', ''), "request_id": result.get('request_id', '')}
    
    def _query_moondream_video(self, video_path, question):
        """Moondream视频查询 - 不支持视频"""
        return {"answer": "Moondream暂不支持直接视频分析，建议使用OpenAI、Claude、Gemini或通义千问模型", "error": "模型不支持视频"}
    
    def _query_openai(self, image, question):
        """OpenAI GPT-4V查询"""
        # 请求限流
        self._wait_for_rate_limit('openai')
        
        base64_image = self._image_to_base64(image)
        
        response = self.client.chat.completions.create(
            model=self.config["model"],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        return {
            "answer": response.choices[0].message.content,
            "request_id": response.id
        }
    
    def _query_openai_video(self, video_path, question):
        """OpenAI GPT-4V视频查询"""
        # 请求限流
        self._wait_for_rate_limit('openai')
        
        base64_video = self._video_to_base64(video_path)
        
        response = self.client.chat.completions.create(
            model=self.config["model"],
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的视频分析师。请分析整个视频的内容，包括环境、人物、动作、时间变化等动态信息。"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "video_url",
                            "video_url": {
                                "url": f"data:video/mp4;base64,{base64_video}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        return {
            "answer": response.choices[0].message.content,
            "request_id": response.id
        }
    
    def _query_claude(self, image, question):
        """Claude查询"""
        # 请求限流
        self._wait_for_rate_limit('claude')
        
        base64_image = self._image_to_base64(image)
        
        response = self.client.messages.create(
            model=self.config["model"],
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        },
                        {"type": "text", "text": question}
                    ]
                }
            ]
        )
        
        return {
            "answer": response.content[0].text,
            "request_id": response.id
        }
    
    def _query_claude_video(self, video_path, question):
        """Claude视频查询"""
        # 请求限流
        self._wait_for_rate_limit('claude')
        
        base64_video = self._video_to_base64(video_path)
        
        response = self.client.messages.create(
            model=self.config["model"],
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "video",
                            "source": {
                                "type": "base64",
                                "media_type": "video/mp4",
                                "data": base64_video
                            }
                        },
                        {"type": "text", "text": f"请分析这个视频的整体内容：{question}"}
                    ]
                }
            ],
            temperature=0.7
        )
        
        return {
            "answer": response.content[0].text,
            "request_id": response.id
        }
    
    def _query_gemini(self, image, question):
        """Gemini查询"""
        # 请求限流
        self._wait_for_rate_limit('gemini')
        
        # 将PIL图像转换为字节
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        response = self.model.generate_content([question, image_bytes])
        
        return {
            "answer": response.text,
            "request_id": "gemini_response"
        }
    
    def _query_gemini_video(self, video_path, question):
        """Gemini视频查询"""
        # 请求限流
        self._wait_for_rate_limit('gemini')
        
        # 使用_video_to_base64方法，会自动压缩大文件
        base64_video = self._video_to_base64(video_path)
        
        # 将base64转换回字节
        video_bytes = base64.b64decode(base64_video)
        
        # 构建提示词
        enhanced_question = f"请分析这个视频的整体内容，包括环境、人物、动作、时间变化等动态信息：{question}"
        
        response = self.model.generate_content([enhanced_question, video_bytes])
        
        return {
            "answer": response.text,
            "request_id": "gemini_video_response"
        }
    
    def _query_qwen(self, image, question):
        """通义千问查询"""
        from dashscope import MultiModalConversation
        import os
        
        # 将PIL图像转换为字节
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"},
                    {"text": question}
                ]
            }
        ]
        
        # 请求限流：确保不会超过API频率限制
        self._wait_for_rate_limit('qwen')
        
        # 使用官方推荐的调用方式
        try:
            response = MultiModalConversation.call(
                api_key=self.config["api_key"],  # 直接传递API Key
                model=self.config["model"],
                messages=messages,
                stream=False  # 非流式调用
            )
            
            # 检查响应状态码（API可能返回错误状态而不是抛出异常）
            if hasattr(response, 'status_code') and response.status_code is not None:
                if response.status_code >= 400:
                    error_code = getattr(response, 'code', 'Unknown')
                    error_message = getattr(response, 'message', f'API返回错误状态码: {response.status_code}')
                    raise Exception(f"{error_code}: {error_message}")
            
            # 检查output是否为None（表示API调用失败）
            if not hasattr(response, 'output') or response.output is None:
                error_message = getattr(response, 'message', 'API返回output为None')
                error_code = getattr(response, 'code', 'InternalError')
                raise Exception(f"{error_code}: {error_message}")
            
            # 处理响应格式
            if hasattr(response.output, 'choices') and response.output.choices:
                content = response.output.choices[0].message.content[0]
                if hasattr(content, 'text'):
                    answer = content.text
                elif isinstance(content, dict) and 'text' in content:
                    answer = content['text']
                else:
                    answer = str(content)
            else:
                raise Exception("API响应中choices为空或不存在")
            
            return {
                "answer": answer,
                "request_id": getattr(response, 'request_id', '')
            }
        except Exception as e:
            error_msg = str(e)
            error_msg_lower = error_msg.lower()
            
            # 检测InternalError.Algo和500错误
            if "internalerror.algo" in error_msg_lower or "500" in error_msg or "model_dump" in error_msg_lower:
                return {
                    "answer": "通义千问API内部算法错误，可能是：1) 图片格式不兼容 2) 图片内容无法解析 3) API服务暂时异常。建议：1) 尝试其他图片 2) 稍后重试 3) 或切换到其他模型",
                    "error": f"API内部算法错误: {error_msg}"
                }
            else:
                return {
                    "answer": f"通义千问处理失败: {error_msg}",
                    "error": error_msg
                }
    
    def _query_qwen_video(self, video_path, question):
        """通义千问视频查询"""
        try:
            from dashscope import MultiModalConversation
            import os
            
            # 记录文件大小
            file_size = os.path.getsize(video_path)
            print(f"通义千问处理视频，大小: {file_size/1024/1024:.1f}MB")
            
            # 使用_video_to_base64方法，会自动压缩大文件
            base64_video = self._video_to_base64(video_path)
            
            # 构建提示词
            enhanced_question = f"请分析这个视频的整体内容，包括环境、人物、动作、时间变化等动态信息：{question}"
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"video": f"data:video/mp4;base64,{base64_video}"},
                        {"text": enhanced_question}
                    ]
                }
            ]
            
            # 添加超时和重试机制
            max_retries = 5  # 增加到5次重试
            for attempt in range(max_retries):
                try:
                    # 请求限流：确保不会超过API频率限制
                    self._wait_for_rate_limit('qwen')
                    
                    print(f"正在调用通义千问API... (第{attempt+1}次尝试)")
                    # 使用官方推荐的调用方式
                    response = MultiModalConversation.call(
                        api_key=self.config["api_key"],  # 直接传递API Key
                        model=self.config["model"],
                        messages=messages,
                        stream=False,  # 非流式调用
                        timeout=300  # 增加到300秒超时
                    )
                    
                    # 检查响应状态码（API可能返回错误状态而不是抛出异常）
                    if hasattr(response, 'status_code') and response.status_code is not None:
                        if response.status_code >= 400:
                            # API返回了错误状态码
                            error_code = getattr(response, 'code', 'Unknown')
                            error_message = getattr(response, 'message', f'API返回错误状态码: {response.status_code}')
                            raise Exception(f"{error_code}: {error_message}")
                    
                    # 检查output是否为None（表示API调用失败）
                    if not hasattr(response, 'output') or response.output is None:
                        error_message = getattr(response, 'message', 'API返回output为None')
                        error_code = getattr(response, 'code', 'InternalError')
                        raise Exception(f"{error_code}: {error_message}")
                    
                    print("通义千问API调用成功")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        error_msg = str(e)
                        print(f"通义千问API调用失败，第{attempt+1}次重试: {e}")
                        
                        # 检测是否是频率限制错误
                        is_rate_limit = any(keyword in error_msg.lower() for keyword in 
                                           ['rate limit', '频率', 'quota', 'limit exceeded', 'too many requests', '429'])
                        
                        if is_rate_limit:
                            # 频率限制错误：等待更长时间
                            sleep_time = 30 + (attempt * 10)  # 30秒起步，每次重试增加10秒
                            print(f"⚠️ 检测到频率限制错误，等待{sleep_time}秒后重试...")
                        else:
                            # 普通错误：智能重试间隔
                            sleep_time = [3, 5, 10, 15][min(attempt, 3)]
                            print(f"等待{sleep_time}秒后重试...")
                        
                        time.sleep(sleep_time)
                    else:
                        print(f"通义千问API调用失败，已达到最大重试次数{max_retries}次")
                        raise e
            
            # 处理响应格式
            try:
                if hasattr(response, 'output') and response.output is not None:
                    if hasattr(response.output, 'choices') and response.output.choices:
                        content = response.output.choices[0].message.content[0]
                        if hasattr(content, 'text'):
                            answer = content.text
                        elif isinstance(content, dict) and 'text' in content:
                            answer = content['text']
                        else:
                            answer = str(content)
                    else:
                        # choices为空或不存在
                        raise Exception("API响应中choices为空或不存在")
                else:
                    # output为None
                    raise Exception("API响应中output为None")
            except Exception as parse_error:
                # 解析响应时出错，返回错误信息
                error_msg = getattr(response, 'message', str(parse_error))
                error_code = getattr(response, 'code', 'ResponseParseError')
                raise Exception(f"{error_code}: {error_msg}")
            
            return {
                "answer": answer,
                "request_id": getattr(response, 'request_id', '')
            }
            
        except Exception as e:
            error_msg = str(e)
            error_msg_lower = error_msg.lower()
            
            # 检测InternalError.Algo和500错误
            if "internalerror.algo" in error_msg_lower or "500" in error_msg or "model_dump" in error_msg_lower:
                return {
                    "answer": "通义千问API内部算法错误，可能是：1) 视频格式不兼容 2) 视频内容无法解析 3) API服务暂时异常。建议：1) 尝试其他视频文件 2) 稍后重试 3) 或切换到其他模型（如OpenAI GPT-4V、Claude）",
                    "error": f"API内部算法错误: {error_msg}"
                }
            elif "ProxyError" in error_msg:
                return {
                    "answer": "通义千问API连接失败，可能是网络代理问题。建议：1) 检查网络连接 2) 关闭代理 3) 或尝试使用其他模型（如OpenAI、Claude）",
                    "error": f"网络代理错误: {error_msg}"
                }
            elif "ConnectionResetError" in error_msg or "Connection aborted" in error_msg:
                return {
                    "answer": "通义千问API连接被远程主机强制关闭，可能是：1) 视频文件太大 2) 网络不稳定 3) 服务器负载过高。建议：1) 压缩视频到<20MB 2) 重试几次 3) 或切换到其他模型",
                    "error": f"连接被重置: {error_msg}"
                }
            elif "video" in error_msg_lower:
                return {
                    "answer": "通义千问可能不支持视频输入，建议使用支持视频的模型如OpenAI GPT-4V或Claude。",
                    "error": f"视频处理错误: {error_msg}"
                }
            else:
                return {
                    "answer": f"通义千问处理失败: {error_msg}",
                    "error": error_msg
                }
    
    def detect(self, image, target):
        """目标检测接口（使用专门的Moondream模型）"""
        if not self.moondream_model:
            return {"objects": [], "error": "Moondream 目标检测模型未初始化"}
        
        try:
            result = self.moondream_model.detect(image, target)
            return result
        except Exception as e:
            return {"objects": [], "error": str(e)}

