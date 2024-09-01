<template>
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Регистрация прошла успешно</div>
		<div class="d-flex flex-column w-100 login-form">
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Войти в аккаунт" @click="this.$emit('changeTab', TabProfileTypes.Login)"></BasicPrimaryButton>
			</div>
		</div>
	</div>
</template>

<script>
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import { TabProfileTypes } from "@/components/common/profile/profile-tab";

export default {
	name: "RegistrationCompleteComponent",
	components: { BasicPrimaryButton },
	props: {
	},
	data() {
		return {
			TabProfileTypes,
		};
	},
	methods: {
	}
};
</script>
