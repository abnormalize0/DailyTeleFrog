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

import PostPreview from "./components/feed/post-preview/PostPreview.vue";

export default {
  name: "MVP",
  components: {
    HeaderComponent,
    PostPreview,
},
  data() {
    return {
      post: {
        header: 'Ответ на пост «А вот это интересная точка зрениz',
        body: "Сама по себе религия - это хорошо. По идее, во всех священных писаниях просто начертались условия выживания. Знаете, зачем нужен вот этот сорокадневный пост? Да чтобы вы последнюю скотину перед летом не сожрали. Сожрете скотину - будет голодный год, Бог вас так карает. А знаете, почему беспорядочный секс - это грех? Да потому что не знал никто раньше про сифилис и гонорею. Вот и думали, вот эти язвы - это их Бог наказывает. Или вот дни без еды, да? По средам и пятницам. Про интервальное голодание они тоже что-то знали.",
        img: 'https://e7.pngegg.com/pngimages/799/987/png-clipart-computer-icons-avatar-icon-design-avatar-heroes-computer-wallpaper-thumbnail.png',
        hashtags: ['asd', 'asd', 'asd'],
        avatarImg: 'https://e7.pngegg.com/pngimages/799/987/png-clipart-computer-icons-avatar-icon-design-avatar-heroes-computer-wallpaper-thumbnail.png',
        profileName: 'bebeb',
        accountTag: '@fff',
        commentsNumber: 3,
        likesCount: 4,
        clickCount: 2,
        watchCount: 5,
        spotlightCount: 5,
        registrationDate: 'ffff'
      }
    }
  },
};
</script>
