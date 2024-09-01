<template>
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Регистрация</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput 
				class="form-input" 
				name="Email" 
				label="Email" 
				v-model="email" 
        :validators="this.emailValidators"
        @error="validateEmail"
			/>
			<BasicInput 
				class="form-input" 
				name="Логин" 
				label="Логин" 
				v-model="username"
        :validators="this.loginValidators"
        @error="validateUsername"
			/>
			<BasicInput 
				class="form-input" 
				name="Пароль" 
				label="Пароль" 
        type="password" 
				v-model="password" 
        :validators="this.passwordValidators"
        @error="validatePassword"
			/>
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Создать аккаунт" @click="register()" :disabled="!registerFormValid"></BasicPrimaryButton>
			</div>
			<div class="d-flex justify-center">
				<BasicSecondaryButton class="w-100" content="Назад" @click="this.$emit('changeTab', TabProfileTypes.Login)"></BasicSecondaryButton>
			</div>
		</div>
	</div>
</template>

<script>
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import BasicSecondaryButton from "@/components/basic/buttons/BasicSecondaryButton.vue";
import BasicInput from "@/components/basic/input/BasicInput.vue";
import { required, sanitizeLogin, sanitizeEmail, sanitizePassword } from "@/utils/validators";
import { TabProfileTypes } from "@/components/common/profile/profile-tab";
import { UserService } from "@/services";

export default {
	name: "RegistrationComponent",
	components: { BasicPrimaryButton, BasicInput, BasicSecondaryButton},
	props: {
		groups: [],
	},
  emits: ["changeTab"],
	data() {
		return {
			TabProfileTypes,
			username: "",
			password: "",
			email: "",
      registerFormValid: true,
      registerForm: {
        email: true,
        username: true,
        password: true,
      }
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
		async register() {
			if (this.registerFormValid && this.username && this.email && this.password) {
        const result = await UserService.register(this.username, this.password, this.email);
				if (result) {
          this.$emit("changeTab", TabProfileTypes.RegistrationSuccess);
        }
			}
		},
    validateUsername(value) {
      this.registerForm.username = !value;
      this.registerFormValid = this.registerForm.username && this.registerForm.password && this.registerForm.email;
    },
    validatePassword(value) {
      this.registerForm.password = !value;
      this.registerFormValid = this.registerForm.username && this.registerForm.password && this.registerForm.email;
    },
    validateEmail(value) {
      this.registerForm.email = !value;
      this.registerFormValid = this.registerForm.username && this.registerForm.password && this.registerForm.email;
    }
	}
};
</script>
