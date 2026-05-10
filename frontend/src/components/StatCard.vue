<template>
  <el-card :class="['block-card', cardClass]">
    <div style="font-size:14px;opacity:.9;">{{ title }}</div>
    <div class="value-big">{{ value }}</div>
    <div class="value-small">{{ desc }}</div>
  </el-card>
</template>

<script setup>
defineProps({
  title: String,
  value: [String, Number],
  desc: String,
  cardClass: String
})
</script>