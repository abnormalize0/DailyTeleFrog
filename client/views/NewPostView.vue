<script setup>
import { nextTick, ref } from 'vue';
import { useMousePressed } from '@vueuse/core'
const renderComponent = ref(true);
const page_render = ref(true);
const { pressed } = useMousePressed()

let counter = 0;

    
    let blocks = [];
    let content = [];

    const sleep = (ms) => {
        return new Promise(resolve => setTimeout(resolve, ms))
    }

    async function display_reset() {
        renderComponent.value = false;
        page_render.value = false;
        await nextTick();
        renderComponent.value = true;
        page_render.value = true;
        await nextTick();
    }

    async function add_element(index) {
        blocks.splice(index, 0, counter);
        content.push("block" + counter);
        counter++;
        await display_reset();
    }

    async function block_shift(movable_block, index, new_index) {
        let temp = blocks[index];
        blocks[index] = blocks[new_index];
        blocks[new_index] = temp;
        let elem = document.getElementById("elem" + index );
        elem.id = "elem" + (new_index);
        movable_block.id = "elem" + index;
        await display_reset();
        elem = document.getElementById("elem" + blocks[new_index]);
        elem.classList.remove("element");
        elem.classList.add("element_hidden");
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
                await block_shift(upstairs_neighbor, index, index - 1);
                document.onmousemove = (e) => position(e, index - 1);
                event_setter = 1;

            }
        }

        if(index < blocks.length - 1) {
            let downstairs_neighbor = document.getElementById("elem" + blocks[index + 1]);
            if(float_element.getBoundingClientRect().top > downstairs_neighbor.getBoundingClientRect().top - 25) {
                await block_shift(downstairs_neighbor, index, index + 1);
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
        console.log("pass");
        console.log(index);
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
    
</script>

<template>
<div class="worksheet" id="worksheet" v-if="page_render">
    <div v-for="(block, index) in blocks" v-bind:key="index">
        <div @click="edit_content(block)" class="content" :id="`content` + block">{{ content[block]}}</div><br>
    </div>
</div>
<div class="right_menu" id="right_menu" v-if="renderComponent">
    <div @click="add_element(0)" class="add"></div>
    <div v-for="(block, index) in blocks" v-bind:key="index">
        <div @mousedown="hold_begin($event, index)" :class="`element`" :id="`elem` + blocks[index]">{{block}}</div>
        <div @click="add_element(index + 1)" :class="`add`"></div>
    </div>
</div>

</template>

<style>
.content {
    background-color: lightgray;
}
.worksheet {
    right: 300px;
    left: 300px;
    height: 100%;
    position: fixed;
    /* background-color: blue; */
}
.right_menu {
    height: 100%;
    width: 150px;
    position: fixed;
    right: 0;
    background-color: orangered;
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
}
</style>