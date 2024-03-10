<template>
  <v-app class="background-main-color">
    <HeaderComponent/>
  </v-app>
</template>

<style>
  @import '../public/css/styles.css';
</style>

<script>
  import HeaderComponent from "@/components/common/HeaderComponent.vue";

  export default {
    name: "MVP",
    components: {
      HeaderComponent
    }
  }
</script>