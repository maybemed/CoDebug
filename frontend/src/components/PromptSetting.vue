<template>
  <div>
    <input v-model="prompt" />
    <button @click="setPrompt">设置系统Prompt</button>
  </div>
</template>
<script>
export default {
  data() {
    return { prompt: '' }
  },
  methods: {
    async setPrompt() {
      await fetch('/api/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: this.prompt })
      });
      alert('系统Prompt已更新');
    }
  }
}
</script> 