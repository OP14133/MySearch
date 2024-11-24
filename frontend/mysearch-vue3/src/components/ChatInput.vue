<template>
  <div class="chat-input-container">
    <el-input
      v-model="inputValue"
      placeholder="Type your message..."
      :clearable="true"
      class="chat-input"
      @keyup.enter="sendMessage"
    >
      <template #append>
        <el-button icon="el-icon-s-promotion" circle @click="sendMessage"></el-button>
      </template>
    </el-input>
  </div>
</template>

<script>
export default {
  name: "ChatInput",
  data() {
    return {
      inputValue: ""
    };
  },
  methods: {
    sendMessage() {
      if (this.inputValue.trim()) {
        console.log("Message sent:", this.inputValue); // 输出消息到控制台
        this.inputValue = ""; // 清空输入框
      }
    }
  }
};
</script>

<style scoped>
.chat-input-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px;
  background-color: #fff;
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
  border-top: 1px solid #e0e0e0;
}

.chat-input {
  width: 100%;
  max-width: 600px;
  border-radius: 20px;
  overflow: hidden;
}
</style>
