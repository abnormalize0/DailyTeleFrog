<template>
  <v-app class="background-main-color">
    <HeaderComponent />
    <div class="d-flex">
      <LeftMenuComponent :groups="groups"/>
      <PostPreview :post="post"></PostPreview>
    </div>
    
  </v-app>
</template>

<style>
@import "../public/css/styles.css";
</style>

<script>
import HeaderComponent from "@/components/common/HeaderComponent.vue";
import LeftMenuComponent from "@/components/common/LeftMenuComponent.vue";

export default {
  name: "MVP",
  components: {
    HeaderComponent,
    LeftMenuComponent,
  },
  data() {
    return {
      groups: [
        {
          name: "onanisti",
          img: "https://cdn2.iconfinder.com/data/icons/people-groups/512/Leader_Avatar-512.png",
        },
        {
          name: "dungeonSlaveZ",
          img: "https://cdn2.iconfinder.com/data/icons/people-groups/512/Leader_Avatar-512.png",
        },
        {
          name: "boyNextDoor",
          img: "https://cdn2.iconfinder.com/data/icons/people-groups/512/Leader_Avatar-512.png",
        },
        {
          name: "Jhohan pohan",
          img: "https://cdn2.iconfinder.com/data/icons/people-groups/512/Leader_Avatar-512.png",
        },
        {
          name: "tester mokaka",
          img: "https://cdn2.iconfinder.com/data/icons/people-groups/512/Leader_Avatar-512.png",
        },
      ],
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
    }
  },
};
</script>
