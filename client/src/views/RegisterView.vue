<template>
  <h1>Регистрация</h1>
  <form name="register">
    <table>
      <tr><td><b>Логин:</b></td><td><input name="login" size=20></td></tr>
      <tr><td><b>Пароль:</b></td><td><input name="password" size=20></td></tr>
    </table>
    <input type="button" value="Готово" @click="register_request()">
  </form>
</template>

<script>
  import router from '../router';
  export default {
    methods: {
      async register_request() {
        let user_info = {
          name: document.register.login.value,
          password: document.register.password.value
        };
        const request = await fetch("http://127.0.0.1:5000/users", {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(user_info),
        });
        let status = await request.json();
        console.log(status);
        if (status.status) {
          localStorage.id = status.user_id;
          router.push({ name: 'feed'});
        } else {
          alert("Что-то пошло не так.");
        }
      }
    }
  }
</script>