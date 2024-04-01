<template>
  <section class="avatar-section">
    <div class="left-block">
      <img :src="avatarImg" />
      <div>
        <div class="d-flex justify-start p1 text-color">
          {{ profileName }}
        </div>
        <div class="d-flex justify-start additional-info">
          <div class="p4 text-secondary-color">{{ accountTag }}</div>
          <div class="p4 text-secondary-color">{{ registrationDate }}</div>
        </div>
      </div>
    </div>
    <div class="justify-space-between">
      <div class="d-flex justify-end additional-info rightBlockHeader">
        <div class="p4 text-color">{{ displayClickString }} открытий</div>
        <div class="p4 text-color">{{ displayWatchString }} просмотров</div>
      </div>
      <div class="d-flex justify-end additional-info">
        <div class="d-flex align-center icon-prepend-button">
          <i class="bookmark-text-color-icon"></i>
          <div class="p3 text-color">{{ spotlightCount }}</div>
        </div>
        <div class="d-flex align-center icon-prepend-button">
          <i class="comment-text-color-icon"></i>
          <div class="p3 text-color">{{ commentsNumber }}</div>
        </div>
        <div class="d-flex align-center rating">
          <i class="arrow-down-text-color-icon"></i>
          <div class="p3 text-color">
            {{ likesCount }}
          </div>
          <i class="arrow-up-text-color-icon"></i>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
  .avatar-section {
    padding: 0px 26px 15px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .left-block {
    display: flex;
    gap: 15px;
    align-items: center;
  }

  .additional-info {
    gap: 10px;
  }

  .icon-prepend-button {
    padding: 2px 12px;
    gap: 8px;
  }

  .rating {
    padding: 2px 6px;
    gap: 5px;
  }

  img {
    height: 45px;
    width: 45px;
  }
</style>

<script>
export default {
  name: "avatar-section",
  components: {},
  props: {
    avatarImg: String,
    profileName: String,
    accountTag: String,
    registrationDate: String,
    commentsNumber: Number,
    likesCount: Number,
    clickCount: Number,
    watchCount: Number,
    spotlightCount: Number,
  },
  data() {
    return {
      displayClickString: "",
      displayWatchString: "",
    };
  },
  computed: {},
  mounted() {
    if (this.clickCount) {
      this.displayClickString = this.getDisplayString(this.clickCount);
      this.displayWatchString = this.getDisplayString(this.watchCount);
    }
  },
  methods: {
    getDisplayString(num) {
      if (num >= 1000000) {
        let numString = num.toString();
        return numString.substring(0, numString.length - 6) + "M";
      } else if (num >= 1000) {
        let numString = num.toString();
        return numString.substring(0, numString.length - 3) + "K";
      } else {
        return num.toString();
      }
    },
  },
};
</script>