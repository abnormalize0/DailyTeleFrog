<style>
  @import '../css/NewPostStyle.css';
</style>

<script setup>
  import { nextTick, ref } from 'vue';
  import { useMousePressed } from '@vueuse/core';
  import router from '../router';
  import axios from 'axios';

  const config = require('../config.json');

  const insert_menu_ref = ref(false);
  const { pressed } = useMousePressed();

  let counter = 0;

  let blocks = ref([]);
  let content = [];
  let block_type = [];

  let types_list = ["Подзаголовок", "Текст", "Изображение"];

  const sleep = (ms) => {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  let current_index = 0;

  async function open_insert_menu(e, index) {
    current_index = index;
    insert_menu_ref.value = true;
    await nextTick();

    let insert_menu = document.getElementById("insert_menu");
    insert_menu.style.top = e.clientY - 40 + "px";
    insert_menu.style.left = e.clientX - 190 + "px";
    insert_menu.onmouseleave = function() { insert_menu_ref.value = false; };
  }

  function add_element(index) {
    blocks.value.splice(current_index, 0, counter);
    content.push(types_list[index] + counter);
    block_type.push(index);
    counter++;
    insert_menu_ref.value = false;
  }

  function block_shift(index, new_index) {
    let temp = blocks.value[index];
    blocks.value[index] = blocks.value[new_index];
    blocks.value[new_index] = temp;
    
    let elem = document.getElementById("elem" + blocks.value[index]);
    for(let i = 0; i < counter; i++) {
      let tmp_elem = document.getElementById("elem" + i);
      if(tmp_elem.classList.contains("element_hidden")) {
        tmp_elem.classList.remove("element_hidden");
        tmp_elem.classList.add("element");
      }
    }
    elem.classList.remove("element");
    elem.classList.add("element_hidden");
  }

  let posx = -1;
  let posy = -1;

  function hold_begin(e, index) {
    let elem = document.getElementById("elem" + blocks.value[index]);
    elem.classList.remove("element");
    elem.classList.add("element_hidden");
    document.onmousemove = (e) => position(e, index);
    
    let float_element = document.createElement('div');
    float_element.className = "element_float";
    float_element.id = "float_element";
    float_element.innerHTML = elem.innerHTML;
    document.body.append(float_element);

    float_element.style.top = elem.getBoundingClientRect().top + "px";
    float_element.style.left = elem.getBoundingClientRect().left + "px";

    posx = e.clientX;
    posy = e.clientY;
  }

  async function position(e, index) {
    document.onmousemove = null;
    let float_element = document.getElementById("float_element");
    float_element.style.top = float_element.getBoundingClientRect().top + (e.clientY - posy) + "px";
    float_element.style.left = float_element.getBoundingClientRect().left + (e.clientX - posx) + "px";
    posx = e.clientX;
    posy = e.clientY;

    let event_setter = 0;
    
    if(index > 0) {
      let upstairs_neighbor = document.getElementById("elem" + blocks.value[index - 1]);
      if(float_element.getBoundingClientRect().top < upstairs_neighbor.getBoundingClientRect().top + 25) { //захардкодил размеры блоков пока что
        await block_shift(index, index - 1);
        document.onmousemove = (e) => position(e, index - 1);
        event_setter = 1;
      }
    }

    if(index < blocks.value.length - 1) {
      let downstairs_neighbor = document.getElementById("elem" + blocks.value[index + 1]);
      if(float_element.getBoundingClientRect().top > downstairs_neighbor.getBoundingClientRect().top - 25) {
        await block_shift(index, index + 1);
        document.onmousemove = (e) => position(e, index + 1);
        event_setter = 1;
      }
    }

    if(!event_setter) {
      document.onmousemove = (e) => position(e, index);
    }
      
    if(!pressed.value) {
      document.onmousemove = null;
      let elem = document.getElementById("elem" + blocks.value[index]);
      smooth_transition(elem, float_element);
      posx = -1;
      posy = -1;
    }
  }

  async function smooth_transition(elem, float_element) {
    let gapx = (elem.getBoundingClientRect().top - float_element.getBoundingClientRect().top) / 30;
    let gapy = (elem.getBoundingClientRect().left - float_element.getBoundingClientRect().left) / 30;
    for(let i = 0; i < 30; i++) {
      float_element.style.top = float_element.getBoundingClientRect().top + gapx + "px";
      float_element.style.left = float_element.getBoundingClientRect().left + gapy + "px";
      await sleep(1);
    }
    document.getElementById("float_element").remove();
    elem.classList.add("element");
    elem.classList.remove("element_hidden");
  }

  let allow_edit = 1;

  async function edit_content(index) {
    if(!allow_edit) {
      return;
    }
    allow_edit = 0;
    let target = document.getElementById("content" + index);
    let local_content = target.innerHTML;
    target.innerHTML = "<form><input id='active_input' value=" + local_content + "></form>";
    let input = document.getElementById("active_input");
    input.focus();
    input.addEventListener("focusout", () => {
      content[index] = input.value;
      target.innerHTML = input.value;
      allow_edit = 1;
    })
  }

  async function edit_image(index) {
    if(!allow_edit) {
      return;
    }
    allow_edit = 0;
    let target = document.getElementById("content" + index);
    target.innerHTML = "<img id='img" + index + "' width='600' src='" + content[index] + "'><input class='image_loader' id='active_input' type='file'>";
    let input = document.getElementById("active_input");
    input.click();
    input.addEventListener("change", async () => {
      console.log(input.files[0])
      target.innerHTML = "<img id='img" + index + "' width='100'>";
      document.querySelector("#img" + index).src = "https://i.giphy.com/media/sSgvbe1m3n93G/giphy.webp";
      allow_edit = 1;
        
      // let myHeaders = new Headers();
      // let formdata = new FormData();
      // myHeaders.append("Authorization", "Bearer " + config.keys.imgur);
      // formdata.append("image", input.files[0]);
      // let requestOptions = {
      //   method: 'POST',
      //   headers: myHeaders,
      //   body: formdata,
      //   redirect: 'follow'
      // };

      // const request = await fetch("https://api.imgur.com/3/upload", requestOptions);
      // let response = await request.json();
      // target.innerHTML = "<img id='img" + index + "' width='600'>";
      // document.querySelector("#img" + index).src = response.data.link;
      // content[index] = response.data.link;
        

      var reader = new FileReader();
      reader.readAsDataURL(input.files[0]);
      reader.onload = async function () {
        const myForm = new FormData();
        myForm.append("image", reader.result.substring(reader.result.indexOf(",") + 1));

        await axios.post("https://api.imgbb.com/1/upload?key=" + config.keys.imgbb, myForm, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }).then((response) => {
          console.log(response);
          target.innerHTML = "<img id='img" + index + "' width='600'>";
          document.querySelector("#img" + index).src = response.data.data.url;
          content[index] = response.data.data.url;
        }).catch((err) => {
          console.log(err);
        });
      };
    })
  }

  async function post_request() {
    let article = [];
    for(let i = 0; i < counter; i++) {
      article.push({
        type: block_type[blocks.value[i]], 
        content: encodeURIComponent(content[blocks.value[i]]),
      });
    }
    let post = {
      'article-body': JSON.stringify(article), 
      'preview-content': JSON.stringify(article), 
      name: encodeURIComponent("test"), 
      tags: encodeURIComponent("~abc~bca~cab~"), 
    };
    console.log(JSON.stringify(post));
    const request = await fetch("http://127.0.0.1:5000/article", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'user-id': localStorage.id
      },
      body: JSON.stringify(post)
    });
    let status = await request.json();
    console.log(status);
    if(status.status) {
      router.push({ name: 'post', params: { id: status.article_id } });
    } else {
      alert("Ошибка добавления поста.");
    }
  }
    
