<template>
  <LoginComponent @changeTab="onTabChange($event)"
    v-if="tabType === TabProfileTypes.Login" />
  <LoggedInComponent
    v-if="tabType === TabProfileTypes.LoggedIn" />
  <RegistrationComponent @changeTab="onTabChange($event)" 
    v-if="tabType === TabProfileTypes.Register" />
  <ForgotPasswordComponent @changeTab="onTabChange($event)"
    v-if="tabType === TabProfileTypes.ForgotPassword" />
  <RegistrationCompleteComponent @changeTab="onTabChange($event)"
    v-if="tabType === TabProfileTypes.RegistrationSuccess" />
</template>

<style>
.login-form {
	gap: 15px;
}
.wrap-menu {
	width: 267px;
	height: auto;
	padding: 20px;
	gap: 11px;
}
</style>

<script>
import LoginComponent from "./LoginComponent.vue";
import LoggedInComponent from "./LoggedInComponent.vue";
import RegistrationComponent from "./RegistrationComponent.vue";
import ForgotPasswordComponent from "./ForgotPasswordComponent.vue";
import RegistrationCompleteComponent from "./RegistrationCompleteComponent.vue";
import { TabProfileTypes } from "@/components/common/profile/profile-tab";

export default {
	name: "ProfileComponent",
	components: { LoginComponent, LoggedInComponent, RegistrationComponent, RegistrationCompleteComponent, ForgotPasswordComponent },
	props: {
		groups: [],
	},
	data() {
		return {
			tabType: 0,
      TabProfileTypes,
		};
	},
	methods: {
		onTabChange(tabNumber) {
			this.tabType = tabNumber;
		}
	}
};
</script>
