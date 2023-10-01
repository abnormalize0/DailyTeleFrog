<script setup>
  import { onMounted, ref } from 'vue';
  const post_loaded = ref(false);

  let json;

  async function get_post(id) {
    const request = await fetch("http://127.0.0.1:5000/article", {
      method: 'GET',
      headers: {
        'article-id': id,
      },
    } )
    json = await request.json();
    console.log(json);
    post_loaded.value = true;
  }

  onMounted(() => {
    get_post(window.location.pathname.split('/')[2]);
  })
</script>

<template>
  <div class="post-item" id="post-item" v-if="post_loaded">
    <h1>{{ json.article.name }}</h1>
    <div v-for="(block, index) in json.article.article" v-bind:key="index"> 
      <div v-if="block.type == 0"><h1>{{ block.content}}</h1></div>
      <div v-if="block.type == 1">{{ block.content}}</div>
      <!-- <div v-if="block.type == 2" ><img :id="`img` + block" width='600' :src="content[block]"></div> -->
      <br>
    </div>
  </div>
</template>
