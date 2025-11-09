#!/usr/bin/env python3
"""
视频批量处理脚本
用于处理大量视频文件，自动分批上传到API
"""

import os
import requests
import time
import json
import pandas as pd
from pathlib import Path

class VideoBatchProcessor:
    def __init__(self, api_url="http://localhost:5000", max_files_per_batch=5):
        self.api_url = api_url
        self.max_files_per_batch = max_files_per_batch
        self.results = []
    
    def get_video_files(self, folder_path):
        """获取文件夹中的所有视频文件"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
        video_files = []
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    video_files.append(os.path.join(root, file))
        
        return video_files
    
    def group_videos_by_city(self, video_files):
        """按城市分组视频文件"""
        city_groups = {}
        
        for video_path in video_files:
            # 从文件路径中提取城市信息
            # 假设路径格式为：.../大洲/国家/城市/视频名.mp4
            path_parts = video_path.split(os.sep)
            city_name = '未知城市'
            
            # 尝试从路径中提取城市名（通常是倒数第二个部分）
            if len(path_parts) >= 3:
                city_name = path_parts[-2]
            
            if city_name not in city_groups:
                city_groups[city_name] = []
            city_groups[city_name].append(video_path)
        
        return city_groups
    
    def process_batch(self, video_files, prompt):
        """处理一批视频文件，确保文件被正确关闭"""
        print(f"正在处理 {len(video_files)} 个视频文件...")
        
        files = []
        try:
            for video_path in video_files:
                # 使用原始文件名作为文件对象名
                files.append(('videos', open(video_path, 'rb')))
            
            data = {
                'question': prompt  # 新的API使用question参数
            }
            
            response = requests.post(f"{self.api_url}/api/video-batch-query", 
                                   files=files, data=data, timeout=1800)  # 30分钟超时
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ 批次处理成功，处理了 {len(result.get('results', []))} 个视频")
                    return result
                else:
                    print(f"❌ 批次处理失败: {result.get('error')}")
                    return None
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None
        finally:
            # 确保所有文件被正确关闭
            for _, file_obj in files:
                try:
                    file_obj.close()
                except Exception as e:
                    print(f"⚠️  关闭文件失败: {e}")
    
    def process_folder(self, folder_path, prompt):
        """处理整个文件夹的视频"""
        video_files = self.get_video_files(folder_path)
        print(f"找到 {len(video_files)} 个视频文件")
        
        if not video_files:
            print("没有找到视频文件")
            return
        
        # 按城市分组处理
        city_groups = self.group_videos_by_city(video_files)
        cities = list(city_groups.keys())
        
        print(f"视频分布在 {len(cities)} 个城市中")
        
        all_results = []
        failed_videos = []  # 记录失败视频信息
        
        # 按城市顺序处理
        for city_index, city_name in enumerate(cities):
            city_files = city_groups[city_name]
            print(f"\n🏙️  开始处理城市【{city_name}】的 {len(city_files)} 个视频")
            
            # 每个城市内分批处理
            total_batches = (len(city_files) + self.max_files_per_batch - 1) // self.max_files_per_batch
            
            for i in range(0, len(city_files), self.max_files_per_batch):
                batch_num = i // self.max_files_per_batch + 1
                batch_files = city_files[i:i + self.max_files_per_batch]
                
                print(f"📦 处理 {city_name} 的第 {batch_num}/{total_batches} 批 ({len(batch_files)} 个文件)")
                
                result = self.process_batch(batch_files, prompt)
                if result:
                    all_results.extend(result.get('results', []))
                    # 记录失败视频
                    for batch_result in result.get('results', []):
                        if not batch_result.get('success', False):
                            failed_videos.append({
                                '文件名': batch_result.get('filename', ''),
                                '错误信息': batch_result.get('error', '未知错误'),
                                '城市': city_name,
                                '批次': f"{city_name}_批次{batch_num}",
                                '处理时间': time.strftime("%Y-%m-%d %H:%M:%S")
                            })
                
                # 批次间休息，避免服务器过载
                if batch_num < total_batches or city_index < len(cities) - 1:
                    print("⏳ 等待5秒后处理下一批...")
                    time.sleep(5)
            
            print(f"✅ 城市【{city_name}】处理完成")
        
        # 保存所有结果（按城市分组保存）
        self.save_results_by_city(all_results, folder_path)
        
        # 保存失败视频统计
        if failed_videos:
            self.save_failed_statistics(failed_videos, folder_path)
        
        print(f"\n🎉 全部处理完成！共处理 {len(all_results)} 个视频，覆盖 {len(cities)} 个城市")
        if failed_videos:
            print(f"⚠️  其中有 {len(failed_videos)} 个视频处理失败，已生成失败统计报告")
    
    def save_results_by_city(self, results, folder_path):
        """按城市分组保存结果到对应文件夹"""
        # 创建主输出文件夹
        output_base = "dataset分析"
        os.makedirs(output_base, exist_ok=True)
        
        # 按城市分组结果
        city_results = {}
        for result in results:
            # 从文件名中提取城市信息
            file_path = result.get('filename', '')
            path_parts = file_path.split(os.sep)
            
            # 提取大洲、国家、城市信息（假设路径格式：.../大洲/国家/城市/视频名.mp4）
            if len(path_parts) >= 4:
                continent = path_parts[-4] if len(path_parts) >= 4 else '未知大洲'
                country = path_parts[-3] if len(path_parts) >= 3 else '未知国家'
                city = path_parts[-2] if len(path_parts) >= 2 else '未知城市'
                
                city_key = f"{continent}/{country}/{city}"
                if city_key not in city_results:
                    city_results[city_key] = []
                city_results[city_key].append(result)
            else:
                # 如果路径格式不符合预期，保存到未知文件夹
                city_key = "未知/未知/未知"
                if city_key not in city_results:
                    city_results[city_key] = []
                city_results[city_key].append(result)
        
        # 为每个城市创建Excel文件
        excel_files = []
        for city_key, city_results_list in city_results.items():
            # 创建对应的文件夹结构
            city_folder = os.path.join(output_base, city_key)
            os.makedirs(city_folder, exist_ok=True)
            
            # 创建Excel文件
            excel_file = os.path.join(city_folder, "street.xlsx")
            
            # 转换结果格式为DataFrame
            df_data = []
            for result in city_results_list:
                df_data.append({
                    '文件名': result.get('filename', ''),
                    '描述结果': result.get('answer', ''),
                    '处理状态': '成功' if result.get('success', False) else '失败',
                    '错误信息': result.get('error', '')
                })
            
            df = pd.DataFrame(df_data)
            df.to_excel(excel_file, index=False, engine='openpyxl')
            excel_files.append(excel_file)
            
            print(f"📊 {city_key} 的结果已保存到: {excel_file}")
        
        # 同时保存一个总的JSON文件（可选）
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        json_file = f"视频描述结果_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 总结果JSON已保存到: {json_file}")
        
        return json_file, excel_files
    
    def save_city_results_immediately(self, city_results, city_name):
        """立即保存单个城市的结果到Excel文件"""
        # 创建主输出文件夹
        output_base = "dataset分析"
        os.makedirs(output_base, exist_ok=True)
        
        # 从第一个结果中提取路径信息
        if city_results:
            first_result = city_results[0]
            file_path = first_result.get('filename', '')
            path_parts = file_path.split(os.sep)
            
            # 提取大洲、国家信息（假设路径格式：.../大洲/国家/城市/视频名.mp4）
            if len(path_parts) >= 4:
                continent = path_parts[-4] if len(path_parts) >= 4 else '未知大洲'
                country = path_parts[-3] if len(path_parts) >= 3 else '未知国家'
                
                # 创建对应的文件夹结构
                city_folder = os.path.join(output_base, continent, country, city_name)
                os.makedirs(city_folder, exist_ok=True)
                
                # 创建Excel文件
                excel_file = os.path.join(city_folder, "street.xlsx")
                
                # 转换结果格式为DataFrame
                df_data = []
                for result in city_results:
                    df_data.append({
                        '文件名': result.get('filename', ''),
                        '描述结果': result.get('answer', ''),
                        '处理状态': '成功' if result.get('success', False) else '失败',
                        '错误信息': result.get('error', '')
                    })
                
                df = pd.DataFrame(df_data)
                df.to_excel(excel_file, index=False, engine='openpyxl')
                
                print(f"📊 城市【{city_name}】结果已保存到: {excel_file}")
                return excel_file
        
        # 如果路径格式不符合预期，保存到默认位置
        default_folder = os.path.join(output_base, "未知", "未知", city_name)
        os.makedirs(default_folder, exist_ok=True)
        excel_file = os.path.join(default_folder, "street.xlsx")
        
        df_data = []
        for result in city_results:
            df_data.append({
                '文件名': result.get('filename', ''),
                '描述结果': result.get('answer', ''),
                '处理状态': '成功' if result.get('success', False) else '失败',
                '错误信息': result.get('error', '')
            })
        
        df = pd.DataFrame(df_data)
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        print(f"📊 城市【{city_name}】结果已保存到默认位置: {excel_file}")
        return excel_file
    
    def save_failed_statistics(self, failed_videos, folder_path):
        """保存失败视频统计到Excel文件"""
        if not failed_videos:
            print("✅ 没有失败视频，无需生成统计报告")
            return
        
        # 创建失败统计文件夹
        failed_stats_dir = "失败视频统计"
        os.makedirs(failed_stats_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        excel_file = os.path.join(failed_stats_dir, f"失败视频统计_{timestamp}.xlsx")
        
        # 创建DataFrame
        df_data = []
        for failed in failed_videos:
            df_data.append({
                '文件名': failed['文件名'],
                '城市': failed['城市'],
                '批次': failed['批次'],
                '错误信息': failed['错误信息'],
                '处理时间': failed['处理时间']
            })
        
        df = pd.DataFrame(df_data)
        
        # 保存Excel文件
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 主表：所有失败视频详情
            df.to_excel(writer, sheet_name='失败视频详情', index=False)
            
            # 统计表：按城市和错误类型统计
            # 按城市统计
            city_stats = df.groupby('城市').size().reset_index(name='失败数量')
            city_stats.to_excel(writer, sheet_name='按城市统计', index=False)
            
            # 按错误类型统计
            error_stats = df.groupby('错误信息').size().reset_index(name='出现次数')
            error_stats = error_stats.sort_values('出现次数', ascending=False)
            error_stats.to_excel(writer, sheet_name='按错误类型统计', index=False)
            
            # 按批次统计
            batch_stats = df.groupby('批次').size().reset_index(name='失败数量')
            batch_stats.to_excel(writer, sheet_name='按批次统计', index=False)
            
            # 汇总统计
            summary_data = {
                '统计项目': ['总视频数', '失败视频数', '成功率', '失败率', '涉及城市数', '错误类型数'],
                '数值': [
                    len(failed_videos) + sum(1 for failed in failed_videos),  # 总视频数（估算）
                    len(failed_videos),
                    f"{((len(failed_videos) + sum(1 for failed in failed_videos) - len(failed_videos)) / (len(failed_videos) + sum(1 for failed in failed_videos)) * 100):.1f}%" if (len(failed_videos) + sum(1 for failed in failed_videos)) > 0 else '0%',
                    f"{(len(failed_videos) / (len(failed_videos) + sum(1 for failed in failed_videos)) * 100):.1f}%" if (len(failed_videos) + sum(1 for failed in failed_videos)) > 0 else '0%',
                    df['城市'].nunique(),
                    df['错误信息'].nunique()
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='汇总统计', index=False)
        
        print(f"📊 失败视频统计已保存到: {excel_file}")
        print(f"📋 统计包含 {len(failed_videos)} 个失败视频，分布在 {df['城市'].nunique()} 个城市")
        print(f"🔍 主要错误类型: {error_stats.iloc[0]['错误信息'] if len(error_stats) > 0 else '无'}")
        
        return excel_file

def main():
    """主函数"""
    print("🎬 视频批量处理工具")
    print("=" * 50)
    
    # 配置参数
    folder_path = input("请输入视频文件夹路径: ").strip()
    if not os.path.exists(folder_path):
        print("❌ 文件夹不存在")
        return
    
    prompt = input("请输入描述提示词: ").strip()
    if not prompt:
        prompt = "请用中文描述视频中的主要内容和场景"
    
    max_files = int(input("每批处理文件数 (默认5): ") or "5")
    
    # 创建处理器
    processor = VideoBatchProcessor(max_files_per_batch=max_files)
    
    # 开始处理
    processor.process_folder(folder_path, prompt)

if __name__ == "__main__":
    main()

