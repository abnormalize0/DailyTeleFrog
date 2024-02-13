<template v-if="title">
  <div class="post-item" id="post-item">
    <h1>{{ decodeURIComponent(title) }}</h1>
    <div v-for="(block, index) in body" v-bind:key="index"> 
      <div v-if="block.type == 0"><h1>{{ decodeURIComponent(block.content) }}</h1></div>
      <div v-if="block.type == 1">{{ decodeURIComponent(block.content) }}</div>
      <div v-if="block.type == 2" ><img width='600' :src=decodeURIComponent(block.content)></div>
      <br>
    </div>
  </div>
  <br>
</template>

<script>
  export default {
    data() {
      return {
        article: {},
        title: {},
        body: []
      } 
    },
    methods: {
      async get_post(id) {
        const request = await fetch("http://127.0.0.1:5000/article", {
          method: 'GET',
          headers: {
            'article-id': id,
          },
        } )
        this.article.value = await request.json();
        this.title = this.article.value.article.name;
        for (let i = 0; i < this.article.value.article.article_body.length; i++) {
          this.body.push(this.article.value.article.article_body[i]);
        }
      }
    },
    async mounted() {
      await this.get_post(window.location.pathname.split('/')[2]);
    }
  }
</script>