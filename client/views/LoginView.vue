<script setup>
  async function login_request() {
            const response = await fetch("http://127.0.0.1:5000/users/check_password", {
                method: 'GET',
                mode: 'cors',
                headers: {
                    'user-id': document.login.login.value,
                    'password': document.login.password.value
                },
            } )
            let json = await response.json();
            console.log(json); 
            if (response?.ok) {
                alert("Пароль верный!")
                console.log('Ok!');
            } else {
                alert("Пароль неверный!");
                console.error(`HTTP Response Code: ${response?.status}`)
            }
            localStorage.id = document.login.login.value;
            window.location.href = "/";
        }
</script>

<template>
<H1>Вход</H1>
<FORM NAME="login">
    <TABLE>
        <TR><TD><B>ID:</B></TD>
            <TD><INPUT NAME="login" SIZE=20></input></TD></TR>
        <TR><TD><B>Пароль:</B></TD>
            <TD><INPUT NAME="password" SIZE=20></input></TD></TR>
    </TABLE>
    <INPUT TYPE="button" VALUE="Готово" v-on:Click="$event=>login_request()"></input>
</FORM>
</template>