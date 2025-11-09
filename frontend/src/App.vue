<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 顶部导航栏 -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo-section">
            <el-icon :size="32" color="#409EFF"><Picture /></el-icon>
            <div class="title-group">
              <h1>SmartVision批量视频处理系统</h1>
              <span class="subtitle">基于 AI 的智能视频分析平台</span>
            </div>
          </div>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="app-main">
        <el-row :gutter="0" class="main-content-row">
          <!-- 左侧：文件上传区域 -->
          <el-col :span="10" class="upload-section">
            <el-card shadow="hover" class="upload-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Upload /></el-icon>
                  <span>{{ activeTab === 'video' ? '视频上传' : '图片上传' }}</span>
                </div>
              </template>

              <!-- 图片上传 -->
              <el-upload
                v-if="activeTab !== 'video'"
                ref="upload"
                class="upload-component"
                drag
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleImageChange"
                accept="image/*"
              >
                <div v-if="!imagePreview" class="upload-placeholder">
                  <el-icon class="upload-icon" :size="60"><Plus /></el-icon>
                  <div class="upload-text">
                    <div class="el-upload__text">
                      拖拽图片到此处或<em>点击上传</em>
                    </div>
                    <div class="el-upload__tip">支持 JPG、PNG、GIF 等格式</div>
                  </div>
                </div>
                <div v-else class="image-preview-container">
                  <canvas 
                    ref="imageCanvas" 
                    class="image-canvas"
                    @click="clearDetections"
                  ></canvas>
                </div>
              </el-upload>

              <!-- 视频上传 -->
              <el-upload
                v-if="activeTab === 'video'"
                ref="videoUpload"
                class="upload-component"
                drag
                multiple
                :auto-upload="false"
                :on-change="handleVideoChange"
                :on-remove="handleVideoRemove"
                accept="video/*"
                webkitdirectory
                directory
              >
                <div v-if="videoFiles.length === 0" class="upload-placeholder">
                  <el-icon class="upload-icon" :size="60"><Plus /></el-icon>
                  <div class="upload-text">
                    <div class="el-upload__text">
                      拖拽视频到此处或<em>点击上传</em>
                    </div>
                    <div class="el-upload__tip">支持常见视频格式，可多选或选择整个文件夹</div>
                  </div>
                </div>
                <div v-else class="video-list-container">
                  <div v-for="(file, index) in videoFiles" :key="index" class="video-item">
                    <el-icon><VideoPlay /></el-icon>
                    <span class="video-name">{{ file.name }}</span>
                    <span class="video-size">{{ formatFileSize(file.size) }}</span>
                  </div>
                </div>
              </el-upload>

              <el-divider v-if="imagePreview || videoFiles.length > 0" />

              <div v-if="imagePreview && activeTab !== 'video'" class="upload-actions">
                <el-space wrap :size="10">
                  <el-button type="primary" :icon="Refresh" @click="$refs.upload.$el.querySelector('input').click()">
                    更换图片
                  </el-button>
                  <el-button :icon="Delete" @click="clearImage">清除</el-button>
                </el-space>
              </div>

              <div v-if="activeTab === 'video'" class="upload-actions">
                <el-space wrap :size="10">
                  <el-button type="primary" :icon="Upload" @click="selectFiles">
                    上传文件
                  </el-button>
                  <el-button type="success" :icon="Folder" @click="selectFolder">
                    上传文件夹
                  </el-button>
                  <el-button v-if="videoFiles.length > 0" :icon="Delete" @click="clearVideoList">清空列表</el-button>
                </el-space>
                
              </div>

              <el-descriptions v-if="imageInfo && activeTab !== 'video'" :column="1" border class="image-info">
                <el-descriptions-item label="文件名">{{ imageInfo.name }}</el-descriptions-item>
                <el-descriptions-item label="大小">{{ formatFileSize(imageInfo.size) }}</el-descriptions-item>
              </el-descriptions>

              <el-descriptions v-if="videoFiles.length > 0 && activeTab === 'video'" :column="1" border class="image-info">
                <el-descriptions-item label="视频数量">{{ videoFiles.length }} 个</el-descriptions-item>
                <el-descriptions-item label="总大小">{{ formatFileSize(videoFiles.reduce((sum, f) => sum + f.size, 0)) }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>

          <!-- 右侧：问答区域 -->
          <el-col :span="14" class="query-section">
            <el-card shadow="hover" class="query-card">
              <template #header>
                <div class="card-header">
                  <el-icon><ChatDotRound /></el-icon>
                  <span>智能问答</span>
                </div>
              </template>

              <el-tabs v-model="activeTab">
                <el-tab-pane label="视频批量描述" name="video">
                  
                  
                  <el-form label-position="top">
                    <el-form-item label="提示词（prompt）">
                      <el-input
                        v-model="videoPrompt"
                        type="textarea"
                        :rows="5"
                        placeholder="例如：请用一句中文总结视频内容"
                        :disabled="videoLoading"
                        show-word-limit
                        maxlength="2000"
                      />
                    </el-form-item>


                    <el-form-item>
                      <el-space wrap>
                        <el-button
                          :type="videoFiles.length > 5 ? 'warning' : 'primary'"
                          size="large"
                          :loading="videoLoading || smartBatchLoading"
                          :disabled="videoFiles.length === 0 || !videoPrompt.trim() || isPaused"
                          :icon="videoFiles.length > 5 ? MagicStick : Search"
                          @click="handleBatchProcess"
                        >
                          {{ getButtonText() }}
                        </el-button>
                        
                        <!-- 暂停/恢复按钮 -->
                        <el-button
                          v-if="smartBatchLoading || videoLoading"
                          :type="isPaused ? 'success' : 'warning'"
                          size="large"
                          :icon="isPaused ? VideoPlay : VideoPause"
                          @click="togglePause"
                        >
                          {{ isPaused ? '恢复处理' : '暂停处理' }}
                        </el-button>
                      </el-space>
                    </el-form-item>

                    <!-- 状态栏：显示当前处理的视频 -->
                    <el-alert 
                      v-if="smartBatchLoading || videoLoading" 
                      :title="isPaused ? '⏸️ 处理已暂停' : '📹 正在处理'" 
                      :type="isPaused ? 'warning' : 'info'" 
                      :closable="false"
                      style="margin-bottom: 12px;"
                    >
                      <template #default>
                        <div style="margin-top: 8px; font-size: 14px;">
                          <div v-if="batchStatus.current_file" style="margin-bottom: 4px;">
                            <strong>当前视频：</strong>
                            <span style="color: #409EFF;">{{ batchStatus.current_file }}</span>
                          </div>
                          <div>
                            <strong>进度：</strong>
                            {{ batchStatus.current_index || 0 }}/{{ batchStatus.total_files || videoFiles.length || 0 }} 个视频
                            <span v-if="batchStatus.current_city" style="margin-left: 12px;">
                              | 当前城市：<span style="color: #67C23A;">{{ batchStatus.current_city }}</span>
                            </span>
                            <span v-if="!batchStatus.current_file && !batchStatus.current_city" style="margin-left: 12px; color: #909399;">
                              (等待处理中...)
                            </span>
                          </div>
                        </div>
                      </template>
                    </el-alert>

                    <!-- 智能批量处理进度 -->
                    <el-alert v-if="smartBatchLoading" title="智能批量处理进度" type="info" :closable="false">
                      <template #default>
                        <div style="margin-top: 12px">
                          <el-progress 
                            :percentage="Math.round((smartBatchProgress.current / smartBatchProgress.total) * 100)"
                            :status="smartBatchLoading ? 'active' : 'success'"
                          />
                          <p style="margin-top: 8px; font-size: 14px; color: #666;">
                            第 {{ smartBatchProgress.currentBatch }}/{{ smartBatchProgress.totalBatches }} 批 | 
                            已处理 {{ smartBatchProgress.current }}/{{ smartBatchProgress.total }} 个视频
                          </p>
                        </div>
                      </template>
                    </el-alert>

                    <el-alert v-if="videoResults.length > 0 || smartBatchLoading || videoLoading" title="分析结果" type="success" :closable="false">
                      <template #default>
                        <div style="margin-top: 12px">
                          <el-button 
                            type="success" 
                            :icon="Download" 
                            @click="exportToExcel"
                            :loading="exportLoading"
                            :disabled="videoResults.length === 0"
                          >
                            {{ exportLoading ? '导出中' : videoResults.length > 0 ? `导出Excel (已处理 ${videoResults.length} 条)` : '导出Excel' }}
                          </el-button>
                          <span v-if="smartBatchLoading || videoLoading" style="margin-left: 12px; color: #909399; font-size: 13px;">
                            💡 提示：可在处理过程中随时导出已完成的记录
                          </span>
                        </div>
                      </template>
                    </el-alert>

                    <el-timeline v-if="videoResults.length > 0" style="margin-top: 12px">
                      <el-timeline-item
                        v-for="(vr, idx) in videoResults"
                        :key="idx"
                        :timestamp="vr.filename"
                        placement="top"
                      >
                        <el-card>
                          <div class="answer-content">
                            <div class="question-text">
                              <el-tag type="info" effect="plain">处理方式</el-tag>
                              <span>直接视频分析</span>
                            </div>
                            <el-divider />
                            <div class="answer-text">
                              <el-tag type="success" effect="plain">描述</el-tag>
                              <span>{{ vr.description }}</span>
                            </div>
                          </div>
                        </el-card>
                      </el-timeline-item>
                    </el-timeline>
                  </el-form>
                </el-tab-pane>

                <el-tab-pane label="智能问答" name="query">
                  <el-form label-position="top">
                    <el-form-item label="您的问题">
                      <el-input
                        v-model="question"
                        type="textarea"
                        :rows="5"
                        placeholder="请输入您的问题（建议使用英文以获得更好效果）"
                        :disabled="!imageFile || loading"
                        @keyup.ctrl.enter="submitQuery"
                        show-word-limit
                        maxlength="500"
                      />
                    </el-form-item>

                    <el-form-item>
                      <el-space wrap>
                        <el-button
                          type="primary"
                          size="large"
                          :loading="loading"
                          :disabled="!imageFile || !question.trim()"
                          :icon="Search"
                          @click="submitQuery"
                        >
                          {{ loading ? '分析中' : '提交问题' }}
                        </el-button>
                        <el-button
                          v-if="imageFile"
                          type="success"
                          size="large"
                          :loading="batchLoading"
                          :icon="MagicStick"
                          @click="submitBatchQuery"
                        >
                          {{ batchLoading ? '批量分析中' : '一键批量分析' }}
                        </el-button>
                      </el-space>
                    </el-form-item>
                  </el-form>
                </el-tab-pane>

                <el-tab-pane label="目标检测" name="detect">
                  <el-form label-position="top">
                    <el-form-item label="检测目标">
                      <el-select 
                        v-model="detectTarget" 
                        placeholder="选择要检测的目标"
                        size="large"
                        style="width: 100%"
                      >
                        <el-option label="人物 (person)" value="person" />
                        <el-option label="人脸 (face)" value="face" />
                        <el-option label="汽车 (car)" value="car" />
                        <el-option label="狗 (dog)" value="dog" />
                        <el-option label="猫 (cat)" value="cat" />
                        <el-option label="手机 (phone)" value="phone" />
                        <el-option label="书 (book)" value="book" />
                        <el-option label="椅子 (chair)" value="chair" />
                        <el-option label="桌子 (table)" value="table" />
                      </el-select>
                    </el-form-item>

                    <el-form-item>
                      <el-button
                        type="primary"
                        size="large"
                        :loading="detectLoading"
                        :disabled="!imageFile"
                        :icon="Aim"
                        @click="submitDetection"
                      >
                        {{ detectLoading ? '检测中' : '开始检测' }}
                      </el-button>
                    </el-form-item>

                    <el-alert
                      v-if="detectionResult"
                      :title="`检测到 ${detectionResult.count} 个 ${detectTarget}`"
                      type="success"
                      :closable="false"
                      style="margin-top: 16px"
                    >
                      <template #default>
                        <div style="margin-top: 8px">
                          <el-tag v-for="(obj, idx) in detectionResult.objects" :key="idx" style="margin: 4px">
                            目标 {{ idx + 1 }}: 
                            位置 ({{ obj.x_min_px }}, {{ obj.y_min_px }}) - 
                            大小 {{ obj.width_px }}x{{ obj.height_px }}
                          </el-tag>
                        </div>
                      </template>
                    </el-alert>
                  </el-form>
                </el-tab-pane>
              </el-tabs>

            </el-card>

            <!-- 答案显示区域 -->
            <el-card v-if="answers.length > 0" shadow="hover" class="answers-card">
              <template #header>
                <div class="card-header">
                  <div>
                    <el-icon><Document /></el-icon>
                    <span>问答历史</span>
                    <el-badge :value="answers.length" class="badge" />
                  </div>
                  <el-button text :icon="Delete" @click="clearAnswers">清空</el-button>
                </div>
              </template>

              <el-timeline>
                <el-timeline-item
                  v-for="(item, index) in answers"
                  :key="index"
                  :timestamp="item.timestamp"
                  placement="top"
                  :color="index === 0 ? '#409EFF' : '#909399'"
                >
                  <el-card class="answer-card">
                    <div class="answer-content">
                      <div class="question-text">
                        <el-tag type="info" effect="plain">Q{{ answers.length - index }}</el-tag>
                        <span>{{ item.question }}</span>
                      </div>
                      <el-divider />
                      <div class="answer-text">
                        <el-tag type="success" effect="plain">A</el-tag>
                        <span>{{ item.answer }}</span>
                      </div>
                    </div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { 
  Plus, 
  Upload, 
  Refresh, 
  Delete, 
  Search, 
  MagicStick,
  ChatDotRound,
  Document,
  Picture,
  Aim,
  VideoPlay,
  VideoPause,
  Download
} from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    Plus,
    Upload,
    Refresh,
    Delete,
    Search,
    MagicStick,
    ChatDotRound,
    Document,
    Picture,
    Aim,
    VideoPlay,
    VideoPause,
    Download
  },
  setup() {
    const imageFile = ref(null)
    const imagePreview = ref('')
    const imageInfo = ref(null)
    const question = ref('')
    const answers = ref([])
    const loading = ref(false)
    const batchLoading = ref(false)
    const activeTab = ref('video')
    const detectTarget = ref('person')
    const detectLoading = ref(false)
    const detectionResult = ref(null)
    const imageCanvas = ref(null)
    const originalImage = ref(null)

    // 视频批量描述
    const videoPrompt = ref('')
    const videoFiles = ref([])
    const videoLoading = ref(false)
    const videoResults = ref([])
    const exportLoading = ref(false)
    const smartBatchLoading = ref(false)
    const smartBatchProgress = ref({ current: 0, total: 0, currentBatch: 0, totalBatches: 0 })
    
    // 批量处理控制状态
    const isPaused = ref(false)
    const batchStatus = ref({
      is_processing: false,
      is_paused: false,
      current_file: '',
      current_index: 0,
      total_files: 0,
      current_city: '',
      total_cities: 0
    })
    let statusPollInterval = null



    // 处理图片选择
    const handleImageChange = (file) => {
      imageFile.value = file.raw
      imagePreview.value = URL.createObjectURL(file.raw)
      imageInfo.value = {
        name: file.name,
        size: file.size
      }
      
      // 加载图片到 canvas
      const img = new Image()
      img.onload = () => {
        originalImage.value = img
        drawImageOnCanvas(img)
        ElMessage.success('图片加载成功')
      }
      img.src = imagePreview.value
      
      // 清除之前的检测结果
      detectionResult.value = null
    }

    // 在 canvas 上绘制图片
    const drawImageOnCanvas = (img, detections = null) => {
      if (!imageCanvas.value) return
      
      const canvas = imageCanvas.value
      const ctx = canvas.getContext('2d')
      
      // 设置 canvas 尺寸
      const maxWidth = canvas.parentElement.clientWidth
      const maxHeight = 600
      let width = img.width
      let height = img.height
      
      // 保持宽高比缩放
      if (width > maxWidth) {
        height = (maxWidth / width) * height
        width = maxWidth
      }
      if (height > maxHeight) {
        width = (maxHeight / height) * width
        height = maxHeight
      }
      
      canvas.width = width
      canvas.height = height
      
      // 绘制图片
      ctx.drawImage(img, 0, 0, width, height)
      
      // 绘制检测框
      if (detections && detections.length > 0) {
        ctx.strokeStyle = '#f56c6c'
        ctx.lineWidth = 3
        ctx.font = '16px Arial'
        ctx.fillStyle = '#f56c6c'
        
        const scaleX = width / img.width
        const scaleY = height / img.height
        
        detections.forEach((obj, idx) => {
          const x = obj.x_min_px * scaleX
          const y = obj.y_min_px * scaleY
          const w = obj.width_px * scaleX
          const h = obj.height_px * scaleY
          
          // 绘制边界框
          ctx.strokeRect(x, y, w, h)
          
          // 绘制标签背景
          const label = `${detectTarget.value} ${idx + 1}`
          const textWidth = ctx.measureText(label).width
          ctx.fillStyle = '#f56c6c'
          ctx.fillRect(x, y - 25, textWidth + 10, 25)
          
          // 绘制标签文字
          ctx.fillStyle = 'white'
          ctx.fillText(label, x + 5, y - 7)
        })
      }
    }

    // 清除检测结果
    const clearDetections = () => {
      if (detectionResult.value && originalImage.value) {
        detectionResult.value = null
        drawImageOnCanvas(originalImage.value)
      }
    }

    // 清除图片
    const clearImage = () => {
      imageFile.value = null
      imagePreview.value = ''
      imageInfo.value = null
      answers.value = []
      detectionResult.value = null
      originalImage.value = null
    }

    // 清空答案
    const clearAnswers = () => {
      answers.value = []
    }

    // 格式化文件大小
    const formatFileSize = (bytes) => {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
    }

    // 获取当前时间
    const getTimestamp = () => {
      const now = new Date()
      return now.toLocaleTimeString('zh-CN')
    }

    // 提交单个问题
    const submitQuery = async () => {
      if (!imageFile.value || !question.value.trim()) {
        ElMessage.warning('请先上传图片并输入问题')
        return
      }

      loading.value = true
      const formData = new FormData()
      formData.append('image', imageFile.value)
      formData.append('question', question.value)

      try {
        const response = await axios.post('/api/query', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        if (response.data.success) {
          answers.value.unshift({
            question: response.data.question,
            answer: response.data.answer,
            timestamp: getTimestamp()
          })
          ElMessage.success('回答生成成功')
          question.value = '' // 清空问题
        } else {
          ElMessage.error(response.data.error || '查询失败')
        }
      } catch (error) {
        ElMessage.error('请求失败: ' + (error.response?.data?.error || error.message))
      } finally {
        loading.value = false
      }
    }

    // 批量问答
    const submitBatchQuery = async () => {
      if (!imageFile.value) {
        ElMessage.warning('请先上传图片')
        return
      }

      // 使用默认问题列表进行批量问答
      const defaultQuestions = [
        "What's in this image?",
        "Describe this image in detail",
        "What objects can you see?",
        "What is the person wearing?",
        "What are the main colors?",
        "Where is this photo taken?",
        "What is the mood or atmosphere?",
        "Count the number of people",
      ]

      batchLoading.value = true
      const formData = new FormData()
      formData.append('image', imageFile.value)
      formData.append('questions', JSON.stringify(defaultQuestions))

      try {
        const response = await axios.post('/api/batch-query', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        if (response.data.success) {
          const timestamp = getTimestamp()
          response.data.results.forEach((result) => {
            if (result.success) {
              answers.value.unshift({
                question: result.question,
                answer: result.answer,
                timestamp: timestamp
              })
            }
          })
          ElMessage.success(`成功生成 ${response.data.results.length} 个答案`)
        } else {
          ElMessage.error(response.data.error || '批量查询失败')
        }
      } catch (error) {
        ElMessage.error('批量查询失败: ' + (error.response?.data?.error || error.message))
      } finally {
        batchLoading.value = false
      }
    }

    // 提交目标检测
    const submitDetection = async () => {
      if (!imageFile.value) {
        ElMessage.warning('请先上传图片')
        return
      }

      detectLoading.value = true
      const formData = new FormData()
      formData.append('image', imageFile.value)
      formData.append('target', detectTarget.value)

      try {
        const response = await axios.post('/api/detect', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        if (response.data.success) {
          detectionResult.value = response.data
          
          // 在 canvas 上绘制检测结果
          if (originalImage.value) {
            drawImageOnCanvas(originalImage.value, response.data.objects)
          }
          
          ElMessage.success(`检测到 ${response.data.count} 个 ${detectTarget.value}`)
        } else {
          ElMessage.error(response.data.error || '检测失败')
        }
      } catch (error) {
        ElMessage.error('检测失败: ' + (error.response?.data?.error || error.message))
      } finally {
        detectLoading.value = false
      }
    }

    // 处理视频选择/移除
    const handleVideoChange = (file, fileList) => {
      videoFiles.value = fileList.map(f => f.raw)
    }
    const handleVideoRemove = (file, fileList) => {
      videoFiles.value = fileList.map(f => f.raw)
    }
    const clearVideoList = () => {
      videoFiles.value = []
      videoResults.value = []
    }

    // 提交视频批量描述（使用直接视频处理）
    const submitVideoBatch = async () => {
      if (videoFiles.value.length === 0 || !videoPrompt.value.trim()) {
        ElMessage.warning('请先选择视频并填写提示词')
        return
      }

      videoLoading.value = true
      isPaused.value = false
      
      // 初始化结果列表，以便随时可以导出
      videoResults.value = []
      
      // 初始化状态显示
      batchStatus.value = {
        is_processing: true,
        is_paused: false,
        current_file: '',
        current_index: 0,
        total_files: videoFiles.value.length,
        current_city: '',
        total_cities: 0
      }
      
      // 开始状态轮询（在请求发送前就开始，这样能及时获取后端状态）
      startStatusPolling()
      
      try {
        const formData = new FormData()
        videoFiles.value.forEach(v => formData.append('videos', v))
        formData.append('question', videoPrompt.value)

        const resp = await axios.post('/api/video-batch-query', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        if (resp.data.success) {
          // 转换结果格式以兼容现有显示逻辑
          videoResults.value = resp.data.results.map(result => ({
            filename: result.filename,
            frames_used: 1, // 直接视频处理，相当于1帧
            answers: [result.answer],
            description: result.answer
          }))
          ElMessage.success(`分析完成，共 ${videoResults.value.length} 个视频`)
        } else {
          ElMessage.error(resp.data.error || '分析失败')
        }
      } catch (e) {
        ElMessage.error('请求失败: ' + (e.response?.data?.error || e.message))
      } finally {
        videoLoading.value = false
        stopStatusPolling()
      }
    }

    // 选择文件
    const selectFiles = () => {
      const input = document.createElement('input')
      input.type = 'file'
      input.multiple = true
      input.accept = 'video/*'
      
      input.onchange = (e) => {
        const files = Array.from(e.target.files)
        const MAX_FILES = 10
        
        // 检查文件数量
        if (files.length > MAX_FILES) {
          ElMessage.error(`最多只能选择 ${MAX_FILES} 个文件`)
          return
        }
        
        const filteredVideoFiles = files.filter(file => {
          const fileName = file.name.toLowerCase()
          const isValidFormat = fileName.endsWith('.mp4') || fileName.endsWith('.avi') || 
                               fileName.endsWith('.mov') || fileName.endsWith('.mkv') || 
                               fileName.endsWith('.wmv') || fileName.endsWith('.flv') ||
                               fileName.endsWith('.webm') || fileName.endsWith('.m4v')
          
          return isValidFormat
        })
        
        if (filteredVideoFiles.length > 0) {
          // 直接使用原始文件对象，保留路径信息
          videoFiles.value = filteredVideoFiles
          ElMessage.success(`成功加载 ${filteredVideoFiles.length} 个视频文件`)
        } else {
          ElMessage.warning('没有选择有效的视频文件')
        }
      }
      
      input.click()
    }
    
    // 选择文件夹
    const selectFolder = () => {
      // 检查浏览器是否支持文件夹选择
      if (!('webkitdirectory' in document.createElement('input'))) {
        ElMessage.warning('当前浏览器不支持文件夹选择功能，请使用Chrome或Edge浏览器，或使用文件多选功能')
        return
      }
      
      const input = document.createElement('input')
      input.type = 'file'
      input.webkitdirectory = true
      input.multiple = true
      input.accept = 'video/*'
      
      input.onchange = (e) => {
        const files = Array.from(e.target.files)
        
        console.log('选择的文件列表:', files)
        
        if (files.length === 0) {
          ElMessage.warning('没有选择任何文件，请确保文件夹中有视频文件')
          return
        }
        
        const filteredVideoFiles = files.filter(file => {
          const fileName = file.name.toLowerCase()
          const isValidFormat = fileName.endsWith('.mp4') || fileName.endsWith('.avi') || 
                               fileName.endsWith('.mov') || fileName.endsWith('.mkv') || 
                               fileName.endsWith('.wmv') || fileName.endsWith('.flv') ||
                               fileName.endsWith('.webm') || fileName.endsWith('.m4v')
          
          return isValidFormat
        })
        
        console.log('过滤后的视频文件:', filteredVideoFiles)
        
        if (filteredVideoFiles.length > 0) {
          // 直接使用原始文件对象，保留路径信息
          videoFiles.value = filteredVideoFiles
          ElMessage.success(`成功加载 ${filteredVideoFiles.length} 个视频文件`)
          
          // 如果文件数量很多，给出提示
          if (filteredVideoFiles.length > 50) {
            ElMessage.warning(`检测到 ${filteredVideoFiles.length} 个视频文件，处理时间可能较长，建议分批处理`)
          }
        } else {
          ElMessage.warning('所选文件夹中没有找到有效的视频文件，请确保文件夹中包含MP4、AVI、MOV等格式的视频文件。注意：文件夹选择器不会递归遍历子文件夹，请选择包含视频文件的直接父文件夹。')
        }
      }
      
      input.oncancel = () => {
        console.log('用户取消了文件夹选择')
      }
      
      // 添加错误处理
      try {
        input.click()
      } catch (error) {
        console.error('文件夹选择出错:', error)
        ElMessage.error('文件夹选择功能出错，请尝试使用文件多选功能')
      }
    }

    // 智能按钮处理函数
    const handleBatchProcess = async () => {
      if (videoFiles.value.length > 5) {
        await startSmartBatchProcess()
      } else {
        await submitVideoBatch()
      }
    }

    // 获取按钮文本
    const getButtonText = () => {
      if (videoLoading.value) return '分析中'
      if (smartBatchLoading.value) return '智能处理中...'
      if (videoFiles.value.length > 5) return '智能批量处理'
      return '开始批量描述'
    }

    // 按城市分组处理视频文件
    const groupVideosByCity = (files) => {
      const cityGroups = {}
      
      files.forEach(file => {
        // 从文件名中提取城市信息
        // 假设文件名格式为：dataset/大洲/国家/城市/视频名.mp4
        const pathParts = file.name.split('/')
        let cityName = '未知城市'
        
        // 尝试从路径中提取城市名（通常是倒数第二个部分）
        if (pathParts.length >= 3) {
          cityName = pathParts[pathParts.length - 2]
        }
        
        if (!cityGroups[cityName]) {
          cityGroups[cityName] = []
        }
        cityGroups[cityName].push(file)
      })
      
      return cityGroups
    }

    // 暂停/恢复处理
    const togglePause = async () => {
      try {
        const action = isPaused.value ? 'resume' : 'pause'
        const response = await axios.post('/api/batch-control', { action })
        if (response.data.success) {
          isPaused.value = !isPaused.value
          batchStatus.value.is_paused = isPaused.value
          ElMessage.success(response.data.message)
        }
      } catch (error) {
        ElMessage.error('操作失败: ' + (error.response?.data?.error || error.message))
      }
    }

    // 状态轮询（优化：降低频率，避免过多请求）
    const startStatusPolling = () => {
      // 如果已经有轮询在运行，先停止
      if (statusPollInterval) {
        clearInterval(statusPollInterval)
        statusPollInterval = null
      }
      
      // 立即执行一次状态查询
      const pollStatus = async () => {
        // 只有在处理中时才轮询，避免无用请求
        if (!videoLoading.value && !smartBatchLoading.value) {
          stopStatusPolling()
          return
        }
        
        try {
          const response = await axios.get('/api/batch-status')
          if (response.data.success) {
            batchStatus.value = response.data.status
            isPaused.value = response.data.status.is_paused || false
            // 如果处理完成，停止轮询
            if (!response.data.status.is_processing && !videoLoading.value && !smartBatchLoading.value) {
              stopStatusPolling()
            }
          }
        } catch (error) {
          console.error('获取状态失败:', error)
          // 如果连续失败，降低轮询频率
        }
      }
      
      // 立即执行一次
      pollStatus()
      
      // 降低轮询频率：从每秒改为每2秒轮询一次，减少请求压力
      statusPollInterval = setInterval(pollStatus, 2000)
    }

    // 停止状态轮询
    const stopStatusPolling = () => {
      if (statusPollInterval) {
        clearInterval(statusPollInterval)
        statusPollInterval = null
      }
    }

    // 智能批量处理（按城市分组）
    const startSmartBatchProcess = async () => {
      if (videoFiles.value.length === 0 || !videoPrompt.value.trim()) {
        ElMessage.warning('请先选择视频并填写提示词')
        return
      }

      smartBatchLoading.value = true
      isPaused.value = false
      smartBatchProgress.value = { current: 0, total: videoFiles.value.length, currentBatch: 0, totalBatches: 0 }
      
      // 初始化结果列表，以便随时可以导出
      videoResults.value = []
      
      // 初始化状态显示
      batchStatus.value = {
        is_processing: true,
        is_paused: false,
        current_file: '',
        current_index: 0,
        total_files: videoFiles.value.length,
        current_city: '',
        total_cities: 0
      }
      
      // 开始状态轮询
      startStatusPolling()
      
      try {
        // 按城市分组
        const cityGroups = groupVideosByCity(videoFiles.value)
        const cities = Object.keys(cityGroups)
        const totalCities = cities.length
        
        ElMessage.info(`开始智能批量处理，共 ${videoFiles.value.length} 个视频，分布在 ${totalCities} 个城市`)
        
        const allResults = []
        
        // 按城市顺序处理
        for (let cityIndex = 0; cityIndex < cities.length; cityIndex++) {
          const cityName = cities[cityIndex]
          const cityFiles = cityGroups[cityName]
          
          ElMessage.info(`开始处理城市【${cityName}】的 ${cityFiles.length} 个视频`)
          
          // 收集当前城市的所有批次结果
          const cityResults = []
          
          // 每个城市内的视频分批处理（每批最多3个，减少并发压力）
          const BATCH_SIZE = 3
          const cityBatches = Math.ceil(cityFiles.length / BATCH_SIZE)
          
          for (let batchIndex = 0; batchIndex < cityBatches; batchIndex++) {
            // 检查是否暂停
            while (isPaused.value) {
              await new Promise(resolve => setTimeout(resolve, 1000))
            }
            
            const startIdx = batchIndex * BATCH_SIZE
            const endIdx = Math.min(startIdx + BATCH_SIZE, cityFiles.length)
            const batchFiles = cityFiles.slice(startIdx, endIdx)
            
            const batchNum = batchIndex + 1
            const totalBatchNum = (cityIndex * cityBatches) + batchIndex + 1
            
            smartBatchProgress.value.currentBatch = totalBatchNum
            smartBatchProgress.value.totalBatches = cities.reduce((total, city) => 
              total + Math.ceil(cityGroups[city].length / BATCH_SIZE), 0
            )
            
            ElMessage.info(`正在处理 ${cityName} 的第 ${batchNum}/${cityBatches} 批 (${batchFiles.length} 个文件)`)
            
            const formData = new FormData()
            batchFiles.forEach(v => formData.append('videos', v))
            formData.append('question', videoPrompt.value)
            // 不设置 skip_export，让后端自动为每个视频生成Excel文件

            try {
              const resp = await axios.post('/api/video-batch-query', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                timeout: 1800000 // 30分钟超时，适应大量视频处理
              })
              
              if (resp.data.success) {
                const batchResults = resp.data.results || []
                // 收集当前批次的结果
                cityResults.push(...batchResults)
                
                // 转换结果格式以兼容现有显示逻辑
                const convertedResults = batchResults.map(result => ({
                  filename: result.filename,
                  frames_used: 1, // 直接视频处理，相当于1帧
                  answers: [result.answer],
                  description: result.answer
                }))
                allResults.push(...convertedResults)
                // 实时更新videoResults，以便随时可以导出
                videoResults.value = [...allResults]
                smartBatchProgress.value.current += batchFiles.length
                
                ElMessage.success(`${cityName} 第 ${batchNum} 批处理完成，成功处理 ${batchResults.length} 个视频`)
              } else {
                ElMessage.error(`${cityName} 第 ${batchNum} 批处理失败: ${resp.data.error || '未知错误'}`)
              }
            } catch (error) {
              const errorMsg = error.response?.data?.error || error.message || '请求失败'
              ElMessage.error(`${cityName} 第 ${batchNum} 批请求失败: ${errorMsg}`)
              
              // 如果是频率限制错误，等待更长时间
              if (errorMsg.includes('频率') || errorMsg.includes('rate') || errorMsg.includes('429') || 
                  errorMsg.includes('InternalError') || errorMsg.includes('500')) {
                ElMessage.warning('检测到API限制错误，等待30秒后继续...')
                await new Promise(resolve => setTimeout(resolve, 30000))
              }
            }
            
            // 批次间休息，避免服务器过载（增加等待时间）
            if (batchIndex < cityBatches - 1 || cityIndex < cities.length - 1) {
              const waitTime = 10 // 从5秒增加到10秒
              ElMessage.info(`等待${waitTime}秒后处理下一批，避免API频率限制...`)
              await new Promise(resolve => setTimeout(resolve, waitTime * 1000))
            }
          }
          
          // 每个视频处理完成后已自动导出Excel，无需统一导出
          ElMessage.success(`城市【${cityName}】处理完成，共处理 ${cityFiles.length} 个视频，每个视频已自动生成Excel文件`)
        }
        
        // 确保最终结果已更新（虽然处理过程中已实时更新）
        videoResults.value = [...allResults]
        ElMessage.success(`智能批量处理完成！共处理 ${allResults.length} 个视频，覆盖 ${cities.length} 个城市`)
        
      } catch (e) {
        ElMessage.error('智能批量处理失败: ' + (e.response?.data?.error || e.message))
      } finally {
        smartBatchLoading.value = false
        smartBatchProgress.value = { current: 0, total: 0, currentBatch: 0, totalBatches: 0 }
        stopStatusPolling()
      }
    }

    // 导出Excel
    const exportToExcel = async () => {
      if (videoResults.value.length === 0) {
        ElMessage.warning('没有可导出的数据')
        return
      }

      exportLoading.value = true
      try {
        // 转换数据格式以匹配后端API期望的格式
        const exportData = videoResults.value.map(result => ({
          filename: result.filename || '',
          description: result.description || result.answer || (result.answers && result.answers[0]) || ''
        }))
        
        const response = await axios.post('/api/export-excel', {
          results: exportData
        }, {
          headers: { 'Content-Type': 'application/json' }
        })

        if (response.data.success) {
          const exportedFiles = response.data.exported_files || []
          const totalCities = response.data.total_cities || 0
          
          if (exportedFiles.length > 0) {
            // 现在是一个视频一个Excel文件，简化显示逻辑
            if (exportedFiles.length === 1) {
              // 单个文件，显示文件路径
              const file = exportedFiles[0]
              ElMessage.success({
                message: `${response.data.message}\n文件保存位置：${file.filepath}`,
                duration: 6000,
                showClose: true
              })
            } else {
              // 多个文件，显示前几个文件的路径（避免消息过长）
              const maxDisplay = 5
              const displayFiles = exportedFiles.slice(0, maxDisplay)
              const fileInfo = displayFiles.map(file => {
                const videoName = file.video_filename ? file.video_filename.split('/').pop() : '未知视频'
                return `${videoName}: ${file.filepath}`
              }).join('\n')
              
              let message = `${response.data.message}\n\n文件保存位置（前${Math.min(maxDisplay, exportedFiles.length)}个）：\n${fileInfo}`
              if (exportedFiles.length > maxDisplay) {
                message += `\n... 还有 ${exportedFiles.length - maxDisplay} 个文件`
              }
              
              ElMessage.success({
                message: message,
                duration: 10000,
                showClose: true
              })
            }
            console.log('导出文件信息：', exportedFiles)
          } else {
            ElMessage.success(response.data.message)
          }
        } else {
          ElMessage.error(response.data.error || '导出失败')
        }
      } catch (error) {
        ElMessage.error('导出失败: ' + (error.response?.data?.error || error.message))
      } finally {
        exportLoading.value = false
      }
    }

    onMounted(() => {
      // 组件挂载完成
    })

    return {
      imageFile,
      imagePreview,
      imageInfo,
      question,
      answers,
      loading,
      batchLoading,
      activeTab,
      detectTarget,
      detectLoading,
      detectionResult,
      imageCanvas,
      handleImageChange,
      clearImage,
      clearAnswers,
      formatFileSize,
      submitQuery,
      submitBatchQuery,
      submitDetection,
      clearDetections,
      drawImageOnCanvas,
      // 视频
      videoPrompt,
      videoFiles,
      videoLoading,
      videoResults,
      handleVideoChange,
      handleVideoRemove,
      submitVideoBatch,
      clearVideoList,
      selectFiles,
      selectFolder,
      handleBatchProcess,
      getButtonText,
      startSmartBatchProcess,
      smartBatchLoading,
      smartBatchProgress,
      exportToExcel,
      exportLoading,
      // 批量处理控制
      isPaused,
      batchStatus,
      togglePause
    }
  }
}
</script>

<style scoped>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f7fa;
  min-height: 100vh;
}

.app-container {
  min-height: 100vh;
  background: #f5f7fa;
}

/* 顶部导航栏 */
.app-header {
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border-bottom: 1px solid #e4e7ed;
  height: 70px;
  padding: 0 20px;
}

.header-content {
  height: 100%;
  display: flex;
  justify-content: flex-start;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-group h1 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
}

.subtitle {
  font-size: 13px;
  color: #909399;
}

/* 主内容区 */
.app-main {
  padding: 0;
  margin: 0;
  width: 100%;
  height: calc(100vh - 70px);
  overflow-y: auto;
}

/* 主内容行 */
.main-content-row {
  min-height: 100%;
  margin: 0;
}

/* 上传区域 */
.upload-section {
  min-height: 100%;
  padding: 16px 0 16px 16px;
}

/* 问答区域 */
.query-section {
  min-height: 100%;
  padding: 16px 16px 16px 16px;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge {
  margin-left: 8px;
}

/* 上传卡片 */
.upload-card {
  margin: 0;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
}

.upload-component {
  width: 100%;
  flex: 1;
}

.upload-placeholder {
  padding: 60px 20px;
  text-align: center;
}

.upload-icon {
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text {
  color: #606266;
}

.el-upload__text {
  font-size: 16px;
  margin-bottom: 8px;
}

.el-upload__text em {
  color: #409eff;
  font-style: normal;
}

.el-upload__tip {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.image-preview-container {
  width: 100%;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border-radius: 8px;
  overflow: hidden;
}

.image-canvas {
  max-width: 100%;
  cursor: pointer;
  display: block;
}

.upload-actions {
  text-align: center;
}

.image-info {
  margin-top: 20px;
}

/* 问答卡片 */
.query-card {
  margin: 0;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
}


/* 答案卡片 */
.answers-card {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

/* 确保卡片内容区域填充 */
:deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

/* 智能问答部分特殊样式 */
.query-card :deep(.el-card__body) {
  padding: 24px 20px 20px 20px;
}

.answer-card {
  box-shadow: none;
  border: 1px solid #ebeef5;
}

.answer-content {
  padding: 8px 0;
}

.question-text,
.answer-text {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  line-height: 1.8;
}

.question-text span,
.answer-text span {
  flex: 1;
  color: #606266;
  font-size: 15px;
}

.question-text {
  margin-bottom: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-header {
    height: auto;
    padding: 12px 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }

  .app-main {
    height: calc(100vh - auto);
  }

  .upload-section,
  .query-section {
    padding: 8px;
  }

  .title-group h1 {
    font-size: 20px;
  }
}

/* 时间线样式优化 */
:deep(.el-timeline-item__timestamp) {
  color: #909399;
  font-size: 13px;
}

/* 表单优化 */
:deep(.el-form-item__label) {
  font-weight: 600;
  color: #606266;
}

/* 上传组件优化 */
:deep(.el-upload-dragger) {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  transition: all 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}

/* 视频列表样式 */
.video-list-container {
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.video-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 4px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  min-height: 40px;
}

.video-item:last-child {
  margin-bottom: 0;
}

.video-name {
  flex: 1;
  font-weight: 500;
  color: #495057;
  word-break: break-all;
  line-height: 1.2;
  font-size: 14px;
  max-height: 2.4em;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.video-size {
  color: #6c757d;
  font-size: 13px;
}
</style>

