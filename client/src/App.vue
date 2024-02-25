<style>
  @import '../public/css//MainStyle.css';
  @import '../public/css/styles.css';
</style>

<script setup>
  import { watch, ref } from "vue";
  import { useRoute } from "vue-router";

  const login = ref(false);
  const route = useRoute();
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
  </div>
  <router-view/>
</template>
