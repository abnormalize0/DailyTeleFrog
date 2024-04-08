<style>
  @import '../../public/css/NewPostStyle.css';
</style>

<template>

  <div>че</div>


  <div class="modal_menu" id="modal_menu" @focusout="handle_focus_out" tabindex="0">
    <div @click="add_element('text')" class="block_type" >Текстовый блок</div>
    <div @click="add_element('carousel')" class="block_type">Карусель изображений</div>
  </div>

  <div>че</div>

  <div id="modal_image_insert" class="modal_image_insert">
    <span class="close" @click="collapse()">&times;</span>
    <div class="modal_back">
      <draggable v-model="slidesarray[current_image]"  handle=".handle" @dragstart="drag_start_handler">
        <template #item="{ element: block, index }">
          <div class="modal_grid">
            <img class="handle" :src=block.image style="max-height: 8vh;">
            <input :id="`img_title` + index" @input="image_title(index)" size="10" :value=block.title />
            <div style="font-size: 40px; color:black;" @click="delete_img(index)">&times;</div>
          </div>
        </template>
      </draggable>
      <div class="addition" v-if="current_image != -1 && slidesarray[current_image].length < 10">
        <div class="modal_grid">
          <input id="new_img" size="10" placeholder="Укажите URL" />
          <div style="font-size: 40px; color:black;" @click="add_img()">&or;</div>
        </div>
      </div>
    </div>
  </div>

  <div class="worksheet" id="worksheet" @scroll="scroll_worker()">
    <div v-for="(block, index) in blocks" v-bind:key="index" :id="'block_element' + block.id" class="element">
      <div class="single_block">
        <QuillEditor placeholder="Вставить текст" v-if="block.type == 'text'" v-model:content="myContent[block.id]" theme="bubble" @update:content="() => on_update(block.id)" :options="options" />
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

  <div class="right_menu">
    <div class="position" id="position"></div>
    <draggable v-model="blocks" animation="150" :options="{forceFallback: true}">
      <template #item="{ element: block }">
        <div 
          @mouseover="show_menu_buttons(block.id)" @mouseleave="hide_menu_buttons(block.id)" 
          class="miniature_item"
          @dragstart="drag_start_handler"
          @dragend="drag_end_handler"
          :id="`miniature_item` + block.id"
        >
          <div class="insert_button" :id="`top_insert` + block.id" @click="open_add_menu($event, block.id); block_place = 0"></div>
          <div class="miniature" @click="scroll_to(block.id)" :id="`miniature` + block.id">{{ block.name }}</div>
          <div class="insert_button" :id="`bot_insert` + block.id" @click="open_add_menu($event, block.id); block_place = 1"></div>
        </div>
      </template>
    </draggable>
  </div>
  
</template>

<script>
  import draggable from 'vuedraggable';
  import { QuillEditor } from '@vueup/vue-quill'
  import 'quill-paste-smart';
  import { toRaw } from 'vue';

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
    data() {
      return {
        blocks: [
          {name:'Element 0', id: 0, type: "text"},
        ],
        options: {
          modules: {
            toolbar: ['bold', 'italic', 'underline', 'strike', { 'list': 'ordered'}, { 'list': 'bullet' }, 'link', 'clean' ],
          },
        },
        last_id: 1,
        scale: 0.5,
        timer: 0,
        current_image: -1,
        after_block: 0,
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
      this.blocks.forEach((block) => {
        let content = document.getElementById("block_element" + block.id)
        let element = document.getElementById("miniature" + block.id)
        let item = document.getElementById("miniature_item" + block.id)
        item.style.height = content.clientHeight * this.scale + "px";
        element.style.height = content.clientHeight * this.scale + "px";
      })
      document.getElementById("position").style.height = document.getElementById("worksheet").clientHeight * this.scale + "px"
    },
    methods: {
      add_element(type) {
        this.blocks.splice(this.blocks.map(function (img) { return img.id; }).indexOf(this.after_block) + this.block_place, 0, {name:'Element ' + this.last_id, id: this.last_id, type: type})
        if(type == 'carousel') {
          this.slidesarray[this.last_id] = structuredClone(this.slides);
        }
        this.last_id++
        document.getElementById("modal_menu").style.display = "none";
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
      on_update(id) {
        console.log(toRaw(this.myContent[id]))
      },
      scroll_to(id) {
        let content = document.getElementById("block_element" + id)
        content.scrollIntoView({ behavior: 'smooth' })
        setTimeout(function() { content.classList.toggle("blink"); }, 300)
        setTimeout(function() { content.classList.toggle("blink"); }, 800)
      },
      scroll_worker() {
        let pos = document.getElementById("position")
        pos.style.top = document.getElementById("worksheet").scrollTop * this.scale + "px"
       
        pos.style.visibility = "visible"
        if (this.timer == 0) {
          pos.classList.toggle("fade")
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
          setTimeout(function() { that.recursive_shutdown() }, 50);
          console.log(this.timer)
          return
        }
        let pos = document.getElementById("position")
        pos.classList.toggle("fade")
        setTimeout(function() { pos.style.visibility = "hidden"; }, 200)
      },
      expand(index) {
        console.log(index)
        let modal = document.getElementById("modal_image_insert");
        modal.style.display = "block";
        this.current_image = index;
      },
      collapse() {
        document.getElementById("modal_image_insert").style.display = "none";
      },
      image_title(index) {
        this.slidesarray[this.current_image][index].title = document.getElementById("img_title" + index).value;
      },
      delete_img(index) {
        if(this.slidesarray[this.current_image].length == 1) {
          alert("Должна быть хотя бы одна картинка");
          return;
        }
        this.slidesarray[this.current_image].splice(index, 1);
      },
      add_img() {
        this.slidesarray[this.current_image].push({
          title: '',
          image: document.getElementById("new_img").value
        })
        document.getElementById("new_img").value = "";
      },
      open_add_menu(e, after_id) {
        this.after_block = after_id;
        console.log(this.after_block)
        let modal = document.getElementById("modal_menu");
        modal.style.display = "block";
        modal.style.left = e.clientX + 'px';
        modal.style.top = e.clientY + 'px';
        console.log(e.pageX)
        modal.focus()
      },
      handle_focus_out() {
        let modal = document.getElementById("modal_menu");
        modal.style.display = "none";
      },
      show_menu_buttons(id) {
        if(!this.allow_menu){
          return;
        }
        document.getElementById("top_insert" + id).style.visibility = "visible";
        document.getElementById("bot_insert" + id).style.visibility = "visible";
      },
      hide_menu_buttons(id) {
        document.getElementById("top_insert" + id).style.visibility = "hidden";
        document.getElementById("bot_insert" + id).style.visibility = "hidden";
      }
    }
  }
  
</script>
