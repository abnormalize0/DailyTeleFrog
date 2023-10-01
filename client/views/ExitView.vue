<script setup>
  import router from '../router';
  localStorage.removeItem('id');
  router.push({ name: 'feed'});
</script>

<template>
  Подождите...
</template>
