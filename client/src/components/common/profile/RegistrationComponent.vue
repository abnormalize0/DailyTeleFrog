<template>
	<!--Регистрация-->
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Регистрация</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput 
				class="form-input" 
				name="Email" 
				label="Email" 
				v-model="email" 
				@input="updateEmail($event.target.value)"
        :validators="this.emailValidators"
			/>
			<BasicInput 
				class="form-input" 
				name="Логин" 
				label="Логин" 
				v-model="username"
				@input="updateUsername($event.target.value)"
        :validators="this.loginValidators"
			/>
			<BasicInput 
				class="form-input" 
				name="Пароль" 
				label="Пароль" 
        type="password" 
				v-model="password" 
				@input="updatePassword($event.target.value)"
        :validators="this.passwordValidators"
			/>
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Создать аккаунт" @click="register()"></BasicPrimaryButton>
			</div>
			<div class="d-flex justify-center">
				<BasicSecondaryButton class="w-100" content="Назад" @click="TabService.changeTab(this, TabService.tabProfileTypes.Login)"></BasicSecondaryButton>
			</div>
		</div>
	</div>
</template>

<script>
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import BasicSecondaryButton from "@/components/basic/buttons/BasicSecondaryButton.vue";
import BasicInput from "@/components/basic/input/BasicInput.vue";
import { TabService } from "@/services";
import { required, sanitizeLogin, sanitizeEmail, sanitizePassword } from "@/utils/validators";

export default {
	name: "RegistrationComponent",
	components: { BasicPrimaryButton, BasicInput, BasicSecondaryButton},
	props: {
		groups: [],
	},
  emits: ["changeTab", "update:email", "update:username", "update:password"],
	data() {
		return {
			TabService,
			username: "",
			password: "",
			email: "",
    }
	},
  computed: {
    emailValidators() {
      return [required, sanitizeEmail];
    },
    loginValidators() {
      return [required, sanitizeLogin];
    },
    passwordValidators() {
      return [required, sanitizePassword];
    },
  },
	methods: {
		register() {
			const notGood = true;
			if (!notGood) {
				const registrationData = {
					email: this.email,
					username: this.username,
					password: this.password
				} 
				console.log(registrationData); // lint
				TabService.changeTab(this, TabService.tabProfileTypes.RegistrationSuccess);
			}
		},
		updateEmail(value) {
			this.$emit("update:email", value);
		},
		updateUsername(value) {
			this.$emit("update:username", value);
		},
		updatePassword(value) {
			this.$emit("update:password", value);
		}
	}
};
</script>
