<template>
  <div id="kg"></div>
</template>
<script>
import * as d3 from 'd3';
export default {
  mounted() {
    fetch('/api/kg')
      .then(res => res.json())
      .then(data => {
        // 用d3渲染知识图谱
        // 这里只是结构示例
      });
  }
}
</script> 