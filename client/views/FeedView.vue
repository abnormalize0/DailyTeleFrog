<style>
  @import '../css/PreviewStyle.css';
</style>

<template id="post_template">
  <section class="posts-list">
    <div class="list">
      <div id="feed">
        <div v-for="post in posts" :key="post.article_id" >
          <PostPreview :post="post" />
        </div>
      </div>
    </div>
  </section>
</template>

<script>
  import PostPreview from '../components/feed/PostPreview.vue';

  export default {
    data() {
      return {
        PAGE_PER_ARTICLES:5, 
        posts: [], 
        page:0, 
        post_id:1, 
        load_line_id:5, 
        allow:0
      };
    },
    methods: {
      async handleScroll() {
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
          console.log("id is " + this.load_line_id)
          this.load_line_id += this.PAGE_PER_ARTICLES;
          this.allow = 0;
          this.page++;
          await this.get_posts(this.page);
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
          this.load_line_id = json.pages[page][i].id;  //костыль для бесконечной ленты
        }
      }
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
    components: {
      PostPreview
    }
  };
  
</script>
