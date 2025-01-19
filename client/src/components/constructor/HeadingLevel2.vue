<template>
  <div class="h2 text-color">
    {{ content }}
  </div>
</template>

<script>
export default {
  name: "HeadingLevel2",
  props: {
    content: {
      type: String,
      default: "",
    }
  }
}
</script>