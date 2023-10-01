<script setup>
import { onMounted, ref } from 'vue';
const tag_readed = ref(false);

let tag;
onMounted(() => {
  tag = window.location.pathname.split('/')[2];
  tag_readed.value = true;
})
</script>

<template>
  <div v-if="tag_readed">Тут должно быть отображение постов по тегу {{ tag }}, но его пока нет :(</div>
</template>