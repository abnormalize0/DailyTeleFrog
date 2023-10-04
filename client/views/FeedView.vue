<script setup>
  import { ref, onMounted, onUpdated } from 'vue';

  let PAGE_PER_ARTICLES = 5;

  let page = 0;
  let post_id = 1;
  let load_line_id = PAGE_PER_ARTICLES;
  let allow = 0;

  onMounted(() => {
    get_posts(page);
    posts.value.splice(0);
    load_line_id = PAGE_PER_ARTICLES;
    page = 0;
  })

  onUpdated(() => {
    allow = 1;
    post_id = 1;
  })

  document.addEventListener("scroll", () => {
    if(allow === 0) {
      return;
    }
    let element = document.getElementById('post' + load_line_id);
    if(element == null) {
      allow = 0;
      return;
    }
    let load_line_element = element.getBoundingClientRect();
    if(load_line_element.top <= (window.innerHeight || document.documentElement.clientHeight)) {
      load_line_id += PAGE_PER_ARTICLES;
      allow = 0;
      page++;
      get_posts(page);
    }
  })

  async function like_change(post_id) { //заглушка пока не будет рабочего апи от сервера
    const request = await fetch("http://127.0.0.1:5000/article/like", {
      method: 'POST',
      headers: {
        'user-id': localStorage.id,
        'article-id': post_id,
      },
    })
    let status = await request.json();
    console.log(status);
    let like = document.getElementById("like" + post_id);
    if(((like.innerHTML).split(" ")[1]) == 1) {
      like.innerHTML = "♥ 2";
    } else {
      like.innerHTML = "♡ 1";
    }
  }
</script>

<template id="post_template">
  <section class="posts-list">
    <div class="list">
      <div id="feed">
        <div v-for="post in posts" :key="post.id" >
          <router-link :to="{ name: 'post', params: { id: post.article_id } }" custom v-slot="{ navigate }">
            <div :class="`post-item`" :id="'post' + post_id++">
              <div @click="navigate">
                <br>
                <h1>{{ post.name }}</h1>
                <div v-for="(block, index) in post.preview_content" v-bind:key="index"> 
                  <div v-if="block.type == 0"><h1>{{ decodeURIComponent(block.content) }}</h1></div>
                  <div v-if="block.type == 1">{{ decodeURIComponent(block.content) }}</div>
                  <!-- <div v-if="block.type == 2" ><img :id="`img` + block" width='600' :src="content[block]"></div> -->
                  
                </div>
                <br><br>
                <i style="top: 0px; left:0px; position: absolute;">Запостил пользователь {{ post.author_preview.name }} {{ post.created }} </i>
              </div>

              <div style="position: absolute; bottom: 0px; left:10px;">
                <div style="display: inline-block; margin: 10px 5px;" v-for="(tag, index) in post.tags" :key="index">
                  <router-link :to="{ name: 'tag', params: { id: decodeURIComponent(post.tags[index]) } }" custom v-slot="{ navigate }">
                    <div @click="navigate" >{{ tag }}</div>
                  </router-link>
                </div>
              </div>
              <div style="right: 10px; bottom: 0px; position: absolute;">
                <div style="display: inline-block; margin: 10px 5px;">🗪 {{ post.comments_count }}</div>
                <div @click="like_change(post.article_id)" :id="'like'+post.article_id" style="display: inline-block; margin: 10px 5px;">♡ {{ post.likes_count }}</div>
              </div>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
  let posts = ref([]);
  async function get_posts(page) {
    const request = await fetch("http://127.0.0.1:5000/pages", {
      method: 'GET',
      headers: {
        'indexes': "~"+page+"~",
        'user-id': localStorage.id,
      }
    })
    let json = await request.json();
    console.log(json);
    for(let i = 0; i < json.pages[page].length; i++) {
      posts.value.push({
        id: i,
        name: decodeURIComponent(json.pages[page][i].name),
        created: json.pages[page][i].created,
        preview_content: json.pages[page][i].preview_content,
        tags: decodeURIComponent(json.pages[page][i].tags).split("~").filter(elm => elm),
        article_id: json.pages[page][i].id,
        author_preview: json.pages[page][i].author_preview,
        likes_count: json.pages[page][i].likes_count,
        comments_count: json.pages[page][i].comments_count,
      })
    }
  }
</script>
