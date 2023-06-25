<script setup>
  async function register_request() {
            let request = '{"name": "' + document.register.login.value + '", "password": "' 
            + document.register.password.value + '", "page": "' + document.register.login.value + '"}';
            console.log(request);
            const response = await fetch("http://127.0.0.1:5000/users/new", {
                method: 'POST',
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json',
                    'user-info': request
                },
            } )

            if (response?.ok) {
                alert("Успешно")
                console.log('Ok!');
            } else {
                alert("Ошбика добавления пользователя (скорее всего такой пользователь уже зарегистрирован)");
                console.error(`HTTP Response Code: ${response?.status}`)
            }
        }
</script>

<template>
<H1>Регистрация</H1>
<FORM NAME="register">
    <TABLE>
        <TR><TD><B>Логин:</B></TD>
            <TD><INPUT NAME="login" SIZE=20></input></TD></TR>
        <TR><TD><B>Пароль:</B></TD>
            <TD><INPUT NAME="password" SIZE=20></input></TD></TR>
    </TABLE>
    <INPUT TYPE="button" VALUE="Готово" v-on:Click="$event=>register_request()"></input>
</FORM>
</template>