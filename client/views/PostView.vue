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
  let element = document.getElementById("post-item");
  console.log(json);
  element.innerHTML += json['preview_content'];
}

onMounted(() => {
  get_post(window.location.pathname.split('/')[2]);
})
</script>

<template>
  <div class="post-item" id="post-item">
    <h1>Пост</h1>
    {{$route.params.id }}
  </div>
</template>