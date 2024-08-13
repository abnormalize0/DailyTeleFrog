<template>
	<!--Регистрация прошла успешно-->
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Регистрация прошла успешно</div>
		<div class="d-flex flex-column w-100 login-form">
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Войти в аккаунт" @click="TabService.changeTab(this, TabService.tabProfileTypes.Login)"></BasicPrimaryButton>
			</div>
		</div>
	</div>
</template>

<style scoped>
.wrap-menu {
	width: 267px;
	height: auto;
	padding: 20px;
	gap: 11px;
}

.login-form {
	gap: 15px;
}
</style>

<script>
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import { TabService } from "@/services";

export default {
	name: "RegistrationCompleteComponent",
	components: { BasicPrimaryButton },
	props: {
	},
    emits: ["changeTab"],
	data() {
		return {
			TabService,
		};
	},
	methods: {
	}
};
</script>
