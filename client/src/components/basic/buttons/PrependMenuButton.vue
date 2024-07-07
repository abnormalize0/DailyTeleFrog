<template>
  <div class="d-flex btn pointer primary-rounded">
    <i :class=icon></i>
    <div class="p2 text-color">{{label}}</div>
  </div>
</template>

<style scoped>
.btn {
  justify-content: left;
  align-items: center;
  height: 46px;
  padding: 10px 10px 10px 15px;
  gap: 10px;
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