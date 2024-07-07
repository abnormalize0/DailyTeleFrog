<template>
  <v-app class="background-main-color">
    <HeaderComponent />
    <MainView/>
  </v-app>
</template>

<style>
@import "../public/css/styles.css";
</style>

<script>
import HeaderComponent from "@/components/common/HeaderComponent.vue";
import MainView from "@/views/MainView.vue";

export default {
  name: "MVP",
  components: {
    HeaderComponent,
    MainView,
  }
};
</script>
