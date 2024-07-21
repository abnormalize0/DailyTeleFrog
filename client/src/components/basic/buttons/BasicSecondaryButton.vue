<template>
    <v-btn 
      variant="outlined"
      class="button text-secondary-color primary-rounded p-button"
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
    name: "BasicSecondaryButton",
    props: {
      content: {
        type: String,
        default: "",
      },
    }
  }
  </script>