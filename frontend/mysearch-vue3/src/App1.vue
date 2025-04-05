<template>
  <div id="app">
    <div class="conversation-container"> 
      <div
        v-for="(message, index) in conversationHistory"
        :key="index"
        class="message-group"
      >
        <!-- 日志信息 -->
        <div
          v-if="message.logs && message.sender === 'server'"
          class="log-container"
        >
          <div v-if="!message.showAllLogs">
            <p>{{ message.logs.slice(-1)[0] }}</p>
            <button @click="toggleLogVisibility(index)">查看全部</button>
          </div>
          <div v-else>
            <p v-for="(log, logIndex) in message.logs" :key="logIndex">
              {{ log }}
            </p>
            <button @click="toggleLogVisibility(index)">收起</button>
          </div>
        </div>
        <!-- 系统回复或用户输入 -->
        <div
          :class="['message', message.sender]"
          v-html="message.isMarkdown ? renderMarkdown(message.text) : message.text"
        ></div>
      </div>
    </div>

    <!-- 用户输入框 -->
    <div class="input-container">
      <input
        type="text"
        v-model="currentMessage"
        :disabled="isGenerating"
        placeholder="请输入您的问题..."
        @keyup.enter="sendMessage"
      />
      <button @click="sendMessage" :disabled="isGenerating">
        发送
      </button>
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
      currentMessage: "", // 当前输入的消息
      conversationHistory: [], // 存储多轮对话
      isGenerating: false, // 标识是否在生成报告中
      isInitialRequest: true, // 是否为首次请求
      // currentReportId: null, // 当前正在生成的报告ID
    };
  },
  methods: {
    sendMessage() {
      if (!this.currentMessage.trim()) return;

      if (!this.socket || this.socket.readyState === WebSocket.CLOSED) {
        this.initializeWebSocket(() => {
          this.sendData();
        });
      } else if (this.socket.readyState === WebSocket.CONNECTING) {
        alert("WebSocket 正在连接，请稍候再试！");
      } else {
        this.sendData();
      }
    },
    sendData() {
      const userMessage = this.currentMessage.trim();

      // 禁用输入框
      this.isGenerating = true;

      // 添加用户输入到对话历史
      this.conversationHistory.push({
        sender: "user",
        text: userMessage,
        isMarkdown: false,
      });

      const data = this.isInitialRequest
        ? {
            type: "start",
            task: userMessage,
            report_type: "research_report",
            report_source: "web",
            tone: "Objective"
          }
        : {
            type: "chat",
            // message:userMessage,
            // context: userMessage
            context: this.conversationHistory
              .filter(msg => msg.text.trim() !== "") // 过滤掉 msg.text 为空的记录
              .map((msg) => ({
                role: msg.sender === "user" ? "question" : "report",
                content: msg.text,
              })),
          };

      this.socket.send(JSON.stringify(data));
      console.log("发送数据:", data);

      // 清空当前输入框
      this.currentMessage = "";
      this.isInitialRequest = false;
    },
    initializeWebSocket(onConnected) {
      const wsUri = "ws://localhost:8000/ws";
      this.socket = new WebSocket(wsUri);

      this.socket.onopen = () => {
        console.log("WebSocket 连接已建立");
        this.socketConnected = true;
        if (onConnected) onConnected();
      };

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("收到服务端消息:", data);

        if (data.type === "report") {
          // 如果当前没有创建报告框，先创建一个框
          const lastMessage = this.conversationHistory.at(-1);
          if (lastMessage && lastMessage.sender === "server" && lastMessage.logs) {
            // 如果最后一条消息是服务器的消息并且已经包含了日志信息，追加报告内容
            lastMessage.text += `\n${data.output}`;
            lastMessage.isMarkdown = true; // 确保报告内容以 Markdown 格式显示
          } else {
            // 如果最后一条消息不是服务器的消息或者不包含日志信息，创建新的报告消息
            this.conversationHistory.push({
              sender: "server",
              text: data.output,
              isMarkdown: true,
            });
          }
          // if (this.currentReportId === null) {
          //   this.currentReportId = this.conversationHistory.length;
          //   this.conversationHistory.push({
          //     sender: "server",
          //     text: data.output,
          //     isMarkdown: true,
          //   });
          // } else {
          //   // 如果已有框，追加内容到当前框
          //   this.conversationHistory[this.currentReportId].text += `\n${data.output}`;
          // }
        } else if (data.type === "path") {
          // 报告结束时清空当前报告ID，允许用户再次输入
          // this.currentReportId = null;
          this.isGenerating = false;
        } else if (data.type === "logs") {
          // 日志消息：追加或创建日志
          const lastMessage = this.conversationHistory.at(-1);
          if (lastMessage && lastMessage.sender === "server" && lastMessage.logs) {
            lastMessage.logs.push(data.output);
          } else {
            this.conversationHistory.push({
              sender: "server",
              logs: [data.output],
              isMarkdown: false,
              text: "",
              showAllLogs: false, // 日志默认不展开
            });
          }
        }
      };

      this.socket.onerror = (error) => {
        console.error("WebSocket 错误:", error);
        this.isGenerating = false;
      };

      this.socket.onclose = () => {
        console.log("WebSocket 连接已关闭");
        this.socketConnected = false;
        this.isGenerating = false;
      };
    },
    toggleLogVisibility(index) {
      const message = this.conversationHistory[index];
      if (message && message.logs) {
        message.showAllLogs = !message.showAllLogs;
      }
    },
    renderMarkdown(text) {
      return marked(text);
    },
  },
  // mounted() {
  //   this.initializeWebSocket();
  // },
};
</script>

<style>
/* 页面整体布局 */
#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f4f6f9;
}

/* 对话容器 */
.conversation-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

/* 日志容器 */
.log-container {
  max-width: 70%;
  margin-bottom: 5px;
  padding: 8px;
  border-radius: 5px;
  background-color: #f8f9fa;
  color: #6c757d;
  font-size: 12px;
}

/* 对话气泡样式 */
.message-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;
}

.message {
  max-width: 70%;
  padding: 10px 15px;
  border-radius: 10px;
  word-wrap: break-word;
}

.message.user {
  align-self: flex-end;
  background-color: #d1e7ff;
  color: #004085;
}

.message.server {
  align-self: flex-start;
  background-color: #e9ecef;
  color: #495057;
}

/* 输入框样式 */
.input-container {
  display: flex;
  padding: 10px;
  border-top: 1px solid #ddd;
  background-color: #fff;
}

.input-container input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  margin-right: 10px;
}

.input-container button {
  padding: 10px 20px;
  background-color: #007bff;
  color: #fff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.input-container button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
