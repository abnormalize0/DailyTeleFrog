
<script setup>
  import { onMounted, ref } from 'vue';

  let article = ref({
    article: {
      name: null,
      article: null,
    }
  });

  async function get_post(id) {
    const request = await fetch("http://127.0.0.1:5000/article", {
      method: 'GET',
      headers: {
        'article-id': id,
      },
    } )
    article.value = await request.json();
    console.log(article.value.article.article_body)
  }

  onMounted(async () => {
    get_post(window.location.pathname.split('/')[2]);
  })
</script>

<template v-if="article.article.name">
  <div class="post-item" id="post-item">
    <h1>{{ decodeURIComponent(article.article.name) }}</h1>
    <div v-for="(block, index) in article.article.article_body" v-bind:key="index"> 
      <div v-if="block.type == 0"><h1>{{ decodeURIComponent(block.content) }}</h1></div>
      <div v-if="block.type == 1">{{ decodeURIComponent(block.content) }}</div>
      <div v-if="block.type == 2" ><img width='600' :src=decodeURIComponent(block.content)></div>
      <br>
    </div>
  </div>
</template>