
<template>
  <div id="app">
    <div class="content">
      <h2>舆情信息检索系统</h2>

      <!-- 表单 -->
      <form class="form-container">
        <div class="form-item">
          <label for="task">检索一下：</label>
          <input type="text" id="task" name="task" v-model="form.task" placeholder="请输入任务描述" />
        </div>

        <div class="form-item">
          <label for="report_type">报告类型：</label>
          <select id="report_type" name="report_type" v-model="form.report_type">
            <option value="research_report">摘要 - 简短快速（~2 分钟）</option>
            <option value="resource_report">资源报告</option>
<!--            <option value="summary_report">摘要报告</option>-->
<!--            <option value="outline_report">大纲报告</option>-->
            <option value="detailed_report">详细 - 深入且较长（~5 分钟）</option>
<!--            <option value="subtopic_report">子主题报告</option>-->
          </select>
        </div>

        <div class="form-item">
          <label for="report_source">数据来源：</label>
          <select id="report_source" name="report_source" v-model="form.report_source">
            <option value="web">网络</option>
            <option value="local">我的文档</option>
            <option value="hybrid">混合</option>
          </select>
        </div>

        <div class="form-item">
          <label for="tone">语气：</label>
          <select id="tone" name="tone" v-model="form.tone">
            <option value="Objective">客观</option>
            <option value="Formal">正式</option>
          </select>
        </div>

        <button type="button" @click="sendData" :disabled="!socketConnected">发送请求</button>
      </form>
    </div>

    <div class="response-container">
      <!-- 日志区域 -->
      <h3>日志：</h3>
      <div v-if="logs.length">
        <p class="log-item">当前任务：{{ latestLog }}</p>
        <button @click="toggleLogs" class="toggle-button">
          {{ showAllLogs ? "隐藏全部日志" : "查看全部日志" }}
        </button>
        <div v-if="showAllLogs" class="all-logs">
          <p v-for="(log, index) in logs" :key="index">{{ log }}</p>
        </div>
      </div>

      <!-- 报告区域 -->
      <h3>生成报告：</h3>
      <div v-if="reportContent" class="report-container" v-html="renderedReport"></div>
    </div>
  </div>
</template>

<script>
import { marked } from "marked";

export default {
  data() {
    return {
      socket: null, // WebSocket 实例
      socketConnected: false, // WebSocket 状态
      form: {
        task: "",
        report_type: "research_report",
        report_source: "web",
        tone: "Objective",
        agent: "",
        source_urls: [],
      },
      logs: [], // 服务端日志数据
      showAllLogs: false, // 是否展示所有日志
      reportContent: "", // 报告内容 (Markdown)
    };
  },
  computed: {
    latestLog() {
      return this.logs[this.logs.length - 1] || "暂无日志";
    },
    renderedReport() {
      return marked(this.reportContent);
    },
  },
  methods: {
    initializeWebSocket() {
      const wsUri = "ws://localhost:8000/ws";
      this.socket = new WebSocket(wsUri);

      this.socket.onopen = () => {
        console.log("WebSocket 连接已建立");
        this.socketConnected = true;
      };

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("收到服务端消息:", data);

        if (data.type === "logs") {
          // 添加日志信息
          this.logs.push(data.output);
        } else if (data.type === "report") {
          // 追加报告内容
          this.reportContent += data.output;
        }
      };

      this.socket.onerror = (error) => {
        console.error("WebSocket 错误:", error);
      };

      this.socket.onclose = () => {
        console.log("WebSocket 连接已关闭");
        this.socketConnected = false;
      };
    },
    toggleLogs() {
      this.showAllLogs = !this.showAllLogs;
    },
    sendData() {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        alert("WebSocket 未连接！");
        return;
      }

      const data = {
        ...this.form,
        source_urls:
          this.form.report_source !== "sources" && this.form.source_urls.length
            ? this.form.source_urls.slice(0, -1)
            : this.form.source_urls,
      };

      this.socket.send(`start ${JSON.stringify(data)}`);
      console.log("发送请求数据:", data);

      // 清空历史日志和报告
      this.logs = [];
      this.reportContent = "";
      this.showAllLogs = false;
    },
  },
  mounted() {
    this.initializeWebSocket();
  },
};
</script>

<style>
/* 页面整体布局 */
#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* 主内容区 */
.content {
  padding: 20px;
  background-color: #f5f5f5;
}

/* 响应容器 */
.response-container {
  padding: 20px;
  background-color: #fff;
  border-top: 1px solid #ddd;
  overflow-y: auto;
  height: 50vh;
}

/* 日志样式 */
.log-item {
  margin-bottom: 10px;
  padding: 10px;
  background-color: #e9f7df;
  border-left: 4px solid #2ecc71;
}

.all-logs {
  margin-top: 10px;
  padding: 10px;
  background-color: #f0f0f0;
  border: 1px solid #ccc;
}

.toggle-button {
  margin-top: 10px;
  padding: 5px 10px;
  background-color: #007bff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.toggle-button:hover {
  background-color: #0056b3;
}

/* 报告样式 */
.report-container {
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 10px;
  background-color: #f5f5f5;
  border-left: 4px solid #3498db;
}
</style>
