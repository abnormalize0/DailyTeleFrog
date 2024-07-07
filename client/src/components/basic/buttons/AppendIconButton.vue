<template>
  <div class="d-flex btn pointer primary-rounded">
    <div class="p-button text-color text-uppercase">{{label}}</div>
    <i :class=icon></i>
  </div>
</template>

<style scoped>
.btn {
  justify-content: space-between;
  align-items: center;
  height: 46px;
  padding: 10px 10px 10px 15px;
}
.pointer {
  cursor: pointer;
}
.pointer:hover {
  background-color: #64648d;
}
</style>

<script>
export default {
  name: "LeftMenuButton",
  props: {
    label: {
      type: String,
      default: "",
    },
    icon: {
      type: String,
      default: "",
    },
  },
}
</script>