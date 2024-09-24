<template>
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Войти</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput 
        class="form-input" 
        name="Логин" 
        label="Логин" 
        v-model="username" 
        :validators="this.loginValidators"
        @error="validateUsername"
      />
      <div class="d-flex flex-column password-section">
        <BasicInput 
          class="form-input" 
          name="Пароль" 
          label="Пароль" 
          type="password" 
          v-model="password" 
          :validators="this.passwordValidators"
          @error="validatePassword"
        />
        <div class="d-flex reset-password text-color p3" @click="this.$emit('changeTab', TabProfileTypes.ForgotPassword)">
          Забыли пароль?
        </div>
      </div>
			<div class="d-flex justify-center">
				<BasicPrimaryButton 
          class="w-100" 
          content="Войти" 
          :disabled="!loginFormValid"
          @click="login()">
        </BasicPrimaryButton>
			</div>
			<div class="d-flex justify-center">
				<BasicSecondaryButton class="w-100" content="Создать аккаунт" @click="this.$emit('changeTab', TabProfileTypes.Register)"></BasicSecondaryButton>
			</div>
		</div>
	</div>
</template>

<style scoped>
.password-section {
  gap: 8px;
}

.name-tag-wrap {
	margin-left: 12px;
}

.reset-password {
	text-decoration: underline;
  transition: color 600ms;
}

.reset-password:hover {
	cursor: pointer;
  color: var(--text-color-hover) !important;
}
</style>

<script>
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import BasicSecondaryButton from "@/components/basic/buttons/BasicSecondaryButton.vue";
import BasicInput from "@/components/basic/input/BasicInput.vue";
import { UserService } from "@/services";
import { NOT_FILLED_FIELDS_MESSAGE, WRONGLY_FILLED_FIELDS_MESSAGE} from "@/utils/messages";
import { required, sanitizeLogin, sanitizePassword } from "@/utils/validators";
import { TabProfileTypes } from "@/components/common/profile/profile-tab";
import { showToast } from "@/utils/toast";

export default {
	name: "LoginComponent",
	components: { BasicPrimaryButton, BasicInput, BasicSecondaryButton },
  emits: ["changeTab"],
	data() {
		return {
			username: "",
			password: "",
			email: "",
			avatarBlock: {
				avatarImgSrc: "../../../assets/Avatar.png",
				subscribers: 30,
				rating: 2000,
				patrons: 2,
				profileName: "koks",
				profileTag: "@keks",
			},
      loginFormValid: true,
      loginForm: {
        username: true,
        password: true,
      },
      TabProfileTypes
		};
	},
  computed: {
    loginValidators() {
      return [required, sanitizeLogin];
    },
    passwordValidators() {
      return [required, sanitizePassword];
    }
  },
	methods: {
    async login() {
      if (this.loginFormValid && this.username && this.password) {
        const result = await UserService.login(this.username, this.password);
        if (result) {
          localStorage.setItem('auth_token', result.auth_token);
          this.$emit("changeTab", TabProfileTypes.LoggedIn);
        }
      } else if (!this.loginFormValid) {
        showToast(WRONGLY_FILLED_FIELDS_MESSAGE, { type: 'error', autoClose: 5000});
      } else {
        showToast(NOT_FILLED_FIELDS_MESSAGE, { type: 'error' });
      }
		},
    validateUsername(value) {
      this.loginForm.username = !value;
      this.loginFormValid = this.loginForm.username && this.loginForm.password;
    },
    validatePassword(value) {
      this.loginForm.password = !value;
      this.loginFormValid = this.loginForm.username && this.loginForm.password;
    }
	}
};
</script>
