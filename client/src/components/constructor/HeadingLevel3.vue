<template>
  <div class="h3 text-color">
    {{ content }}
  </div>
</template>

<script>
export default {
  name: "HeadingLevel3",
  props: {
    content: {
      type: String,
      default: "",
    }
  }
}
</script>