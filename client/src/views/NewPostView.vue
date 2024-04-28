<template>
  <v-dialog v-model="dialog" width="auto">
    <v-card>
      <draggable v-model="slidesarray[current_image]"  handle=".handle" @dragstart="drag_start_handler">
        <template #item="{ element: block, index }">
          <div class="modal-grid">
            <img class="handle" :src=block.image style="max-height: 80px;">
            <input @input="image_title(index)" class="ddinput" size="10" :value=block.title />
            <div style="font-size: 40px" @click="delete_img(index)">&times;</div>
          </div>
        </template>
      </draggable>
      <div v-if="current_image != -1 && slidesarray[current_image].length < 10">
        <div class="modal-grid">
          <input v-model="image_src" class="ddinput" size="10" placeholder="Укажите URL" />
          <div style="font-size: 40px" @click="add_img()">&or;</div>
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
    <div v-for="(block, index) in blocks" v-bind:key="index" :ref="el => { if (el) block_element[index] = el }" class="element">
      <div class="single-block">
        <QuillEditor placeholder="Вставить текст" v-if="block.type == 'text'" v-model:content="myContent[block.id]" theme="bubble" :options="options" />
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
          @dragstart="drag_start_handler"
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
    <div class="miniature-position" :class="{'fade': scroll_fade}" :style="{ top: scroll_position + 'px', height: scroll_height + 'px' }" v-if="scroll_visibility"></div>
  </div>

  <div class="submit" @click="submit()">Опубликовать</div>

</template>

<script>
  import draggable from 'vuedraggable';
  import { QuillEditor } from '@vueup/vue-quill'
  import 'quill-paste-smart';
  import {ref, onBeforeUpdate} from 'vue';
  // import { toRaw } from 'vue';

  import '@vueup/vue-quill/dist/vue-quill.snow.css';
  import '@vueup/vue-quill/dist/vue-quill.bubble.css';

  import { VueperSlides, VueperSlide } from 'vueperslides'
  import 'vueperslides/dist/vueperslides.css'

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
        scroll_height: 0,
        scroll_fade: false,
        scroll_visibility: false,
        image_src: "",
        snackbar: false,
        dialog: false,
        last_id: 1,
        scale: 0.5,
        timer: 0,
        current_image: -1,
        block_place: 0,
        allow_menu: 1,
        myContent: [],
        slides: [
          {
            title: 'Заглушка для картинки',
            image: 'https://images.unsplash.com/photo-1431440869543-efaf3388c585?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'
          }
        ],
        slidesarray: []
      }
    },
    updated() {
      let cc = 0;
      this.blocks.forEach((block) => {
        block.height = this.block_element[cc].clientHeight * this.scale
        cc++
      })
      this.scroll_height = this.worksheet.clientHeight * this.scale
    },
    methods: {
      add_element(type, target_block) {
        this.blocks.splice(this.blocks.map(function (img) { return img.id; }).indexOf(target_block) + this.block_place, 0, {name:'Element ' + this.last_id, id: this.last_id, type: type, insert_buttons:false, height: 0})
        if(type == 'carousel') {
          this.slidesarray[this.last_id] = structuredClone(this.slides);
        }
        this.last_id++
      },
      drag_start_handler(e) {
        this.allow_menu = 0;
        e.dataTransfer.setDragImage(new Image(), 0, 0);
        this.blocks.forEach((block) => {
          this.hide_menu_buttons(block.id);
        })
      },
      drag_end_handler() {
        this.allow_menu = 1;
      },
      scroll_to(id) {
        let target = this.blocks.findIndex((element) => element.id == id)
        this.block_element[target].scrollIntoView({ behavior: 'smooth' });
        setTimeout(() => this.block_element[target].classList.toggle("blink"), 300);
        setTimeout(() => this.block_element[target].classList.toggle("blink"), 800);
      },
      scroll_worker() {
        this.scroll_position = this.worksheet.scrollTop * this.scale
        this.scroll_visibility = true
        if (this.timer == 0) {
          this.scroll_fade = false
          this.timer = 4
          this.recursive_shutdown()
        } else {
          this.timer = 4
        }

      },
      recursive_shutdown() {
        let that = this;
        if (this.timer > 0) {
          this.timer--
          setTimeout(() => that.recursive_shutdown(), 50);
          return
        }
        this.scroll_fade = true
        setTimeout(() => this.scroll_visibility = false, 200);
      },
      expand(index) {
        this.dialog = true
        this.current_image = index;
      },
      image_title(index) {
        this.slidesarray[this.current_image][index].title = this.block[this.current_image].title;
      },
      delete_img(index) {
        if(this.slidesarray[this.current_image].length == 1) {
          this.snackbar = true;
          return;
        }
        this.slidesarray[this.current_image].splice(index, 1);
      },
      add_img() {
        this.slidesarray[this.current_image].push({
          title: '',
          image: this.image_src
        })
        this.image_src = "";
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

<style>
  .insert-button {
    /* top: 40px; left: 40px; */
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
    transition: background-color 0.5s
  }

  .element.blink {
    background-color: white;
    transition: background-color 0.5s
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