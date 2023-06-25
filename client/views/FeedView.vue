<script setup>
import { ref, onMounted, onUpdated } from 'vue'


var page = 0;
var post_id = 1;
var load_line_id = 0;
var load_line_element = 0;
var allow = 0;

onMounted(() => {
  get_posts(page);
  posts.value.splice(0);
})

onUpdated(() => {
  console.log("rendered");
  load_line_id = load_line_id + 5;
  allow = 1;
  post_id = 1;
})

document.addEventListener("scroll", (event) => {
  if (allow === 0) {
    return;
  }
  var element = document.getElementById('post' + load_line_id);
  if (element == null) {
    document.getElementById("feed").innerHTML += "<div class='post-item'>Отличная работа, все прочитано!</div>";
    allow = 0;
    return;
  }
  load_line_element = element.getBoundingClientRect();
  if (load_line_element.bottom <= (window.innerHeight || document.documentElement.clientHeight)) {
    allow = 0;
    page++;
    get_posts(page);
  } 

})
</script>

<template id="post_template">
  <section class="posts-list">
    <div class="list">
      <div id="feed">
        <div v-for="post in posts" :key="post.id" :class="`post-item`" :id="'post' + post_id++">
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
async function get_posts(page) {
  const response = await fetch("http://127.0.0.1:5000/pages", {
    method: 'GET',
    headers: {
      'indexes': page,
      'user-id': 1
    }
  } )
  let json = await response.json();
  for (var i = 0; i < json[page].length; i++) {
    posts.value.push({
      id: i,
      title: decodeURIComponent(json[page][i]["name"]),
      date: json[page][i]["date"],
      preview: decodeURIComponent(json[page][i]["preview_content"]),
      tags: decodeURIComponent(json[page][i]["tags"])
    })
  }
}
</script>
