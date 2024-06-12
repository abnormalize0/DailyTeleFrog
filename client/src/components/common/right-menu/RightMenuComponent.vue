<template>
  <div class="wrap-menu primary-rounded background-secondary-color">
    <div class="d-flex justify-center avatar-login-section">
      <AvatarBlockComponent :avatarBlock="avatarBlock"></AvatarBlockComponent>
    </div>
    <div class="d-flex justify-center publsh-post-button">
      <BasicPrimaryButton
        class="button-right-menu"
        content="ОПУБЛИКОВАТЬ ПОСТ"
      ></BasicPrimaryButton>
    </div>
  </div>
</template>

<style scoped>
.wrap-menu {
  width: 275px;
  height: 280px;
  margin: 12px 0px 10px 0px;
}
.button-right-menu {
  height: 50px !important;
  width: 235px;
}
.publish-post-button {
}
.avatar-login-section {
}
</style>

<script>
import BasicPrimaryButton from "@/components/basic/BasicPrimaryButton.vue";
import AvatarBlockComponent from "@/components/common/right-menu/AvatarBlockComponent.vue";

export default {
  name: "RightMenuComponent",
  components: { BasicPrimaryButton, AvatarBlockComponent },
  props: {
    groups: [],
  },
  data() {
    return {
      avatarBlock: {
        avatarImgSrc: "../../../assets/Avatar.png",
        subscribers: 30,
        rating: 2000,
        patrons: 2,
        profileName: "koks",
        profileTag: "@keks",
      },
    };
  },
  mounted() {},
  methods: {},
};
</script>
