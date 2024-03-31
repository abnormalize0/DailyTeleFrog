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
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M10.6667 2H5.33333C4.59695 2 4 2.59695 4 3.33333V14L8 12L12 14V3.33333C12 2.59695 11.403 2 10.6667 2Z"
              stroke="#292929"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <div>{{ spotlightCount }}</div>
        </div>
        <div class="justifyCenter">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M8 14C11.3137 14 14 11.3137 14 7.99997C14 4.68626 11.3137 1.99997 8 1.99997C4.68629 1.99997 2 4.68626 2 7.99997C2 8.99172 2.24062 9.92728 2.66667 10.7514L2 14L5.24853 13.3333C6.07269 13.7593 7.00825 14 8 14Z"
              stroke="#292929"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <div>{{ commentsNumber }}</div>
        </div>
        <div class="justifyCenter">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M4.66666 6.66667L7.99999 10"
              stroke="#DDE5F7"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <path
              d="M8 10L11.3333 6.66667"
              stroke="#DDE5F7"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <div>
            {{ likesCount }}
          </div>
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M11.3333 9.33333L8.00001 6"
              stroke="#DDE5F7"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <path
              d="M8 6L4.66667 9.33333"
              stroke="#DDE5F7"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
      </div>
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
