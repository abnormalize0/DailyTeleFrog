<template>
  <div 
    class="d-flex 
      flex-column 
      primary-rounded 
      background-secondary-color 
      align-center wrap-menu"
  >
    <div class="h2 text-color">Войти</div>
    <div class="d-flex flex-column w-100 login-form">
      <BasicInput label="Логин"/>
      <BasicInput label="Пароль"/>
      <div class="d-flex justify-center publsh-post-button">
        <BasicPrimaryButton
          class="w-100"
          content="Войти"
        ></BasicPrimaryButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wrap-menu {
  width: 267px;
  height: auto;
  padding: 20px;
  gap: 11px;
}
.login-form {
  gap: 15px;
}
</style>

<script>
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import BasicInput from "@/components/basic/input/BasicInput.vue";

export default {
  name: "RightMenuComponent",
  components: { BasicPrimaryButton, BasicInput },
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
