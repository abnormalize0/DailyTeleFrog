<style>
  @import 'css/MainStyle.css';
</style>

<script setup>
  import { watch, ref } from "vue";
  import { useRoute } from "vue-router";

  const menu_refresh = ref(true);
  const route = useRoute();
  let login = 0;
  watch(
    () => route.fullPath,
    async () => {
      console.log("changed");
      console.log(localStorage.id);
      menu_refresh.value = false;
      if ((localStorage.getItem("id") === null) || (localStorage.id == 0)) {
        localStorage.id = 0;
        login = 0;
      } else {
        login = 1;
      }
      menu_refresh.value = true;
    }
  );

  if ((localStorage.getItem("id") === null) || (localStorage.id == 0)) {
    localStorage.id = 0;
  } else {
    login = 1;
  }
</script>

<template>
  <div class="top">
    <h1 style="padding: 10px;">MVP</h1>
    <nav v-if="menu_refresh">
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
