<template>
  <v-container class="header">
    <v-row class="justify-center">
      <v-col cols="3" class="d-flex align-center">
        <img src="../../assets/Logo.png" alt="Logo" />
      </v-col>
      <v-col cols="6" class="d-flex justify-center">
        <SearchBar />
      </v-col>
      <v-col cols="3" class="text-right">
        <BasicPrimaryButton content="Войти" />
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.header {
  height: 72px;
}
</style>

<script>
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import SearchBar from "@/components/basic/SearchBar.vue";

export default {
  name: "HeaderComponent",
  components: {
    BasicPrimaryButton,
    SearchBar,
  }
};
</script>
