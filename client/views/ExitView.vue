<script setup>
  import router from '../router';
  // localStorage.removeItem('id');
  localStorage.id = -1;
  router.push({ name: 'feed'});
</script>

<template>
  Подождите...
</template>
