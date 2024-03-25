<template>
  <section class="avatar-section">
    <div class="leftBlock">
      <img :src="avatarImg" />
      <div>
        <div class="justifyLeft p1">
          {{ profileName }}
        </div>
        <div class="justifyLeft p4">
          <p>{{ accountTag }}</p>
        </div>
      </div>
    </div>
    <div>
      <div>asdasd</div>
    </div>
  </section>
</template>
<script>
export default {
  name: "avatar-section",
  components: {},
  props: {
    avatarImg: String,
    profileName: String,
    accountTag: String,
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
.avatar-section {
  padding-left: 1rem;
  padding-right: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.leftBlock {
  display: flex;
  gap: 5px;
  align-items: center;
}

.justifyLeft {
  display: flex;
  justify-content: left;
}

img {
  height: 60px;
}
</style>
