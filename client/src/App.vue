<style>
  @import '../public/css//MainStyle.css';
  @import '../public/css/styles.css';
</style>

<script setup>
  import { watch, ref } from "vue";
  import { useRoute } from "vue-router";
  import MainPost from "./components/post/MainPost/MainPost.vue";

  const login = ref(false);
  const route = useRoute();
  const hashtags = ["bebra", "booba", "chipi"]; 
  const placeholder = "https://media.istockphoto.com/id/1147544807/vector/thumbnail-image-vector-graphic.jpg?s=612x612&w=0&k=20&c=rnCKVbdxqkjlcs3xH87-9gocETqpspHFXu5dIGB4wuM="
  watch(
    () => route.fullPath,
    async () => {
      console.log("changed");
      console.log(localStorage.id);
      if ((localStorage.getItem("id") === null) || (localStorage.id == 0)) {
        localStorage.id = 0;
        login.value = 0;
      } else {
        login.value = 1;
      }
    }
  );

  if ((localStorage.getItem("id") === null) || (localStorage.id == 0)) {
    localStorage.id = 0;
  } else {
    login.value = 1;
  }
</script>

<template>
  
  <div class="top">
    <h1 style="padding: 10px;">MVP</h1>
    <nav>
      <router-link to="/">Главная</router-link> |
      <router-link to="/about">О сайте</router-link> |
      <span v-if="!login"><router-link to="/login">Войти</router-link> | </span>
      <span v-if="!login"><router-link to="/register">Регистрация</router-link> </span>
      <span v-if="login"><router-link to="/new_post">Добавить статью</router-link> | </span>
      <span v-if="login"><router-link to="/profile">Профиль</router-link> | </span>
      <span v-if="login"><router-link to="/exit">Выйти</router-link> </span>
    </nav>
    <MainPost :img="placeholder" :hashtags="hashtags" header="Lorem ipsum" body="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."></MainPost>
  </div>
  <router-view/>
</template>
