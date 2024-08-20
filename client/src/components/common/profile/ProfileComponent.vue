<template>
	<LoginComponent @changeTab="onTabChange($event)"
	v-if="tabType == TabService.tabProfileTypes.Login" />
	<LogedInComponent
	v-if="tabType == TabService.tabProfileTypes.LogedIn" />
	<RegistrationComponent @changeTab="onTabChange($event)" 
	v-if="tabType == TabService.tabProfileTypes.Register" />
	<ForgotPasswordComponent @changeTab="onTabChange($event)"
	v-if="tabType == TabService.tabProfileTypes.ForgotPassword" />
	<RegistrationCompleteComponent @changeTab="onTabChange($event)"
	v-if="tabType == TabService.tabProfileTypes.RegistrationSuccess" />
</template>

<style>
.not-good-input{
	border: 1px solid #C90C00;
}
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
import LogedInComponent from "./LogedInComponent.vue";
import RegistrationComponent from "./RegistrationComponent.vue";
import ForgotPasswordComponent from "./ForgotPasswordComponent.vue";
import RegistrationCompleteComponent from "./RegistrationCompleteComponent.vue";
import { TabService } from "@/services";

export default {
	name: "ProfileComponent",
	components: { LoginComponent, LogedInComponent, RegistrationComponent, RegistrationCompleteComponent, ForgotPasswordComponent },
	props: {
		groups: [],
	},
	data() {
		return {
			tabType: 0,
			TabService,
		};
	},
	methods: {
		onTabChange(tabNumber) {
			this.tabType = tabNumber;
		}
	}
};
</script>
