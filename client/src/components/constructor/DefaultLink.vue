<template>
<div class="default-link primary-rounded d-flex flex-column">
  <img class="image"
    :src="image"
  />
  <div class="d-flex flex-column text-block">
    <div class="link-text">{{ linkText }}</div>
    <div class="p2 text-color">{{ header }}</div>
    <div class="p3 text text-color">{{ text }}</div>
  </div>
</div>
</template>

<style scoped>
.default-link {
  width: 240px;
  border: 1px solid var(--text-secondary-color);
  gap: 7px;
  padding-bottom: 7px;
}
.image {
  max-width: 100%;
  max-height: 100%;
  vertical-align: middle;
}
.text-block {
  gap: 2px;
  padding-left: 7px;
  padding-right: 7px;
}
.text {
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}
</style>

<script>
export default {
  name: "DefaultLink",
  props: {
    image: {
      type: String,
      default: ""
    },
    linkText: {
      type: String,
      default: "",
    },
    header: {
      type: String,
      default: "",
    },
    text: {
      type: String,
      default: ""
    }
  }
}
</script>