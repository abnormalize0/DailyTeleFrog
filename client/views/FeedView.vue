<style>
  @import '../css/PreviewStyle.css';
</style>

<template id="post_template">
  <section class="posts-list">
    <div class="list">
      <div id="feed">
        <div v-for="post in posts" :key="post.id" >
          <router-link :to="{ name: 'post', params: { id: post.article_id } }" custom v-slot="{ navigate }">
            <div class="post-item" :id="'post' + post.id">
              <div class="post-top">
                <div @click="navigate" class="post-title">{{ post.name }}</div>
                <div class="post-menu-button">...</div>
              </div>
              <div @click="navigate" v-if="posts.length != 0">
                <div class="post-content" v-for="(block, index) in post.preview_content" v-bind:key="index"> 
                  <div v-if="block.type == 0"><h1>{{ decodeURIComponent(block.content) }}</h1></div>
                  <div v-if="block.type == 1">{{ decodeURIComponent(block.content) }}</div>
                  <div v-if="block.type == 2"><img class="post-image" :src=decodeURIComponent(block.content)></div>
                </div>
              </div>
              <div class="post-tags">
                <div style="display: inline-block; margin: 0 10px 0 0;" v-for="(tag, index) in post.tags" :key="index">
                  <router-link :to="{ name: 'tag', params: { id: decodeURIComponent(post.tags[index]) } }" custom v-slot="{ navigate }">
                    <div class="post-tag" @click="navigate">{{ tag }}</div>
                  </router-link>
                </div>
              </div>
              <hr>
              <div class="post-bottom">
                <img class="post-avatar highlight" src="https://img.gruporeforma.com/imagenes/960x640/6/462/5461086.jpg">
                <img class="post-subavatar highlight" src="https://upload.wikimedia.org/wikipedia/commons/9/9f/Nintendo-switch-icon.png">
                <div class="post-author" >{{ post.author_preview.name }}</div>
                <div class="post-subsite">@Nintendo</div>
                <div class="post-time"> {{time_ago(post.created)}} <div class="post-time-tooltip">{{ tooltip_time(post.created) }}</div> </div>
                <div class="post-misc" ></div>
                <div class="post-views" >0 просмотров </div>
                <div class="post-misc" >🗪 {{ post.comments_count }}</div>
                <div class="post-misc" @click="like_change(post.id)" :id="'display_like'+post.article_id">↑</div>
                <div class="post-misc" :id="'like'+post.article_id">{{ post.likes_count - post.dislikes_count }}</div>
                <div class="post-misc" @click="dislike_change(post.id)" :id="'display_dislike'+post.article_id">↓</div>
              </div>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
  import { DateTime, Settings } from 'luxon';
  Settings.defaultLocale = 'ru';

  export default {
    data() {
      return {
        PAGE_PER_ARTICLES:5, 
        posts:[], 
        page:0, 
        post_id:1, 
        load_line_id:5, 
        allow:0
      };
    },
    methods: {
      handleScroll() {
        if(this.allow === 0) {
          return;
        }
        let element = document.getElementById('post' + this.load_line_id);
        if(element == null) {
          this.allow = 0;
          return;
        }
        let load_line_element = element.getBoundingClientRect();
        if(load_line_element.top <= (window.innerHeight || document.documentElement.clientHeight)) {
          this.load_line_id += this.PAGE_PER_ARTICLES;
          this.allow = 0;
          this.page++;
          this.get_posts(this.page);
        }
      },
      async get_posts(page) {
        const request = await fetch("http://127.0.0.1:5000/pages", {
          method: 'GET',
          headers: {
            'indexes': "~"+page+"~",
            'user-id': localStorage.id,
            'include-nonsub': true,
            'sort-column': 'creation_date',
            'sort-direction': "descending"
          }
        })
        let json = await request.json();
        console.log(json);
        for(let i = 0; i < json.pages[page].length; i++) {
          this.posts.push({
            id: i,
            name: decodeURIComponent(json.pages[page][i].name),
            created: json.pages[page][i].creation_date,
            preview_content: json.pages[page][i].preview_content,
            tags: decodeURIComponent(json.pages[page][i].tags).split("~").filter(elm => elm),
            article_id: json.pages[page][i].id,
            author_preview: json.pages[page][i].author_preview,
            likes_count: json.pages[page][i].likes_count,
            dislikes_count: json.pages[page][i].dislikes_count,
            comments_count: json.pages[page][i].comments_count,
          })
          this.load_line_id = i;  //костыль для бесконечной ленты
        }
      },
      async like_change(post_id) { //добавить обновление в реальном времени в дальнейшем
        let like_article = {}
        const request = await fetch("http://127.0.0.1:5000/article/data", {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'user-id': localStorage.id,
            'article-id': this.posts[post_id].article_id,
          },
          body: JSON.stringify({"like-article": like_article}),
        })
        let status = await request.json();
        console.log(status);
      },
      async dislike_change(post_id) { //добавить обновление в реальном времени в дальнейшем
        let dislike_article = {}
        const request = await fetch("http://127.0.0.1:5000/article/data", {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'user-id': localStorage.id,
            'article-id': this.posts[post_id].article_id,
          },
          body: JSON.stringify({"dislike-article": dislike_article}),
        })
        let status = await request.json();
        console.log(status);
      },
      time_ago(date) {
        let seconds = DateTime.now().toUnixInteger() - date / 1000;
        let current_date = DateTime.now().toObject();
        let post_date = DateTime.fromMillis(date).toObject();
        let days = DateTime.now().diff(DateTime.fromMillis(date), ["days"]).toObject();
        if (current_date.year != post_date.year) {
          return DateTime.fromMillis(date).toLocaleString({month: 'long', day: 'numeric', year: 'numeric'});
        }
        if ((days.days < 2)&&(days.days > 1)) {
          return 'вчера';
        }
        if ((current_date.day != post_date.day)||(current_date.month != post_date.month)) {
          return DateTime.fromMillis(date).toLocaleString({month: 'long', day: 'numeric'});
        }
        if (seconds <= 10) {
          return 'только что';
        }
        return DateTime.now().minus({ seconds: DateTime.now().toUnixInteger() - date / 1000 }).toRelative();
      },
      tooltip_time(date) {
        return DateTime.fromMillis(date).toLocaleString({month: 'long', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
      },
    },
    mounted() {
      this.get_posts(this.page);
      this.posts.splice(0);
      this.load_line_id = this.PAGE_PER_ARTICLES;
      this.page = 0;
      
      window.addEventListener('scroll', this.handleScroll);
    },
    updated() {
      this.allow = 1;
      // this.post_id = 1;
    },
    beforeUnmount() {
      window.removeEventListener('scroll', this.handleScroll);
    },
  };

 
  
</script>
