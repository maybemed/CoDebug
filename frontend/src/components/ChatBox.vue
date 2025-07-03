<template>
  <div class="chat-container">
    <div class="chat-history">
      <div v-for="(msg, idx) in chatHistory" :key="idx" class="chat-item">
        <div class="bubble user">
          <span class="role">你：</span>{{ msg.question }}
        </div>
        <div class="bubble ai">
          <span class="role">AI：</span>{{ msg.answer }}
          <button class="extract-btn" @click="extractTriplets(idx)" v-if="!msg.tripletsLoading && !msg.triplets.length">提取三元组</button>
          <span v-if="msg.tripletsLoading" class="loading">三元组生成中...</span>
        </div>
        <div v-if="msg.triplets && msg.triplets.length" class="triplet-card">
          <div class="triplet-title">三元组提取结果：</div>
          <ul>
            <li v-for="(t, i) in msg.triplets" :key="i">({{ t.h }}, {{ t.t }}, {{ t.r }})</li>
          </ul>
        </div>
      </div>
      <div v-if="loading" class="bubble ai loading">AI回答中...</div>
    </div>
    <div class="input-bar">
      <textarea v-model="question" @keydown.enter.exact.prevent="ask" placeholder="请输入你的问题..." rows="2"></textarea>
      <button @click="ask" :disabled="loading || !question.trim()">发送</button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      question: '',
      chatHistory: [],
      loading: false
    }
  },
  methods: {
    async ask() {
      if (!this.question.trim()) return;
      this.loading = true;
      const userQ = this.question;
      this.question = '';
      const idx = this.chatHistory.length;
      this.chatHistory.push({ question: userQ, answer: '', triplets: [], tripletsLoading: false });
      try {
        const res = await fetch('/api/qa', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: userQ })
        });
        const data = await res.json();
        console.log('后端返回：', data);
        this.$set(this.chatHistory, idx, {
          question: userQ,
          answer: data.answer,
          triplets: [],
          tripletsLoading: false
        });
      } finally {
        this.loading = false;
      }
    },
    async extractTriplets(idx) {
      this.$set(this.chatHistory[idx], 'tripletsLoading', true);
      const text = this.chatHistory[idx].answer;
      const res = await fetch('/api/kg/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      this.$set(this.chatHistory[idx], 'triplets', data.triples);
      this.$set(this.chatHistory[idx], 'tripletsLoading', false);
    }
  }
}
</script>

<style scoped>
.chat-container {
  max-width: 600px;
  margin: 40px auto;
  background: #f7f7f8;
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.07);
  display: flex;
  flex-direction: column;
  height: 80vh;
}
.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px 0 16px;
}
.chat-item {
  margin-bottom: 18px;
}
.bubble {
  display: inline-block;
  padding: 12px 18px;
  border-radius: 18px;
  margin-bottom: 4px;
  font-size: 16px;
  line-height: 1.6;
  max-width: 80%;
  word-break: break-all;
  position: relative;
}
.bubble.user {
  background: #fff;
  align-self: flex-end;
  border-bottom-right-radius: 4px;
  margin-left: 20%;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.bubble.ai {
  background: #e6f0fa;
  align-self: flex-start;
  border-bottom-left-radius: 4px;
  margin-right: 20%;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.bubble.loading {
  color: #888;
  font-style: italic;
  background: #f0f0f0;
  text-align: center;
}
.role {
  font-weight: bold;
  margin-right: 6px;
  color: #409eff;
}
.input-bar {
  display: flex;
  align-items: flex-end;
  padding: 16px;
  border-top: 1px solid #ececec;
  background: #fff;
  border-radius: 0 0 12px 12px;
}
.input-bar textarea {
  flex: 1;
  resize: none;
  border: 1px solid #dcdcdc;
  border-radius: 8px;
  padding: 10px;
  font-size: 15px;
  outline: none;
  margin-right: 12px;
  background: #fafbfc;
  transition: border 0.2s;
}
.input-bar textarea:focus {
  border: 1.5px solid #409eff;
}
.input-bar button {
  background: #409eff;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 8px 20px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
}
.input-bar button:disabled {
  background: #b3d8fd;
  cursor: not-allowed;
}
.extract-btn {
  margin-left: 12px;
  background: #fff;
  color: #409eff;
  border: 1px solid #409eff;
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.extract-btn:hover {
  background: #409eff;
  color: #fff;
}
.triplet-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  padding: 10px 16px;
  margin: 8px 0 0 0;
}
.triplet-title {
  font-weight: bold;
  color: #409eff;
  margin-bottom: 4px;
}
</style> 