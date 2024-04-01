<template>
  <v-app class="background-main-color">
    <HeaderComponent />
    <div class="d-flex justify-center">
      <PostPreview :post="post"></PostPreview>
    </div>
  </v-app>
</template>

<style>
@import "../public/css/styles.css";
</style>

<script>
import HeaderComponent from "@/components/common/HeaderComponent.vue";

import PostPreview from "@/components/feed/post-preview/PostPreview.vue";
export default {
  name: "MVP",
  components: {
    HeaderComponent,
    PostPreview,
  },
  data: () => ({
    post: {
      watchCount: "42323",
      clickCount: "1000000",
      spotlightCount: "49",
      commentsNumber: "60",
      likesCount: "-40",
      accountTag: "@Nintendo",
      profileName: "Tsugi",
      avatarImg: "https://cdn4.iconfinder.com/data/icons/expressive-emoticons/64/down_reverse_smile_fake_smile_hate_upside_down_emoji_expression_face_emoticon_smile_happy_fun_big_smile_cheerful_cute_joy_laugh_happiness-512.png",
      img: "../../../assets/img-placeholder.png",
      hashtags: ["bebra", "booba", "chipi"],
      header: 'Ответ на пост "А вот это интересная точка зрения"',
      body: "Сама по себе религия - это хорошо. По идее, во всех священных писаниях просто начертались условия выживания. Знаете, зачем нужен вот этот сорокадневный пост? Да чтобы вы последнюю скотину перед летом не сожрали. Сожрете скотину - будет голодный год, Бог вас так карает. А знаете, почему беспорядочный секс - это грех? Да потому что не знал никто раньше про сифилис и гонорею. Вот и думали, вот эти язвы - это их Бог наказывает. Или вот дни без еды, да? По средам и пятницам. Про интервальное голодание они тоже что-то знали.",
      registrationDate: "25 августа 2023 г"
    }
  }),
};
</script>
