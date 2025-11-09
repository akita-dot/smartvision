#!/usr/bin/env python3
"""
测试直接视频处理功能
验证修改后的代码是否能正确处理视频文件而不需要抽帧
"""

import requests
import os
import sys

def test_video_query():
    """测试单个视频查询接口"""
    print("🧪 测试单个视频查询接口...")
    
    # 检查是否有测试视频文件
    test_video_path = None
    uploads_dir = "uploads"
    
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            if file.endswith(('.mp4', '.avi', '.mov')):
                test_video_path = os.path.join(uploads_dir, file)
                break
    
    if not test_video_path:
        print("❌ 未找到测试视频文件，请在 uploads 文件夹中放置一个视频文件")
        return False
    
    print(f"📹 使用测试视频: {test_video_path}")
    
    # 测试API
    url = "http://localhost:5000/api/video-query"
    
    try:
        with open(test_video_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {'question': '请分析这个视频的整体内容，包括环境、人物、动作等动态信息'}
            
            print("📤 发送请求到API...")
            response = requests.post(url, files=files, data=data, timeout=120)  # 增加超时时间
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ 视频查询成功!")
                    print(f"📝 问题: {result.get('question')}")
                    print(f"💬 回答: {result.get('answer')}")
                    print(f"🆔 请求ID: {result.get('request_id')}")
                    return True
                else:
                    print(f"❌ API返回错误: {result.get('error')}")
                    return False
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_batch_video_query():
    """测试批量视频查询接口，确保文件被正确关闭"""
    print("🧪 测试批量视频查询接口...")
    
    # 检查是否有测试视频文件
    test_videos = []
    uploads_dir = "uploads"
    
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            if file.endswith(('.mp4', '.avi', '.mov')):
                test_videos.append(os.path.join(uploads_dir, file))
                if len(test_videos) >= 2:  # 只需要2个视频测试
                    break
    
    if len(test_videos) < 1:
        print("❌ 未找到测试视频文件，请在 uploads 文件夹中放置至少一个视频文件")
        return False
    
    print(f"📹 找到 {len(test_videos)} 个测试视频")
    
    # 测试API
    url = "http://localhost:5000/api/video-batch-query"
    
    files = []
    try:
        for video_path in test_videos:
            files.append(('videos', open(video_path, 'rb')))
        
        data = {'question': '请分析这个视频的整体内容，包括环境、人物、动作等动态信息'}
        
        print("📤 发送批量请求到API...")
        response = requests.post(url, files=files, data=data, timeout=300)  # 增加超时时间
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 批量视频查询成功!")
                print(f"📝 问题: {result.get('question')}")
                print(f"📊 总文件数: {result.get('total_files')}")
                print("📋 结果:")
                for i, video_result in enumerate(result.get('results', []), 1):
                    print(f"  {i}. {video_result.get('filename')}")
                    print(f"     成功: {video_result.get('success')}")
                    if video_result.get('success'):
                        print(f"     回答: {video_result.get('answer')[:100]}...")
                    else:
                        print(f"     错误: {video_result.get('error')}")
                return True
            else:
                print(f"❌ API返回错误: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False
    finally:
        # 确保所有文件被正确关闭
        for _, file_obj in files:
            try:
                file_obj.close()
            except Exception as e:
                print(f"⚠️  关闭文件失败: {e}")

def test_health_check():
    """测试健康检查接口"""
    print("🏥 测试健康检查接口...")
    
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ 服务器健康检查通过")
            print(f"📊 模型状态: {'已加载' if result.get('model_loaded') else '未加载'}")
            print(f"🤖 模型类型: {result.get('model_type')}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试直接视频处理功能")
    print("=" * 50)
    
    # 首先检查服务器是否运行
    if not test_health_check():
        print("❌ 服务器未运行或无法访问，请先启动后端服务器")
        print("💡 运行命令: python backend_api.py")
        return
    
    print()
    
    # 测试单个视频查询
    print("=" * 30)
    single_test_passed = test_video_query()
    
    print()
    
    # 测试批量视频查询
    print("=" * 30)
    batch_test_passed = test_batch_video_query()
    
    print()
    print("=" * 50)
    
    if single_test_passed and batch_test_passed:
        print("🎉 所有测试通过！直接视频处理功能正常工作")
        print("✅ 现在AI会根据整个视频内容进行分析，而不是逐帧分析")
    else:
        print("❌ 部分测试失败，请检查配置和日志")
        if not single_test_passed:
            print("  - 单个视频查询测试失败")
        if not batch_test_passed:
            print("  - 批量视频查询测试失败")

if __name__ == "__main__":
    main()
