<template>
	<!--Логин-->
	<LoginComponent @changeTab="onTabChange($event)"
	v-if="tabType == TabService.tabProfileTypes.Login" />
	<!--Вид залогиненного пользователя-->
	<LogedInComponent
	v-if="tabType == TabService.tabProfileTypes.LogedIn" />
	<!--Регистрация-->
	<RegistrationComponent @changeTab="onTabChange($event)" 
	v-if="tabType == TabService.tabProfileTypes.Register" />
	<!--Забыли пароль-->
	<ForgotPasswordComponent @changeTab="onTabChange($event)"
	v-if="tabType == TabService.tabProfileTypes.ForgotPassword" />
	<!--Регистрация прошла успешно-->
	<RegistrationCompleteComponent @changeTab="onTabChange($event)"
	v-if="tabType == TabService.tabProfileTypes.RegistrationSuccess" />
</template>

<style scoped>
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
