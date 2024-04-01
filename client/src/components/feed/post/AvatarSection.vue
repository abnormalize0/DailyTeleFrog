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
      <div class="p4 justifyRight rightBlockHeader">
        <div>{{ displayClickString }} открытий</div>
        <div>{{ displayWatchString }} просмотров</div>
      </div>
      <div class="rightBlockFooter p2">
        <div class="justifyCenter">
          <i class="bookmark-text-color-icon"></i>
          <div>{{ spotlightCount }}</div>
        </div>
        <div class="justifyCenter">
          <i class="comment-text-color"></i>
          <div>{{ commentsNumber }}</div>
        </div>
        <div class="justifyCenter">
          <div>
            <i class="arrow-down-text-color"></i>
          </div>
          <div>
            {{ likesCount }}
          </div>
          <div>
            <i class="arrow-up-text-color"></i>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
  .avatar-section {
    padding-left: 1rem;
    padding-right: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .rightBlockHeader {
    width: 100%;
  }

  .leftBlock {
    display: flex;
    gap: 5px;
    align-items: center;
  }

  .justifyRight {
    display: flex;
    justify-content: right;
    gap: 2rem;
  }

  .rightBlockFooter {
    display: flex;
    gap: 3rem;
    align-items: center;
  }

  .justifyLeft {
    display: flex;
    justify-content: left;
  }

  .justifyCenter {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 5px;
  }

  img {
    height: 60px;
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