"""
SmartVision Flask API 后端服务
提供视频批量处理和智能分析接口
"""

# 加载环境变量（支持.env文件）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装python-dotenv，跳过（可以使用系统环境变量）
    pass

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import tempfile
import os
import io
import base64
import pandas as pd
from datetime import datetime
from config import MODEL_TYPE, MODEL_CONFIG
from model_manager import ModelManager

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化模型管理器
print(f"正在初始化 {MODEL_TYPE} 模型...")
try:
    model_manager = ModelManager()
    print(f"✓ {MODEL_TYPE} 模型初始化成功")
except Exception as e:
    print(f"❌ 模型初始化失败: {e}")
    model_manager = None

# 创建上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 批量处理状态管理（全局）
batch_processing_status = {
    'is_paused': False,
    'is_processing': False,
    'current_file': '',
    'current_index': 0,
    'total_files': 0,
    'current_city': '',
    'total_cities': 0
}


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    video_support_info = {}
    if model_manager:
        video_support_info = model_manager.get_video_support_info()
    
    return jsonify({
        'status': 'ok',
        'model_loaded': model_manager is not None,
        'model_type': MODEL_TYPE,
        'moondream_loaded': model_manager.moondream_model is not None if model_manager else False,
        'video_support': video_support_info,
        'current_model_supports_video': video_support_info.get(MODEL_TYPE, {}).get('supported', False)
    })


