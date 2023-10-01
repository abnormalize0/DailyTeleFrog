<script setup>
  import router from '../router';
  async function login_request() {
    const request = await fetch("http://127.0.0.1:5000/users/check_password", {
      method: 'GET',
      headers: {
        'user-id': document.login.login.value,
        'password': document.login.password.value,
      },
    });
    let status = await request.json();
    console.log(status);
    if (status["is-correct"]) {
      localStorage.id = document.login.login.value;
      router.push({ name: 'feed'});
    } else {
      alert("Пароль неверный!");
    }
  }
</script>

<template>
  <h1>Вход</h1>
  <form name="login">
    <table>
      <tr><td><b>ID:</b></td><td><input name="login" size=20></td></tr>
      <tr><td><b>Пароль:</b></td><td><input name="password" size=20></td></tr>
    </table>
    <input type="button" value="Готово" @click="login_request()">
  </form>
</template>