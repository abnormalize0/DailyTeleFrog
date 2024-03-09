<template>
  <div class="background-main-color">
    <HeaderComponent/>
  </div>
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