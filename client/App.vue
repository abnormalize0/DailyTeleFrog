<script setup>
  var login = 0;
  if (localStorage.getItem("id") === null) {
    // alert ("empty");
    // localStorage.id = -1;
  } else {
    login = 1
  }
</script>

<template>
  <body>
  <top>
    <h1>Статьямбус</h1>
    <nav>
      <router-link to="/">Главная</router-link> |
      <router-link to="/about">О сайте</router-link> |
      <span v-if="!login"><router-link to="/login">Войти</router-link> | </span>
      <span v-if="!login"><router-link to="/register">Регистрация</router-link> </span>
      <span v-if="login"><router-link to="/new_post">Добавить статью</router-link> | </span>
      <span v-if="login"><router-link to="/profile">Профиль</router-link> | </span>
      <span v-if="login"><router-link to="/exit">Выйти</router-link> </span>
    </nav>
  </top>
  <router-view/>
  
  </body>
</template>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

body::-webkit-scrollbar{
  display: none;
}

top {
  position: sticky;
  top: 21.44px;
  background-color: white;
  display: block;
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
}

nav a.router-link-exact-active {
  color: #42b983;
}

.post-item {
  border: solid;
}
</style>

<script>
  
</script>
