<template>
  <v-dialog v-model="dialog" width="auto">
    <v-card>
      <draggable v-model="slidesarray[current_image]"  handle=".handle" @dragstart="drag_start_handler_image">
        <template #item="{ element: block, index }">
          <div class="modal-grid">
            <img class="handle" :src=block.image style="max-height: 80px;">
            <input @input="image_title(index, $event)" class="ddinput" size="10" :value=block.title />
            <div style="font-size: 40px" @click="delete_img(index)">&times;</div>
          </div>
        </template>
      </draggable>
      <div v-if="current_image != -1 && slidesarray[current_image].length < 10">
        <div class="modal-grid">
          <input type="file" multiple @change="load_img"/>
        </div>
      </div>
      <template v-slot:actions>
        <v-btn class="ms-auto" text="Закрыть" @click="dialog = false"></v-btn>
      </template>
    </v-card>
  </v-dialog>

  <v-snackbar
    v-model="snackbar"
    :timeout=2000
    location="bottom right"
    color="light-blue-darken-4"
    max-width=1
  >
    Должна остаться хотя бы одна картинка.
  </v-snackbar>

  <div class="worksheet-class" @scroll="scroll_worker()" ref="worksheet">
    <div v-for="(block, index) in blocks" v-bind:key="index" :ref="el => { if (el) block_element[index] = el }" class="element blink">
      <div class="single-block">
        <QuillEditor placeholder="Вставить текст" v-if="block.type == 'text'" v-model:content="markdown_content[block.id]" theme="bubble" :options="options" />
        <vueper-slides v-if="block.type == 'carousel'" fade :touchable="false" arrows-outside bullets-outside :slide-ratio="1080 / 1920">
          <vueper-slide
            v-for="(slide, i) in slidesarray[block.id]"
            :key="i"
            :image="slide.image"
            :title="slide.title"
            @click="expand(block.id)" />
        </vueper-slides>
      </div>
    </div>
  </div>

  <div class="right-menu">
    <draggable v-model="blocks" animation="150" :options="{forceFallback: true}">
      <template #item="{ element: block }">
        <div 
          @mouseover="show_menu_buttons(block.id)" @mouseleave="hide_menu_buttons(block.id)" 
          class="miniature-item"
          @dragstart="drag_start_handler(block.id, $event)"
          @dragend="drag_end_handler"
          :style="{ height: block.height + 'px' }"
        >
          <v-menu target="cursor">
            <template v-slot:activator="{ props }">
              <v-btn @click="block_place = 0" color="success" position="absolute" density="compact" icon="mdi-plus" class="insert-button" v-bind="props" v-if="block.insert_buttons">+</v-btn>
              <div class="miniature" @click="scroll_to(block.id)">{{ block.name }}</div>
              <v-btn @click="block_place = 1" color="success" position="absolute" density="compact" icon="mdi-plus" class="insert-button" v-bind="props" v-if="block.insert_buttons">+</v-btn>
            </template>
            <v-list>
              <v-list-item
                v-for="(item, index) in items"
                :key="index"
              >
                <v-list-item-title @click="add_element(item.type, block.id)">{{ item.title }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
      </template>
    </draggable>
    <div class="miniature-position" :class="{'fade': scroll_fade}" :style="{ top: scroll_position + 'px', height: worksheet.clientHeight * scale + 'px' }" v-if="scroll_visibility"></div>
  </div>

  <div class="submit" @click="submit()">Опубликовать</div>

</template>

<style>
  .insert-button {
    right: 50%;
  }

  .miniature {
    outline-style: solid;
    outline-color: black;
    width: 150px;
    background-color: blue;
    height: 100%;
  }

  .worksheet-class {
    position: absolute;
    width: 100%;
    height: 80%;
    position: fixed;
    overflow-y: scroll;
  }

  .right-menu {
    height: 80%;
    width: 150px;
    background-color: white;
    position: fixed;
    right: 0;
    overflow-y: scroll;
  }

  .miniature-item {
    display: block;
    background-color: transparent;
  }

  .sortable-ghost {
    overflow: hidden;
  }

  .drag-preview {
    position: absolute;
    transform: translateX(-50%) translateY(-50%) translateY(55%);
  }

  .element {
    transition: background-color 0.5s;

  }

  .element.blink {
    animation: mymove 1s;
  }
  .element.blink2 {
    animation: mymove2 1s;
  }

  @keyframes mymove {
    0% {background-color: transparent;}
    50% {background-color: white;}
    100% {background-color: transparent;}
  }

  @keyframes mymove2 {
    0% {background-color: transparent;}
    50% {background-color: white;}
    100% {background-color: transparent;}
  }

  .miniature-position {
    width: 140px;
    height: 0px;
    background-color: rgba(251, 255, 255, 0.4);
    outline-style: solid;
    outline-color: black;
    position: absolute;
    opacity: 1;
    transition: opacity 0.2s ease-in-out;
  }

  .miniature-position.fade {
    opacity: 0;
  }

  .single-block {
    width: 50%;
    margin-left: auto;
    margin-right: auto;
    transition: background-color 0.5s
  }

  .vueperslide__title {
    font-size: 1.2em;
    opacity: 1;
    background: rgba(0,0,0,.6);
    backdrop-filter: grayscale(1) contrast(3) blur(1px);
  }

  .vueperslide__content-wrapper {
    justify-content: flex-end !important;
    align-items: flex-end !important;
  }

  .modal-grid {
    display: grid;
    grid-template-columns: 120px 420px 40px;
    padding: 5px 0 0 20px;
  }

  .ql-editor.ql-blank:before {
    color: white;
  }

  .submit {
    position: fixed;
    bottom: 0px;
    left: 0px;
    background-color: red;
  }

</style>

<script>
  import draggable from 'vuedraggable';
  import { QuillEditor } from '@vueup/vue-quill'
  import 'quill-paste-smart';
  import {ref, onBeforeUpdate} from 'vue';

  import '@vueup/vue-quill/dist/vue-quill.snow.css';
  import '@vueup/vue-quill/dist/vue-quill.bubble.css';

  import { VueperSlides, VueperSlide } from 'vueperslides'
  import 'vueperslides/dist/vueperslides.css'

  import axios from 'axios';

  export default {
    components: {
        draggable,
        QuillEditor,
        VueperSlides, 
        VueperSlide
    },
    setup() {
      const block_element = ref([])
      onBeforeUpdate(() => {
        block_element.value = []
      })
      const worksheet = ref(null)
      return {
        block_element,
        worksheet
      }
    },
    data() {
      return {
        blocks: [
          {name:'Element 0', id: 0, type: "text", insert_buttons: false, height: 0},
        ],
        options: {
          modules: {
            toolbar: ['bold', 'italic', 'underline', 'strike', { 'list': 'ordered'}, { 'list': 'bullet' }, 'link', 'clean' ],
          },
        },
        items: [
          { title: 'Текстовое поле', type: 'text' },
          { title: 'Карусель изображений', type: 'carousel' },
        ],
        scroll_position: 0,
        scroll_fade: false,
        scroll_visibility: false,   //три переменные которые отвечают за позиционирование и видимость указателя позиции в правом меню
        snackbar: false,            //видимость окна уведомления о том что нельзя удалять последнюю картинку
        dialog: false,              //видимость окна добавления картинок
        last_id: 1,                 //текущий последний идентификатор чтоб знать какой присваивать новым блокам
        scale: 0.5,                 //множитель скалирования миниатюр в правом меню
        timer: 0,                   //хехе рекурсия делает бррр
        current_image: -1,          //идентификатор чтоб окну добавления картинок знать с каким элментом он работает
        block_place: 0,             //добавлять новый блок до или после целевого
        allow_menu: 1,              //позволять или нет поялвяться кнопкам при наведении на миниатюру (запрещаю если прямо сейчас происходит драгндроп)
        markdown_content: [],       //содержимое текстовых полей маркдаун эдиторов
        slides: [
          {
            title: 'Заглушка для картинки',
            image: 'https://images.unsplash.com/photo-1431440869543-efaf3388c585?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'
          }
        ],
        slidesarray: []
      }
    },
    //todo: do something with block.height
    updated() {
      let cc = 0;
      this.blocks.forEach((block) => {
        block.height = this.block_element[cc].clientHeight * this.scale
        cc++
      })
    },
    methods: {
      add_element(type, target_block) {
        this.blocks.splice(this.blocks.findIndex((element) => element.id == target_block) + this.block_place, 0, {name:'Element ' + this.last_id, id: this.last_id, type: type, insert_buttons:false, height: 0})
        if(type == 'carousel') {
          this.slidesarray[this.last_id] = structuredClone(this.slides);
        }
        this.last_id++
      },
      drag_start_handler(id, e) {
        this.allow_menu = 0;
        e.dataTransfer.setDragImage(new Image(), 0, 0);
        this.hide_menu_buttons(id);
      },
      drag_start_handler_image(e) {
        e.dataTransfer.setDragImage(new Image(), 0, 0);
      },
      drag_end_handler() {
        this.allow_menu = 1;
      },
      scroll_to(id) {
        let target = this.blocks.findIndex((element) => element.id == id)
        this.block_element[target].scrollIntoView({ behavior: 'smooth' });
        this.block_element[target].classList.toggle("blink")
        this.block_element[target].classList.toggle("blink2")

      },

      sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
      },
      //todo: think about scroll_position
      scroll_worker() {
        this.scroll_position = this.worksheet.scrollTop * this.scale
        this.scroll_visibility = true
        if (this.timer == 0) {
          this.scroll_fade = false
          this.timer = 4
          this.position_shutdown()
        } else {
          this.timer = 4
        }
      },
      async position_shutdown() {
        while(this.timer > 0) {
          this.timer--;
          await new Promise(resolve => setTimeout(resolve, 50));
        }
        this.scroll_fade = true
        setTimeout(() => this.scroll_visibility = false, 200);
      },
      expand(index) {
        this.dialog = true
        this.current_image = index;
      },
      image_title(index, event) {
        this.slidesarray[this.current_image][index].title = event.target.value;
      },
      delete_img(index) {
        if(this.slidesarray[this.current_image].length == 1) {
          this.snackbar = true;
          return;
        }
        this.slidesarray[this.current_image].splice(index, 1);
      },
      load_img(event) {
        let config = require('../config.json');
        let target_array;
        if (event.target.files.length + this.slidesarray[this.current_image].length > 10) {
          target_array = Array.prototype.slice.call( event.target.files, 0, 10 - this.slidesarray[this.current_image].length);
        } else {
          target_array = event.target.files
        }
        target_array.forEach((element) => {
          if(this.slidesarray[this.current_image].length == 10) {
            return;
          }
          let reader = new FileReader();
          reader.readAsDataURL(element);
          reader.onload = () => {
            const myForm = new FormData();
            myForm.append("image", reader.result.substring(reader.result.indexOf(",") + 1));

            axios.post("https://api.imgbb.com/1/upload?key=" + config.keys.imgbb, myForm, {
              headers: {
                "Content-Type": "multipart/form-data",
              },
            }).then((response) => {
              this.slidesarray[this.current_image].push({
                title: '',
                image: response.data.data.url
              })
            });
          };
        });
      },
      show_menu_buttons(id) {
        if(!this.allow_menu){
          return;
        }
        this.blocks.find((element) => element.id == id).insert_buttons = true;
      },
      hide_menu_buttons(id) {
        this.blocks.find((element) => element.id == id).insert_buttons = false;
      },
      submit() {

      }
    }
  }
  
</script>
