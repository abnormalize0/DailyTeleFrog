<script setup>
    import { nextTick, ref } from 'vue';
    import { useMousePressed } from '@vueuse/core'
    const dummy_ref = ref(true);
    const insert_menu_ref = ref(false);
    const { pressed } = useMousePressed()

    let counter = 0;

    
    let blocks = [];
    let content = [];
    let block_type = [];

    let types_list = ["Подзаголовок", "Текст", "Изображение"];

    const sleep = (ms) => {
        return new Promise(resolve => setTimeout(resolve, ms))
    }

    async function display_reset() {
        dummy_ref.value = false;
        await nextTick();
        dummy_ref.value = true;
        await nextTick();
    }

    let current_index = 0;

    async function open_insert_menu(e, index) {
        current_index = index;
        insert_menu_ref.value = true;
        await nextTick();

        let insert_menu = document.getElementById("insert_menu");
        insert_menu.style.top = e.clientY - 40 + "px";
        insert_menu.style.left = e.clientX - 190 + "px";
        insert_menu.onmouseleave  = function() {console.log("aaa"); insert_menu_ref.value = false;};
    }

    // function close_insert_menu() {
    //     insert_menu.value = false;
    // }

    async function add_element(index) {
        blocks.splice(current_index, 0, counter);
        content.push(types_list[index] + counter);
        block_type.push(index);
        counter++;
        insert_menu_ref.value = false;
        await display_reset();
    }

    async function block_shift(index, new_index) {
        let temp = blocks[index];
        blocks[index] = blocks[new_index];
        blocks[new_index] = temp;
        
        let elem = document.getElementById("elem" + blocks[index]);
        for(let i = 0; i < counter; i++) {
            console.log("elem" + i);
            let tmp_elem = document.getElementById("elem" + i);
            if(tmp_elem.classList.contains("element_hidden")) {
                tmp_elem.classList.remove("element_hidden");
                tmp_elem.classList.add("element");
            }
        }
        elem.classList.remove("element");
        elem.classList.add("element_hidden");

        await display_reset();
    }

    let posx = -1;
    let posy = -1;

    function hold_begin(e, index) {
        let elem = document.getElementById("elem" + blocks[index]);
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
            let upstairs_neighbor = document.getElementById("elem" + blocks[index - 1]);
            if(float_element.getBoundingClientRect().top < upstairs_neighbor.getBoundingClientRect().top + 25) { //захардкодил размеры блоков пока что
                await block_shift(index, index - 1);
                document.onmousemove = (e) => position(e, index - 1);
                event_setter = 1;

            }
        }

        if(index < blocks.length - 1) {
            let downstairs_neighbor = document.getElementById("elem" + blocks[index + 1]);
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
            let elem = document.getElementById("elem" + blocks[index]);
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
        await display_reset();
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
            console.log("out of " + index);
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

        // target.innerHTML = "<input id='active_input' type='file'>";
        target.innerHTML = "<img id='img" + index + "' width='600' src='" + content[index] + "'><input class='image_loader' id='active_input' type='file'>";
        let input = document.getElementById("active_input");
        input.click();                                          //сделать удаленное окно на которое будет нажиматься автоматически
        input.addEventListener("change", () => {
            console.log("changed");
            const FR = new FileReader();
            FR.onload = (e) => {
                // this.product.image = event.target.result;
                console.log("loaded");
                target.innerHTML = "<img id='img" + index + "' width='600'>";
                document.querySelector("#img" + index).src = e.target.result;
                content[index] = e.target.result;
                allow_edit = 1;
            }
            FR.readAsDataURL(input.files[0]);
        })
    }
    
</script>

<template>
<div class="worksheet" id="worksheet">
    <div v-for="(block, index) in blocks" v-bind:key="index">
        <div v-if="block_type[block] == 0" @click="edit_content(block)" class="content_header" :id="`content` + block">{{ content[block]}}</div>
        <div v-if="block_type[block] == 1" @click="edit_content(block)" class="content_text" :id="`content` + block">{{ content[block]}}</div>
        <!-- <div v-if="block_type[block] == 2" @click="edit_image(block)" class="content_text" :id="`content` + block">{{ content[block]}}</div> -->
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

<div v-if="dummy_ref"></div>
</template>

<style>
.image_loader {
    opacity: 0;
    position: fixed;
}
.content_header {
    background-color: lightgray;
    font-size: 36px;
    font-weight: bold;
}
.content_text {
    background-color: lightgray;
    font-size: 18px;
}
.worksheet {
    right: 300px;
    left: 300px;
    height: 80%;
    position: fixed;
    overflow-y: scroll;
}
.insert_menu {
    height: 80px;
    width: 200px;
    position: fixed;
    top: 0px;
    left: 0px;
    background-color: lightpink;
}
.insert_menu_element{
    height: 25px;
    margin-bottom: 3px;
    background-color: red;
    text-align: center;
    vertical-align: middle;
    line-height: 25px;       /* The same as your div height */
    border-radius: 25px;
}
.insert_menu_element:hover{
    background-color: lightcoral;
}
.right_menu {
    height: 100%;
    width: 150px;
    position: fixed;
    right: 0;
    overflow-y: scroll;
}
.add {
    width: 100%;
    height: 20px;
    background-color: turquoise;
    position: relative;
}
.element {
    width: 100%;
    height: 50px;
    background-color: darkcyan;
    position: relative;

    text-align: center;
    font-family: "Times New Roman", Times, serif;
}
.element_hidden {
    width: 100%;
    height: 50px;
    background-color: transparent;
    color: transparent;
    position: relative;
}
.element_float {
    width: 150px;
    height: 50px;
    background-color: darkcyan;
    position: absolute;

    text-align: center;
    font-family: "Times New Roman", Times, serif;
}
* {
  -webkit-user-select: none; /* Safari */
  -ms-user-select: none; /* IE 10 and IE 11 */
  user-select: none; /* Standard syntax */
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}

*::-webkit-scrollbar {
  display: none;
}
</style>