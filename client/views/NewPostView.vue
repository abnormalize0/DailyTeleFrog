<script setup>
  async function post_request() {
            let data = JSON.stringify( {
                            'name' : encodeURIComponent(document.post.title.value),
                            'preview_content' : encodeURIComponent(document.post.body.value),
                            'tags' : encodeURIComponent(document.post.tags.value),
                            'date' : new Date().toLocaleDateString('en-us', { month:"short", day:"numeric"})
                    });
            
            const response = await fetch("http://127.0.0.1:5000/article", {
                method: 'POST',
                headers: {
                    'Content-Type' : 'application/json',
                    'user-id': localStorage.id,
                    'article': data
                }
            } )

            if (response?.ok) {
                console.log('Ok!');
            } else {
                alert("Ошбика добавления поста\n");
                console.error(`HTTP Response Code: ${response?.status}`)
            }
        }
</script>

<template>
<H1>Новый пост</H1>
<FORM NAME="post">
    <TABLE>
        <TR><TD><B>Заголовок:</B></TD>
            <TD><INPUT NAME="title" SIZE=20></input></TD></TR>
        <TR><TD><B>Пост:</B></TD>
            <TD><INPUT NAME="body" SIZE=20></input></TD></TR>
        <TR><TD><B>Теги:</B></TD>
            <TD><INPUT NAME="tags" SIZE=20></input></TD></TR>
    </TABLE>
    <INPUT TYPE="button" VALUE="Готово" v-on:Click="$event=>post_request()"></input>
</FORM>
</template>