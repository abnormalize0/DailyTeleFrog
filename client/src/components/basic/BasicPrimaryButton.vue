<template>
  <v-btn 
    class="primary-first-color text-color primary-rounded"
    height="44px"
  >
    {{content}}
  </v-btn>
</template>

<script>
  export default {
    name: "BasicPrimaryButton",
    props: {
      content: {
        type: String,
        default: "",
      }
    }
  }
</script>