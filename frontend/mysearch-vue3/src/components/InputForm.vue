<template>
  <div class="input-form">
    <h2>输入任务</h2>
    <div class="input-container">
      <el-input v-model="input" placeholder="请输入任务" />
      <el-button type="primary" @click="sendTask">
        <el-icon class="el-icon-arrow-right"></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      input: '',
      socket: null,
    };
  },
  mounted() {
    this.initWebSocket();
  },
  methods: {
    initWebSocket() {
      const ws_uri = "ws://localhost:8000/ws";
      this.socket = new WebSocket(ws_uri);

      this.socket.onopen = (event) => {
        console.log("WebSocket connection opened",event);
      };

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("Received message:", data);
        // 处理接收到的消息
      };

      this.socket.onclose = (event) => {
        console.log("WebSocket connection closed",event);
      };
    },
    sendTask() {
      if (this.input.trim() === '') {
        alert('请输入任务');
        return;
      }

      const requestData = {
        task: this.input,
        report_type: "research_report",
        report_source: "web",
        tone: "Objective",
        agent: "",
      };

      this.socket.send(`start ${JSON.stringify(requestData)}`);
    },
  },
};
</script>

<style scoped>
.input-form {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background-color: #f8f9fa;
  padding: 20px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.input-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.el-input {
  width: 300px;
  margin-right: 10px;
}

.el-button {
  padding: 10px 20px;
}
</style>