@app.route('/api/query', methods=['POST'])
def query_image():
    """
    图像问答接口
    接收图像文件和问题，返回答案
    """
    try:
        # 检查模型是否已加载
        if model_manager is None:
            return jsonify({
                'success': False,
                'error': '模型未初始化，请检查 API Key'
            }), 500
        
        # 检查是否有文件
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': '未找到图像文件'
            }), 400
        
        # 检查是否有问题
        question = request.form.get('question', '')
        if not question:
            return jsonify({
                'success': False,
                'error': '未提供问题'
            }), 400
        
        # 读取图像
        image_file = request.files['image']
        image = Image.open(image_file.stream)
        
        # 保存图像（可选）
        # filename = f"{int(time.time())}_{image_file.filename}"
        # filepath = os.path.join(UPLOAD_FOLDER, filename)
        # image.save(filepath)
        
        # 调用模型API
        print(f"收到问题: {question}")
        result = model_manager.query(image, question)
        answer = result.get('answer', '未能生成答案')
        
        print(f"生成答案: {answer}")
        
        return jsonify({
            'success': True,
            'answer': answer,
            'question': question,
            'request_id': result.get('request_id', 'N/A')
        })
    
    except Exception as e:
        print(f"错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/video-query', methods=['POST'])
def video_query():
    """
    直接视频问答接口
    接收视频文件和问题，直接处理视频而不抽帧
    """
    try:
        # 检查模型是否已加载
        if model_manager is None:
            return jsonify({
                'success': False,
                'error': '模型未初始化，请检查 API Key'
            }), 500
        
        # 检查是否有文件
        if 'video' not in request.files:
            return jsonify({
                'success': False,
                'error': '未找到视频文件'
            }), 400
        
        # 检查是否有问题
        question = request.form.get('question', '')
        if not question:
            return jsonify({
                'success': False,
                'error': '未提供问题'
            }), 400
        
        # 读取视频文件
        video_file = request.files['video']
        
        # 保存视频到临时文件
        import tempfile
        from config import TEMP_DIR
        
        # 创建临时文件 - 使用配置的临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4', dir=TEMP_DIR) as tmp_file:
            file_storage.save(tmp_file.name)
            tmp_video_path = tmp_file.name
        
        try:
            # 调用模型API直接处理视频
            print(f"收到视频问题: {question}")
            result = model_manager.query_video(tmp_video_path, question)
            
            # 检查是否有错误
            has_error = 'error' in result and result.get('error')
            answer = result.get('answer', '未能生成答案')
            
            # 检测错误关键词
            error_keywords = ['失败', '错误', '连接失败', 'API连接失败', '处理失败', 
                             '未初始化', '不支持', 'ProxyError', 'ConnectionResetError',
                             '代理问题', '连接被', '强制关闭', '通义千问API连接失败',
                             'InternalError', 'Algo', 'model_dump', '500', '内部算法错误', 
                             'API内部算法错误', '算法错误']
            
            # 判断是否为错误
            is_error = has_error
            if not is_error and isinstance(answer, str):
                answer_lower = answer.lower()
                is_error = any(keyword.lower() in answer_lower or keyword in answer for keyword in error_keywords)
            
            if is_error:
                print(f"API调用失败: {result.get('error', answer[:100])}")
                return jsonify({
                    'success': False,
                    'answer': answer,
                    'error': result.get('error', answer),
                    'question': question
                }), 500
            else:
                print(f"生成答案: {answer}")
                return jsonify({
                    'success': True,
                    'answer': answer,
                    'question': question,
                    'request_id': result.get('request_id', 'N/A')
                })
        
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_video_path)
            except Exception as e:
                print(f"删除临时文件失败: {e}")
    
    except Exception as e:
        print(f"视频查询错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500





@app.route('/api/detect', methods=['POST'])
def detect_objects():
    """
    目标检测接口
    检测图像中的特定对象并返回边界框坐标
    """
    try:
        if model_manager is None:
            return jsonify({
                'success': False,
                'error': '模型未初始化'
            }), 500
        
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': '未找到图像文件'
            }), 400
        
        # 获取检测目标
        target = request.form.get('target', 'person')
        
        # 读取图像
        image_file = request.files['image']
        image = Image.open(image_file.stream)
        image_width, image_height = image.size
        
        print(f"检测目标: {target}")
        
        # 调用模型检测API
        result = model_manager.detect(image, target)
        detections = result.get('objects', [])
        
        # 转换坐标为像素值
        detected_objects = []
        for obj in detections:
            detected_objects.append({
                'x_min': obj['x_min'],
                'y_min': obj['y_min'],
                'x_max': obj['x_max'],
                'y_max': obj['y_max'],
                'x_min_px': int(obj['x_min'] * image_width),
                'y_min_px': int(obj['y_min'] * image_height),
                'x_max_px': int(obj['x_max'] * image_width),
                'y_max_px': int(obj['y_max'] * image_height),
                'width_px': int((obj['x_max'] - obj['x_min']) * image_width),
                'height_px': int((obj['y_max'] - obj['y_min']) * image_height)
            })
        
        print(f"检测到 {len(detected_objects)} 个 {target}")
        
        return jsonify({
            'success': True,
            'target': target,
            'count': len(detected_objects),
            'objects': detected_objects,
            'image_size': {'width': image_width, 'height': image_height},
            'request_id': result.get('request_id', 'N/A')
        })
    
    except Exception as e:
        print(f"检测错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/batch-query', methods=['POST'])
def batch_query():
    """
    批量问答接口
    对同一张图片提出多个问题
    """
    try:
        if model_manager is None:
            return jsonify({
                'success': False,
                'error': '模型未初始化'
            }), 500
        
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': '未找到图像文件'
            }), 400
        
        # 获取问题列表
        questions_json = request.form.get('questions', '[]')
        import json
        try:
            questions = json.loads(questions_json)
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'error': f'问题列表格式错误: {str(e)}'
            }), 400
        
        if not questions or len(questions) == 0:
            return jsonify({
                'success': False,
                'error': '未提供问题列表或问题列表为空'
            }), 400
        
        # 读取图像
        try:
            image_file = request.files['image']
            image = Image.open(image_file.stream)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'图像读取失败: {str(e)}'
            }), 400
        
        # 批量查询
        results = []
        for question in questions:
            try:
                result = model_manager.query(image, question)
                results.append({
                    'question': question,
                    'answer': result.get('answer', '未能生成答案'),
                    'success': True
                })
            except Exception as e:
                print(f"处理问题 '{question}' 时出错: {str(e)}")
                results.append({
                    'question': question,
                    'answer': '',
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        print(f"批量查询接口错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'批量查询失败: {str(e)}'
        }), 500


@app.route('/api/batch-control', methods=['POST'])
def batch_control():
    """
    批量处理控制接口
    - 暂停/恢复批量处理
    """
    global batch_processing_status
    try:
        data = request.get_json()
        action = data.get('action', '')  # 'pause' 或 'resume'
        
        if action == 'pause':
            batch_processing_status['is_paused'] = True
            print("⏸️  批量处理已暂停")
            return jsonify({
                'success': True,
                'message': '批量处理已暂停',
                'status': batch_processing_status
            })
        elif action == 'resume':
            batch_processing_status['is_paused'] = False
            print("▶️  批量处理已恢复")
            return jsonify({
                'success': True,
                'message': '批量处理已恢复',
                'status': batch_processing_status
            })
        else:
            return jsonify({
                'success': False,
                'error': f'未知的操作: {action}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/batch-status', methods=['GET'])
def batch_status():
    """
    获取批量处理状态接口
    """
    global batch_processing_status
    return jsonify({
        'success': True,
        'status': batch_processing_status
    })


@app.route('/api/video-batch-query', methods=['POST'])
def video_batch_query():
    """
    批量视频直接处理接口
    - 接收多个视频文件（表单字段名：videos）与问题
    - 直接处理每个视频文件，不抽帧
    - 支持按城市分组实时导出Excel文件
    - 返回每个视频的分析结果
    """
    try:
        print("收到批量视频直接处理请求")
        
        if model_manager is None:
            print("模型未初始化")
            return jsonify({
                'success': False,
                'error': '模型未初始化'
            }), 500

        # 校验视频文件
        if 'videos' not in request.files:
            print("未找到视频文件字段")
            return jsonify({
                'success': False,
                'error': '未找到视频文件（字段名应为 videos，可多选）'
            }), 400

        question = request.form.get('question', '').strip()
        if not question:
            print("未提供问题")
            return jsonify({
                'success': False,
                'error': '未提供问题'
            }), 400
        
        # 检查是否需要跳过立即导出（由前端统一导出）
        skip_export = request.form.get('skip_export', 'false').lower() == 'true'

        files = request.files.getlist('videos')
        print(f"收到 {len(files)} 个视频文件")
        print(f"问题: {question}")
        
        # 初始化批量处理状态
        global batch_processing_status
        batch_processing_status['is_processing'] = True
        batch_processing_status['is_paused'] = False
        batch_processing_status['total_files'] = len(files)
        batch_processing_status['current_index'] = 0
        batch_processing_status['current_file'] = ''
        batch_processing_status['current_city'] = ''
        
        # 记录文件大小（不限制）
        for file in files:
            if file.content_length:
                print(f"处理文件: {file.filename}, 大小: {file.content_length/1024/1024:.1f}MB")
        
        # 如果文件数量很多，给出警告但不阻止处理
        if len(files) > 100:
            print(f"警告：检测到 {len(files)} 个文件，处理时间可能较长")

        # 按城市分组处理视频
        import os
        city_groups = {}
        for file_storage in files:
            filename = file_storage.filename
            # 解析文件路径，提取城市信息
            file_dir = os.path.dirname(filename)
            # 统一路径分隔符为正斜杠
            file_dir = file_dir.replace(os.sep, '/')
            path_parts = file_dir.split('/')
            
            # 智能提取城市名称
            city_name = "未知城市"
            if path_parts:
                # 查找dataset或dataset_output在路径中的位置
                dataset_index = -1
                for i, part in enumerate(path_parts):
                    if part == "dataset" or part == "dataset_output":
                        dataset_index = i
                        break
                
                if dataset_index != -1 and dataset_index + 3 < len(path_parts):
                    # 从dataset/dataset_output开始：索引[0]=大洲, 索引[1]=国家, 索引[2]=城市
                    city_name = path_parts[dataset_index + 3]
                elif len(path_parts) >= 3:
                    # 如果没有找到dataset/dataset_output，尝试直接使用路径结构
                    # 假设路径格式为：大洲/国家/城市/...
                    city_name = path_parts[2]  # 第三个部分应该是城市
                else:
                    # 如果路径不完整，使用最后一个部分作为备选
                    city_name = path_parts[-1] if path_parts else "未知城市"
                
                # 从城市名中提取真正的城市名称（去掉年份前缀，如 "2023布里斯班" -> "布里斯班"）
                import re
                # 匹配开头是数字的模式，如 "2023布里斯班"
                match = re.match(r'^\d+(.+)$', city_name)
                if match:
                    city_name = match.group(1)  # 提取城市名部分
            
            if city_name not in city_groups:
                city_groups[city_name] = []
            city_groups[city_name].append(file_storage)
        
        print(f"检测到 {len(city_groups)} 个城市组: {list(city_groups.keys())}")
        
        all_results = []
        video_exports = []  # 改为存储每个视频的导出结果
        batch_processing_status['total_cities'] = len(city_groups)
        
        # 按城市顺序处理
        current_global_index = 0
        for city_name, city_files in city_groups.items():
            batch_processing_status['current_city'] = city_name
            print(f"\n🏙️  开始处理城市: {city_name} (共 {len(city_files)} 个视频)")
            
            for i, file_storage in enumerate(city_files):
                # 检查暂停状态
                while batch_processing_status.get('is_paused', False):
                    import time
                    time.sleep(0.5)  # 暂停时每0.5秒检查一次
                
                # 更新当前处理状态
                current_global_index += 1
                batch_processing_status['current_index'] = current_global_index
                batch_processing_status['current_file'] = file_storage.filename
                
                try:
                    print(f"  处理第 {i+1}/{len(city_files)} 个视频: {file_storage.filename}")
                    
                    # 保存视频到临时文件
                    import tempfile
                    import os
                    
                    # 创建临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                        file_storage.save(tmp_file.name)
                        tmp_video_path = tmp_file.name
                    
                    try:
                        # 直接处理视频
                        result = model_manager.query_video(tmp_video_path, question)
                        
                        # 检查是否有错误
                        has_error = 'error' in result and result.get('error')
                        answer = result.get('answer', '未能生成答案')
                        
                        # 检测错误关键词（API失败的各种情况）
                        error_keywords = ['失败', '错误', '连接失败', 'API连接失败', '处理失败', 
                                         '未初始化', '不支持', 'ProxyError', 'ConnectionResetError',
                                         '代理问题', '连接被', '强制关闭', '通义千问API连接失败',
                                         'InternalError', 'Algo', 'model_dump', '500', '内部算法错误', 
                                         'API内部算法错误', '算法错误']
                        
                        # 判断是否为错误
                        is_error = has_error
                        if not is_error and isinstance(answer, str):
                            # 检查answer中是否包含错误关键词
                            answer_lower = answer.lower()
                            is_error = any(keyword.lower() in answer_lower or keyword in answer for keyword in error_keywords)
                        
                        if is_error:
                            video_result = {
                                'filename': file_storage.filename,
                                'answer': answer,
                                'success': False,
                                'error': result.get('error', answer)  # 如果有error字段就用它，否则用answer作为错误信息
                            }
                            print(f"    ⚠️ API调用失败: {file_storage.filename}, 错误: {result.get('error', answer[:100])}")
                        else:
                            video_result = {
                                'filename': file_storage.filename,
                                'answer': answer,
                                'success': True,
                                'request_id': result.get('request_id', 'N/A')
                            }
                        all_results.append(video_result)
                        
                        print(f"    处理完成: {file_storage.filename}")
                        
                        # 每个视频处理完成后，立即导出Excel文件（除非指定跳过）
                        if not skip_export:
                            export_result = export_single_video_result(video_result)
                            if export_result.get('success'):
                                video_exports.append(export_result)
                                print(f"    ✅ Excel文件已保存: {export_result.get('filepath', '未知路径')}")
                            else:
                                print(f"    ⚠️ Excel导出失败: {export_result.get('error', '未知错误')}")
                        
                        # 定期清理内存，每处理10个视频强制垃圾回收
                        if current_global_index % 10 == 0:
                            import gc
                            gc.collect()
                            print(f"    ✅ 已处理 {current_global_index} 个视频，执行内存清理")
                    
                    finally:
                        # 清理临时文件
                        try:
                            os.unlink(tmp_video_path)
                        except Exception as e:
                            print(f"删除临时文件失败: {e}")
                    
                except Exception as e:
                    print(f"处理视频文件 {file_storage.filename} 时发生错误: {str(e)}")
                    video_result = {
                        'filename': file_storage.filename,
                        'answer': '',
                        'success': False,
                        'error': str(e)
                    }
                    all_results.append(video_result)
                    
                    # 即使失败也尝试导出Excel
                    if not skip_export:
                        export_result = export_single_video_result(video_result)
                        if export_result.get('success'):
                            video_exports.append(export_result)
                    
                    # 单个视频处理失败时继续处理下一个，不中断整个批次
                    continue
            
            print(f"✅ 城市 {city_name} 处理完成，共 {len(city_files)} 个视频")
        
        # 处理完成，重置状态
        batch_processing_status['is_processing'] = False
        batch_processing_status['current_file'] = ''
        batch_processing_status['current_index'] = 0
        
        return jsonify({
            'success': True,
            'question': question,
            'total_files': len(files),
            'total_cities': len(city_groups),
            'results': all_results,
            'video_exports': video_exports,
            'message': f'批量处理完成，共处理 {len(files)} 个视频，每个视频已生成独立的Excel文件'
        })
        
    except Exception as e:
        print(f"批量视频直接处理错误: {str(e)}")
        # 出错时也重置状态
        batch_processing_status['is_processing'] = False
        batch_processing_status['current_file'] = ''
        batch_processing_status['current_index'] = 0
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



def export_single_video_result(video_result):
    """
    为单个视频导出Excel文件
    每个视频生成一个独立的Excel文件
    """
    try:
        import os
        from datetime import datetime
        
        if not video_result:
            return {
                'success': False,
                'error': '没有可导出的数据'
            }
        
        # 准备Excel数据（单个视频只有一行）
        excel_data = [{
            '序号': 1,
            '文件路径': video_result.get('filename', ''),
            '描述性语言': video_result.get('answer', ''),
            '处理状态': '成功' if video_result.get('success', False) else '失败',
            '错误信息': video_result.get('error', '')
        }]
        
        # 创建DataFrame
        df = pd.DataFrame(excel_data)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='视频描述结果', index=False)
            
            # 获取工作表并调整列宽
            worksheet = writer.sheets['视频描述结果']
            worksheet.column_dimensions['A'].width = 8   # 序号
            worksheet.column_dimensions['B'].width = 50  # 文件路径
            worksheet.column_dimensions['C'].width = 80  # 描述性语言
            worksheet.column_dimensions['D'].width = 15  # 处理状态
            worksheet.column_dimensions['E'].width = 40  # 错误信息
        
        output.seek(0)
        
        # 根据视频文件的路径自动创建输出目录
        filename = video_result.get('filename', '')
        if filename:
            # 解析文件路径，提取文件夹结构
            file_dir = os.path.dirname(filename)
            # 统一路径分隔符为正斜杠
            file_dir = file_dir.replace(os.sep, '/')
            
            # 如果路径以'dataset/'或'dataset_output/'开头，去掉这个前缀
            if file_dir.startswith('dataset/'):
                file_dir = file_dir[8:]  # 去掉'dataset/'前缀
            elif file_dir.startswith('dataset_output/'):
                file_dir = file_dir[15:]  # 去掉'dataset_output/'前缀
            
            # 创建输出目录：在D:\无人机步态论文\data_anlyis下按照视频目录结构创建新目录
            output_base_dir = r"D:\无人机步态论文\data_anlyis"
            save_dir = os.path.join(output_base_dir, file_dir)
            
            # 确保输出目录存在，自动创建所有必要的父目录
            os.makedirs(save_dir, exist_ok=True)
            print(f"    ✅ 自动创建输出目录: {save_dir}")
            
            # 使用视频文件名（不含扩展名）作为Excel文件名
            video_basename = os.path.basename(filename)
            video_name_without_ext = os.path.splitext(video_basename)[0]
            
            # 使用视频文件名_street.xlsx作为Excel文件名
            # 检查是否已存在同名文件，如果存在则添加数字后缀
            counter = 1
            excel_filename = f'{video_name_without_ext}_street.xlsx'
            filepath = os.path.join(save_dir, excel_filename)
            
            while os.path.exists(filepath):
                excel_filename = f'{video_name_without_ext}_street_{counter}.xlsx'
                filepath = os.path.join(save_dir, excel_filename)
                counter += 1
            
            print(f"    📁 保存Excel文件: {filepath}")
        else:
            # 如果没有文件路径信息，使用默认命名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            excel_filename = f'视频描述结果_{timestamp}.xlsx'
            filepath = os.path.join(UPLOAD_FOLDER, excel_filename)
            print(f"    📄 使用默认路径保存: {filepath}")
        
        # 保存Excel文件
        with open(filepath, 'wb') as f:
            f.write(output.getvalue())
        
        return {
            'success': True,
            'filename': excel_filename,
            'filepath': filepath,
            'video_filename': filename,
            'message': f'视频 {os.path.basename(filename)} 的Excel文件已生成'
        }
    
    except Exception as e:
        print(f"导出单个视频Excel文件错误: {str(e)}")
        return {
            'success': False,
            'video_filename': video_result.get('filename', ''),
            'error': f'导出Excel文件失败: {str(e)}'
        }


def export_city_results_immediately(city_results, city_name):
    """
    立即导出城市视频结果到Excel文件
    按照视频文件的原始文件夹结构组织Excel文件
    """
    try:
        import os
        from datetime import datetime
        
        if not city_results:
            return {
                'success': False,
                'error': '没有可导出的数据'
            }
        
        # 准备Excel数据
        excel_data = []
        for i, result in enumerate(city_results, 1):
            excel_data.append({
                '序号': i,
                '文件路径': result.get('filename', ''),
                '描述性语言': result.get('answer', ''),
                '处理状态': '成功' if result.get('success', False) else '失败',
                '错误信息': result.get('error', '')
            })
        
        # 创建DataFrame
        df = pd.DataFrame(excel_data)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='视频描述结果', index=False)
            
            # 获取工作表并调整列宽
            worksheet = writer.sheets['视频描述结果']
            worksheet.column_dimensions['A'].width = 8   # 序号
            worksheet.column_dimensions['B'].width = 50  # 文件路径
            worksheet.column_dimensions['C'].width = 80  # 描述性语言
            worksheet.column_dimensions['D'].width = 15  # 处理状态
            worksheet.column_dimensions['E'].width = 40  # 错误信息
        
        output.seek(0)
        
        # 根据视频文件的路径自动创建输出目录并保存到E:\视频步态检测
        if city_results and 'filename' in city_results[0]:
            first_file_path = city_results[0]['filename']
            
            # 解析文件路径，提取文件夹结构（大洲/国家/城市）
            file_dir = os.path.dirname(first_file_path)
            # 统一路径分隔符为正斜杠
            file_dir = file_dir.replace(os.sep, '/')
            
            # 如果路径以'dataset/'或'dataset_output/'开头，去掉这个前缀
            if file_dir.startswith('dataset/'):
                file_dir = file_dir[8:]  # 去掉'dataset/'前缀
            elif file_dir.startswith('dataset_output/'):
                file_dir = file_dir[15:]  # 去掉'dataset_output/'前缀
            
            # 智能提取城市名称和构建路径
            path_parts = file_dir.split('/')
            actual_city_name = city_name  # 使用传入的城市名，如果已经正确解析
            
            # 如果传入的城市名无效，重新解析
            if actual_city_name == "未知城市" or not actual_city_name:
                # 查找dataset或dataset_output在路径中的位置（如果还有的话）
                dataset_index = -1
                for i, part in enumerate(path_parts):
                    if part == "dataset" or part == "dataset_output":
                        dataset_index = i
                        break
                
                if dataset_index != -1 and dataset_index + 3 < len(path_parts):
                    actual_city_name = path_parts[dataset_index + 3]
                    file_dir = '/'.join(path_parts[dataset_index + 1:dataset_index + 4])
                elif len(path_parts) >= 3:
                    actual_city_name = path_parts[2]
                    file_dir = '/'.join(path_parts[:3])
                else:
                    actual_city_name = path_parts[-1] if path_parts else "未知城市"
            
            # 从城市名中提取真正的城市名称（去掉年份前缀）
            import re
            match = re.match(r'^\d+(.+)$', actual_city_name)
            if match:
                actual_city_name = match.group(1)  # 提取城市名部分
            
            # 如果没有有效路径结构，使用默认
            if not file_dir or file_dir == '/' or len(path_parts) < 3:
                if len(path_parts) >= 3:
                    file_dir = '/'.join(path_parts[:3])
            
            # 创建输出目录：在D:\无人机步态论文\data_anlyis下按照视频目录结构创建新目录
            # 例如：视频在 dataset/非洲/肯尼亚/内罗毕/walking.mp4
            # 输出目录：D:\无人机步态论文\data_anlyis\非洲\肯尼亚\内罗毕\
            output_base_dir = r"D:\无人机步态论文\data_anlyis"
            save_dir = os.path.join(output_base_dir, file_dir)
            
            # 确保输出目录存在，自动创建所有必要的父目录
            os.makedirs(save_dir, exist_ok=True)
            print(f"✅ 自动创建输出目录: {save_dir}")
            
            # 使用智能解析的城市名称
            actual_city_name = city_name
            
            # 使用城市名称_street.xlsx作为Excel文件名
            # 检查是否已存在同名文件，如果存在则添加数字后缀
            counter = 1
            filename = f'{actual_city_name}_street.xlsx'
            filepath = os.path.join(save_dir, filename)
            
            while os.path.exists(filepath):
                filename = f'{actual_city_name}_street_{counter}.xlsx'
                filepath = os.path.join(save_dir, filename)
                counter += 1
            
            print(f"📁 自动保存到城市Excel文件: {filepath}")
        else:
            # 如果没有文件路径信息，使用默认命名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{city_name}_视频描述结果_{timestamp}.xlsx'
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            print(f"📄 使用默认路径保存: {filepath}")
        
        # 保存Excel文件
        with open(filepath, 'wb') as f:
            f.write(output.getvalue())
        
        return {
            'success': True,
            'city_name': city_name,
            'filename': filename,
            'filepath': filepath,
            'total_records': len(city_results),
            'success_records': len([r for r in city_results if r.get('success', False)]),
            'failed_records': len([r for r in city_results if not r.get('success', False)]),
            'message': f'城市 {city_name} 的Excel文件已生成，共导出 {len(city_results)} 条记录'
        }
    
    except Exception as e:
        print(f"导出城市 {city_name} Excel文件错误: {str(e)}")
        return {
            'success': False,
            'city_name': city_name,
            'error': f'导出Excel文件失败: {str(e)}'
        }


