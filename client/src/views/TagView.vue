<script setup>
  import { onMounted, ref } from 'vue';

  let tag = ref([]);
  onMounted(() => {
    tag.value = window.location.pathname.split('/')[2];
  })
</script>

<template>
  <div>Тут должно быть отображение постов по тегу {{ tag }}, но его пока нет :(</div>
</template>