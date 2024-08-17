<template>
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Регистрация прошла успешно</div>
		<div class="d-flex flex-column w-100 login-form">
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Войти в аккаунт" @click="TabService.changeTab(this, TabService.tabProfileTypes.Login)"></BasicPrimaryButton>
			</div>
		</div>
	</div>
</template>

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
