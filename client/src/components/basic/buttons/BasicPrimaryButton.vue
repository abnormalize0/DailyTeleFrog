<template>
  <v-btn 
    class="button primary-first-color text-color primary-rounded p-button"
    height="44px"
  >
    {{content}}
  </v-btn>
</template>

<style scoped>
  .button {
    transition: 600ms;
  }
</style>

<script>
export default {
  name: "BasicPrimaryButton",
  props: {
    content: {
      type: String,
      default: "",
    },
  }
}
</script>