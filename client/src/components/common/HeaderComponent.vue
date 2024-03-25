<template>
  <v-container class="header">
    <v-row class="justify-center align-center">
      <v-col cols="3" class="d-flex align-center">
        <img src="../../assets/Logo.png" alt="Logo" />
      </v-col>
      <v-col cols="6" class="d-flex justify-center align-center">
        <SearchBar/>
      </v-col>
      <v-col cols="3" class="text-right">
        <BasicPrimaryButton content="Войти" class="button-position"/>
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
import BasicPrimaryButton from '../basic/BasicPrimaryButton.vue';
import SearchBar from '../basic/SearchBar.vue';

export default {
  name: "HeaderComponent",
  components: {
    BasicPrimaryButton,
    SearchBar
  }
}
</script>