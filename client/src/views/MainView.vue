<template>
  <v-container>
    <v-row class="d-flex justify-center pt-15">
    <v-col cols="3">
      <LeftMenuComponent :groups="groups" />
    </v-col>
    <v-col cols="6">
      <PostPreview :post="post"></PostPreview>
    </v-col>
    <v-col cols="3">
      <RightMenuComponent />
    </v-col>
  </v-row>

  </v-container>
</template>

<script>
import PostPreview from "@/components/feed/post-preview/PostPreview.vue";
import LeftMenuComponent from "@/components/common/LeftMenuComponent.vue";
import RightMenuComponent from "@/components/common/right-menu/RightMenuComponent.vue";

export default {
  name: "MainView",
  components: {
    PostPreview,
    LeftMenuComponent,
    RightMenuComponent,
  },
  data() {
    return {
      groups: [
        {
          name: "onanisti",
          img: "community-icon",
        },
        {
          name: "dungeonSlaveZ",
          img: "community-icon",
        },
        {
          name: "boyNextDoor",
          img: "community-icon",
        },
        {
          name: "Jhohan pohan",
          img: "community-icon",
        },
        {
          name: "tester mokaka",
          img: "community-icon",
        },
      ],
      post: {
        header: 'Ответ на пост «А вот это интересная точка зрения',
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
}
</script>