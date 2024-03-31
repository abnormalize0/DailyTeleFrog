<template>
  <section class="post-item" style="color: white">
    <div class="header-container">
      <div>
        <h2 class="h2">{{ header }}</h2>
      </div>
    </div>
    <div class="text-container">
      <div>
        <p class="post-content p3">{{ body }}</p>
      </div>
    </div>
    <div class="d-flex justify-center">
      <img :src="img" />
    </div>
    <post-footer
      :profileTag="accountTag"
      :profileName="profileName"
      :avatarImgSrc="avatarImg"
      :hashtags="hashtags"
      :commentsNumber="commentsNumber"
      :likesCount="likesCount"
      :clickCount="clickCount"
      :watchCount="watchCount"
      :spotlightCount="spotlightCount"
    ></post-footer>
  </section>
</template>
<style scoped>
.post-item {
  width: 37rem;
  height: 31rem;
  border-radius: 2rem;
}

.text-container {
  display: flex;
  padding: 1rem;
  height: 30%;
  padding-top: 0;
  justify-content: left;
  text-align: left;
}

p {
  padding: 0;
  font-size: smaller;
}

.header-container {
  padding: 1rem;
  display: flex;
  justify-content: left;
}

img {
  height: 10rem;
}
</style>
<script>
import PostFooter from "./PostFooter.vue";
export default {
  name: "MainPost",
  components: {
    PostFooter,
  },
  props: {
    header: String,
    body: String,
    img: String,
    hashtags: Array,
    avatarImg: String,
    profileName: String,
    accountTag: String,
    commentsNumber: Number,
    likesCount: Number,
    clickCount: Number,
    watchCount: Number,
    spotlightCount: Number
  },
  data() {
    return {};
  },
  computed: {},
  mounted() {},
  methods: {},
};
</script>
