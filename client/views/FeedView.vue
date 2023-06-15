<script setup>
import { ref, onMounted } from 'vue'

onMounted(() => {
  get_posts()
})
</script>

<template id="post_template">
  <section class="posts-list">
    <div class="list">
      <div>
        <div v-for="post in posts" :key="post.id" :class="`post-item`">
          <h1>{{ post.title }}</h1>
          <h2>{{ post.preview }}</h2>
          <i>{{ post.tags }}</i><br>
          <i>{{ post.date }}</i>
          <br><br>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
var posts = ref([]);
async function get_posts() {
  posts.value.splice(0);
  const response = await fetch("http://127.0.0.1:5000/pages", {
    method: 'GET',
    headers: {
      'indexes': 0,
      'user_id': 1
    }
  } )
  let json = await response.json();
  console.log(json[0]);  
  for (var i = 0; i < json[0].length; i++) {
    posts.value.push({
      id: i,
      title: decodeURIComponent(json[0][i]["name"]),
      date: json[0][i]["date"],
      preview: decodeURIComponent(json[0][i]["preview_content"]),
      tags: decodeURIComponent(json[0][i]["tags"])
    })
  }
}
</script>