</script>

<template>
  <div class="worksheet" id="worksheet">
    <div v-for="(block, index) in blocks" v-bind:key="index">
      <div v-if="block_type[block] == 0" @click="edit_content(block)" class="content_header" :id="`content` + block">{{ content[block]}}</div>
      <div v-if="block_type[block] == 1" @click="edit_content(block)" class="content_text" :id="`content` + block">{{ content[block]}}</div>
      <div v-if="block_type[block] == 2" @click="edit_image(block)" class="content_text" :id="`content` + block"><img :id="`img` + block" width='600' :src="content[block]"></div>
      <br>
    </div>
  </div>
  <div class="right_menu" id="right_menu">
    <div @click="open_insert_menu($event, 0)" class="add"></div>
    <div v-for="(block, index) in blocks" v-bind:key="index">
      <div @mousedown="hold_begin($event, index)" :class="`element`" :id="`elem` + blocks[index]">{{block}}</div>
      <div @click="open_insert_menu($event, index + 1)" :class="`add`"></div>
    </div>
  </div>
  <div class="insert_menu" id="insert_menu" v-if="insert_menu_ref">
    <div v-for="(type, index) in types_list" v-bind:key="index">
      <div class="insert_menu_element" @click="add_element(index)"> {{ type }}</div>
    </div>
  </div>

  <div class="post_button" @click="post_request()">
    Запостить
  </div>

</template>