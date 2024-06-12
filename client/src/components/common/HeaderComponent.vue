<template>
  <v-container class="header">
    <v-row class="justify-center">
      <v-col cols="3" class="d-flex align-center">
        <div>
          <img src="../../assets/Logo.png" alt="Logo" />
          <div class="absolute">
            <LeftMenuComponent :groups="groups" />
          </div>
        </div>
      </v-col>
      <v-col cols="6" class="d-flex justify-center">
        <SearchBar />
      </v-col>
      <v-col cols="3" class="text-right">
        <div>
          <BasicPrimaryButton content="Войти" class="button-position" />
          <div class="right-menu-container">
            <div class="absolute">
              <RightMenuComponent />
            </div>
          </div>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.header {
  height: 72px;
}
.right-menu-container {
  width: 100%;
  display: flex;
  justify-content: right;
}
.enter-container {
  justify-content: right;
}
.absolute {
  position: absolute;
}
</style>

<script>
import BasicPrimaryButton from "@/components/basic/BasicPrimaryButton.vue";
import SearchBar from "@/components/basic/SearchBar.vue";
import LeftMenuComponent from "./LeftMenuComponent.vue";
import RightMenuComponent from "./right-menu/RightMenuComponent.vue";

export default {
  name: "HeaderComponent",
  components: {
    BasicPrimaryButton,
    SearchBar,
    LeftMenuComponent,
    RightMenuComponent,
  },
  data() {
    return {
      groups: [
        {
          name: "onanisti",
          img: "https://cdn2.iconfinder.com/data/icons/people-groups/512/Leader_Avatar-512.png",
        },
        {
          name: "dungeonSlaveZ",
          img: "https://cdn2.iconfinder.com/data/icons/people-groups/512/Leader_Avatar-512.png",
        },
        {
          name: "boyNextDoor",
          img: "https://cdn2.iconfinder.com/data/icons/people-groups/512/Leader_Avatar-512.png",
        },
        {
          name: "Jhohan pohan",
          img: "https://cdn2.iconfinder.com/data/icons/people-groups/512/Leader_Avatar-512.png",
        },
        {
          name: "tester mokaka",
          img: "https://cdn2.iconfinder.com/data/icons/people-groups/512/Leader_Avatar-512.png",
        },
      ],
    };
  },
};
</script>
