<template>
  <div class="d-flex input-field text-color primary-border primary-rounded">
    <input class="input-text-box" placeholder=" "/>
    <label class="floating-label p2 text-secondary-color">{{label}}</label>
  </div>
</template>

<style scoped>
.input-field {
  height: 50px !important;
  width: 100% !important;
  padding: 10px 15px;
  background-color: transparent;
  caret-color: var(--text-secondary-color);
  transition: 600ms;
  position: relative;
}

.input-field:hover,
.input-field:focus-within,
.input-field:active {
  background-color: var(--background-secondary-color);
}

.input-field::-webkit-input-placeholder,
.input-field:-ms-input-placeholder,
.input-field:-moz-placeholder,
.input-field::-moz-placeholder {
  font-family: var(--family-name);
  font-size: 14px !important;
  letter-spacing: 0 !important;
  color: var(--text-secondary-color);
}

.input-text-box {
  width: 100%;
  outline: 0;
  color: var(--text-secondary-color);
}

.floating-label {
  position: absolute;
  pointer-events: none;
  align-self: center;
  transition: 0.2s;
  color: var(--text-secondary-color);
}

.input-field .input-text-box:focus+.floating-label,
.input-field .input-text-box:not(:placeholder-shown)+.floating-label {
  top: 5px;
  -webkit-transform: scale(0.71) translateY(-10%) translateX(-10px);
  transform: scale(0.71) translateY(-10%) translateX(-10px);
}

.input-field .input-text-box:focus,
.input-field .input-text-box:not(:placeholder-shown) {
  padding-top: 10px;
}

.input-field .input-text-box,
.input-field .floating-label {
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
  -webkit-transition: all 0.5s;
  transition: all 0.5s;
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
    }
  }
}
</script>