<template>
  <section>
    <div class="post-footer">
      <div v-for="hashtag in hashtags" class="hashtag" :key="hashtag">
        <post-hashtag :content="hashtag"></post-hashtag>
      </div>
    </div>
    <div>
      <avatar-section
        :accountTag="profileTag"
        :profileName="profileName"
        :avatarImg="avatarImgSrc"
      ></avatar-section>
    </div>
  </section>
</template>
<script>
import PostHashtag from "./PostHashtag.vue";
import AvatarSection from "./AvatarSection.vue";
export default {
  name: "post-footer",
  components: {
    PostHashtag,
    AvatarSection,
  },
  props: {
    hashtags: Array,
    avatarImgSrc: String,
    profileName: String,
    profileTag: String,
  },
  data() {
    return {};
  },
  computed: {},
  mounted() {},
  methods: {},
};
</script>
<style scoped>
.post-footer {
  padding: 1rem;
  padding-bottom: 0.5rem;
  display: flex;
  justify-content: left;
  align-items: center;
  gap: 10px;
}

.hashtag {
}
</style>
