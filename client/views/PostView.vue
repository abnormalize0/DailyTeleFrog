<script setup>
import { onMounted } from 'vue'

async function get_post(id) {
  const response = await fetch("http://127.0.0.1:5000/article", {
    method: 'GET',
    headers: {
      'article-id': id
    }
  } )
  let json = await response.json();
  console.log(json)
}

onMounted(() => {
  get_post(window.location.pathname.split('/')[2]);
})
</script>

<template>
  <div class="about">
    <h1>Пост</h1>
    {{$route.params.id }}
  </div>
</template>