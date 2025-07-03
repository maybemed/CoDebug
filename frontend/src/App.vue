<template>
  <div id="app">
    <ChatBox />
    <KnowledgeGraph />
    <PromptSetting />
  </div>
</template>

<script>
import ChatBox from './components/ChatBox.vue'
import KnowledgeGraph from './components/KnowledgeGraph.vue'
import PromptSetting from './components/PromptSetting.vue'

export default {
  components: {
    ChatBox,
    KnowledgeGraph,
    PromptSetting
  }
}
</script> 