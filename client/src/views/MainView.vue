<template>
  <div class="d-flex justify-center pt-15">
    <div>
        <LeftMenuComponent :groups="groups" />
    </div>
    <PostPreview :post="post"></PostPreview>
    <div class="right-menu-container">
      <div>
        <RightMenuComponent />
      </div>
    </div>
  </div>
</template>

<style scoped>
.right-menu-container {
  width: 100%;
  display: flex;
  justify-content: right;
}
.enter-container {
  justify-content: right;
}
</style>

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