<template>
  <section class="post-item primary-rounded background-secondary-color" style="color: white">
    <div class="d-flex justify-space-between header-container">
      <p class="h2 text-color">{{ post.header }}</p>
      <div>
        <i class="menu-kebab-text-color-icon"></i>
      </div>
    </div>
    <div class="d-flex text-container">
      <p class="p3 text-color">{{ post.body }}</p>
    </div>
    <div class="d-flex justify-center">
      <img src="../../../assets/img-placeholder.png" />
    </div>
    <div class="hashtag-footer d-flex">
      <div v-for="hashtag in post.hashtags" :key="hashtag">
        <HashTagPostPreview :content="hashtag"></HashTagPostPreview>
      </div>
    </div>
    <AvatarSectionPostPreview
      :accountTag="post.accountTag"
      :profileName="post.profileName"
      :avatarImg="post.avatarImg"
      :commentsNumber="post.commentsNumber"
      :likesCount="post.likesCount"
      :clickCount="post.clickCount"
      :watchCount="post.watchCount"
      :registrationDate="post.registrationDate"
      :spotlightCount="post.spotlightCount"
    ></AvatarSectionPostPreview>
  </section>
</template>

<style scoped>
  .post-item {
    width: 558px;
    height: auto;
  }

  .header-container {
    padding: 15px 26px 10px 26px;
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
import HashTagPostPreview from "@/components/feed/post-preview/HashTagPostPreview.vue";
import AvatarSectionPostPreview from "@/components/feed/post-preview/AvatarSectionPostPreview.vue";

export default {
  name: "MainPost",
  components: {
    HashTagPostPreview,
    AvatarSectionPostPreview
  },
  props: {
    post: {
      header: String,
      body: String,
      img: String,
      hashtags: [],
      avatarImg: String,
      profileName: String,
      accountTag: String,
      commentsNumber: Number,
      likesCount: Number,
      clickCount: Number,
      watchCount: Number,
      spotlightCount: Number,
      registrationDate: String
    }
  },
};
</script>
