<template>
  <v-app class="background-main-color">
    <HeaderComponent />
    <div class="d-flex justify-center">
      <MainPost
      watchCount="42323"
      clickCount="1000000"
      spotlightCount="49"
      commentsNumber="60"
      likesCount="-40"
      accountTag="@Nintendo"
      profileName="Tsugi"
      :avatarImg="avatarImg"
      :img="require(`./assets/img-placeholder.png`)"
      :hashtags="hashtags"
      header='Ответ на пост "А вот это интересная точка зрения"'
      body="Сама по себе религия - это хорошо. По идее, во всех священных писаниях просто начертались условия выживания. Знаете, зачем нужен вот этот сорокадневный пост? Да чтобы вы последнюю скотину перед летом не сожрали. Сожрете скотину - будет голодный год, Бог вас так карает.
      А знаете, почему беспорядочный секс - это грех? Да потому что не знал никто раньше про сифилис и гонорею. Вот и думали, вот эти язвы - это их Бог наказывает.
      Или вот дни без еды, да? По средам и пятницам. Про интервальное голодание они тоже что-то знали."
      registrationDate="25 августа 2023 г"
    ></MainPost>
    </div>
  </v-app>
</template>

<style>
@import "../public/css/styles.css";
</style>

<script>
import HeaderComponent from "@/components/common/HeaderComponent.vue";

import MainPost from "@/components/feed/post/MainPost.vue";
export default {
  name: "MVP",
  components: {
    HeaderComponent,
    MainPost,
  },
  data: () => ({
    hashtags: ["bebra", "booba", "chipi"],
    avatarImg:
      "https://cdn4.iconfinder.com/data/icons/expressive-emoticons/64/down_reverse_smile_fake_smile_hate_upside_down_emoji_expression_face_emoticon_smile_happy_fun_big_smile_cheerful_cute_joy_laugh_happiness-512.png",
    placeholder:
      "https://media.istockphoto.com/id/1147544807/vector/thumbnail-image-vector-graphic.jpg?s=612x612&w=0&k=20&c=rnCKVbdxqkjlcs3xH87-9gocETqpspHFXu5dIGB4wuM=",
  }),
};
</script>
