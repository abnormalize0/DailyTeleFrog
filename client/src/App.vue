<template>
  <v-app class="background-main-color">
    <HeaderComponent/>
    <MainPost accountTag="@Nintendo" profileName="Tsugi" :avatarImg="avatarImg" :img="placeholder" :hashtags="hashtags" header="Lorem ipsum" body="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."></MainPost>
  </v-app>
</template>

<style>
  @import '../public/css/styles.css';
</style>

<script>
  import HeaderComponent from "@/components/common/HeaderComponent.vue";
  
  import MainPost from "@/components/feed/post/MainPost.vue";
  export default {
    name: "MVP",
    components: {
      HeaderComponent,
      MainPost
    },
    data: () => ({
      hashtags: ["bebra", "booba", "chipi"],
      avatarImg: "https://cdn4.iconfinder.com/data/icons/expressive-emoticons/64/down_reverse_smile_fake_smile_hate_upside_down_emoji_expression_face_emoticon_smile_happy_fun_big_smile_cheerful_cute_joy_laugh_happiness-512.png",
      placeholder: "https://media.istockphoto.com/id/1147544807/vector/thumbnail-image-vector-graphic.jpg?s=612x612&w=0&k=20&c=rnCKVbdxqkjlcs3xH87-9gocETqpspHFXu5dIGB4wuM="
    })
    
  }
</script>