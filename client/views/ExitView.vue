<script setup>
  import router from '../router';
  // localStorage.removeItem('id');
  localStorage.id = 0;
  router.push({ name: 'feed'});
</script>

<template>
  Подождите...
</template>
