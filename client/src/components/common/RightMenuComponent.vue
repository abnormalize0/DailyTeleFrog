<template>
  <div
    class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu"
  >
    <div class="h2 text-color">Войти</div>
    <div class="d-flex flex-column w-100 login-form">
      <BasicInput label="Логин" />
      <BasicInput label="Пароль" />
      <div class="register-lostpassword-wrap d-flex">
        <button class="p3 striped-button">Забыли пароль?</button>
        <button class="p3 striped-button">Регистрация</button>
      </div>
      <div class="d-flex justify-center publsh-post-button">
        <BasicPrimaryButton class="w-100" content="Войти"></BasicPrimaryButton>
      </div>
    </div>
  </div>
  <button
    @click="topFunction()"
    class="to-top"
    style="color: white; display: none; position: sticky; top: 25px"
  >
    наверх
  </button>
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
.striped-button {
  background: none !important;
  border: none;
  padding: 0 !important;
  text-decoration: underline;
  color: white;
}
.register-lostpassword-wrap {
  justify-content: space-between;
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
  created() {
    window.addEventListener("scroll", this.handleScroll);
  },
  unmounted() {
    window.removeEventListener("scroll", this.handleScroll);
  },
  methods: {
    handleScroll() {
      let goToTopButton = document.querySelector(".to-top");
      if (
        document.body.scrollTop > 20 ||
        document.documentElement.scrollTop > 20
      ) {
        goToTopButton.style.display = "block";
      } else {
        goToTopButton.style.display = "none";
      }
    },
    topFunction() {
      document.body.scrollTop = 0; // For Safari
      document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
    },
  },
};
</script>
