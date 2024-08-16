<template>
  <div class="d-flex input-field primary-border primary-rounded">
    <input 
      class="input-text-box" 
      v-model="modelValue"
      @input="updateModelValue($event.target.value)"
      :type="type"
      placeholder=" "
    />
    <label class="floating-label p2 text-secondary-color">{{label}}</label>
  </div>
</template>

<style scoped>
.input-field {
  display: flex;
  height: 50px !important;
  width: 100% !important;
  padding: 10px 15px;
  background-color: transparent;
  caret-color: var(--text-secondary-color) !important;
  transition: 600ms;
  position: relative;
  justify-content: center;
  align-items: center;
}

.input-field:hover,
.input-field:focus-within,
.input-field:active {
  background-color: var(--background-secondary-color);
}

.input-field .floating-label {
  position: absolute;
  left: 15px;
  pointer-events: none;
}

.input-field:focus-within .floating-label, 
.input-field:active .floating-label {
  position: absolute;
  font-size: 10px !important;
  line-height: 11.6px !important;
  margin-bottom: 2px;
  top: 10px;
}

.input-text-box:not(:focus):not(:placeholder-shown) + .floating-label {
  display: none;
}

.input-text-box {
  width: 100%;
  outline: 0;
  color: var(--text-secondary-color);
}

.input-field .input-text-box:focus {
  padding-top: 14px;
}

.input-field .input-text-box,
.input-field .floating-label {
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
  -webkit-transition: all 0.3s;
  transition: all 0.3s;
  -webkit-transition-timing-function: cubic-bezier(0.25, 0.1, 0.25, 1);
  transition-timing-function: cubic-bezier(0.25, 0.1, 0.25, 1);
}
</style>

<script>
export default {
  name: "BasicInput",
  props: {
    label: {
      type: String,
      default: "",
    },
    type: {
      type: String,
      default: "text"
    }
  },
  data() {
    return {
      modelValue: ""
    }
  },
  methods: {
    updateModelValue(value) {
      this.$emit("update:modelValue", value);
    }
  }
}
</script>