@app.route('/api/export-excel', methods=['POST'])
def export_to_excel():
    """
    导出视频描述结果到Excel文件
    为每个视频生成一个独立的Excel文件
    """
    try:
        data = request.get_json()
        
        if not data or 'results' not in data:
            return jsonify({
                'success': False,
                'error': '未提供视频描述结果数据'
            }), 400
        
        results = data['results']
        if not results:
            return jsonify({
                'success': False,
                'error': '没有可导出的数据'
            }), 400
        
        # 为每个视频生成一个独立的Excel文件
        exported_files = []
        
        for result in results:
            # 转换结果格式以匹配export_single_video_result函数期望的格式
            video_result = {
                'filename': result.get('filename', ''),
                'answer': result.get('description', ''),
                'success': True,  # 假设都是成功的
                'error': ''
            }
            
            # 调用单个视频导出函数
            export_result = export_single_video_result(video_result)
            
            if export_result.get('success'):
                # 从视频文件名中提取城市名称（用于前端显示兼容）
                import os
                import re
                video_filename = export_result.get('video_filename', '')
                city_name = "未知城市"
                
                if video_filename:
                    file_dir = os.path.dirname(video_filename)
                    file_dir = file_dir.replace(os.sep, '/')
                    path_parts = file_dir.split('/')
                    
                    if path_parts:
                        # 查找dataset或dataset_output在路径中的位置
                        dataset_index = -1
                        for i, part in enumerate(path_parts):
                            if part == "dataset" or part == "dataset_output":
                                dataset_index = i
                                break
                        
                        if dataset_index != -1 and dataset_index + 3 < len(path_parts):
                            city_name = path_parts[dataset_index + 3]
                        elif len(path_parts) >= 3:
                            city_name = path_parts[2]
                        else:
                            city_name = path_parts[-1] if path_parts else "未知城市"
                        
                        # 从城市名中提取真正的城市名称（去掉年份前缀）
                        match = re.match(r'^\d+(.+)$', city_name)
                        if match:
                            city_name = match.group(1)
                
                exported_files.append({
                    'filename': export_result.get('filename', ''),
                    'filepath': export_result.get('filepath', ''),
                    'video_filename': export_result.get('video_filename', ''),
                    'city_name': city_name,  # 添加城市名称用于前端兼容
                    'count': 1  # 每个文件只有1个视频
                })
                print(f"📁 Excel文件已保存: {export_result.get('filepath', '未知路径')}")
            else:
                print(f"⚠️ Excel导出失败: {export_result.get('error', '未知错误')}")
        
        message = f'已为 {len(exported_files)} 个视频生成独立的Excel文件，共 {len(results)} 条记录'
        
        return jsonify({
            'success': True,
            'total_records': len(results),
            'total_cities': len(exported_files),  # 添加total_cities字段用于前端兼容（现在每个文件算一个"城市"）
            'exported_files': exported_files,
            'message': message
        })
        
    except Exception as e:
        print(f"Excel导出错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'导出失败: {str(e)}'
        }), 500


