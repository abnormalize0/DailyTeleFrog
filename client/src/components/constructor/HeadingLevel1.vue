<template>
  <div class="h1 text-color">
    {{ content }}
  </div>
</template>

<script>
export default {
  name: "HeadingLevel1",
  props: {
    content: {
      type: String,
      default: "",
    }
  }
}
</script>