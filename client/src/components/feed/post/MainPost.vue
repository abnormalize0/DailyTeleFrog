<template>
  <section class="post-item primary-rounded background-secondary-color" style="color: white">
    <div class="d-flex justify-space-between header-container">
      <p class="h2 text-color">{{ header }}</p>
      <i class="menu-kebab-text-color-icon"></i>
    </div>
    <div class="d-flex text-container">
      <p class="p3 text-color">{{ body }}</p>
    </div>
    <div class="d-flex justify-center">
      <img :src="img" />
    </div>
    <div class="hashtag-footer d-flex">
      <div v-for="hashtag in hashtags" :key="hashtag">
        <post-hashtag :content="hashtag"></post-hashtag>
      </div>
    </div>
    <avatar-section
      :accountTag="accountTag"
      :profileName="profileName"
      :avatarImg="avatarImg"
      :commentsNumber="commentsNumber"
      :likesCount="likesCount"
      :clickCount="clickCount"
      :watchCount="watchCount"
      :registrationDate="registrationDate"
      :spotlightCount="spotlightCount"
    ></avatar-section>
  </section>
</template>

<style scoped>
  .post-item {
    width: 558px;
    height: auto;
  }

  .header-container {
    padding: 20px 26px 10px 26px;
    justify-content: left;
  }  

  .text-container {
    padding: 0px 26px 10px;
  }

  .hashtag-footer {
    padding: 10px 26px;
    gap: 10px;
  }  
</style>

<script>
import PostHashtag from "@/components/feed/post/PostHashtag.vue";
import AvatarSection from "@/components/feed/post/AvatarSection.vue";

export default {
  name: "MainPost",
  components: {
    PostHashtag,
    AvatarSection
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
    spotlightCount: Number,
    registrationDate: String
  },
};
</script>