@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """
    下载文件接口 - 支持嵌套路径
    """
    try:
        # 处理可能包含路径的文件名
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            # 如果直接路径不存在，尝试在uploads文件夹下查找
            filepath = os.path.join(UPLOAD_FOLDER, os.path.basename(filename))
            
            if not os.path.exists(filepath):
                return jsonify({
                    'success': False,
                    'error': '文件不存在'
                }), 404
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filename),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"文件下载错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'下载失败: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🎥 SmartVision 批量视频处理系统")
    print("=" * 60)
    print(f"✓ 主模型: {MODEL_TYPE} (视频/图像问答)")
    print(f"✓ 主模型状态: {'已加载' if model_manager else '未加载'}")
    print(f"✓ Moondream模型: {'已加载' if model_manager and model_manager.moondream_model else '未加载'} (目标检测)")
    print("✓ 服务器地址: http://localhost:5000")
    print("✓ API 文档:")
    print("  - GET  /api/health - 健康检查")
    print("  - POST /api/query - 图像问答")
    print("  - POST /api/video-query - 视频直接问答")
    print("  - POST /api/batch-query - 批量问答")
    print("  - POST /api/video-batch-query - 批量视频直接处理")
    print("  - POST /api/detect - 目标检测 (Moondream)")
    print("  - POST /api/export-excel - 导出Excel文件")
    print("  - GET  /api/download/<filename> - 下载文件")
    print("✓ 模型分工:")
    print(f"  - {MODEL_TYPE} (视频/图像问答)")
    print("  - moondream (目标检测)")
    print("=" * 60)
    print("\n正在启动服务器...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)


