<template>
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Войти</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput 
        class="form-input" 
        name="Логин" 
        label="Логин" 
        v-model="username" 
        @input="updateUsername($event.target.value)" 
      />
      <div class="d-flex flex-column password-section">
        <BasicInput 
          class="form-input" 
          name="Пароль" 
          label="Пароль" 
          type="password" 
          v-model="password" 
          @input="updatePassword($event.target.value)" 
        />
        <div class="d-flex text-mistake-color p2" v-if="displayWarning">
          Неправильный пароль. Попробуйте снова, пожалуйста. 
        </div>
        <div class="d-flex reset-password text-color p3" @click="TabService.changeTab(this, TabService.tabProfileTypes.ForgotPassword)">
          Забыли пароль?
        </div>
      </div>
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Войти" @click="login()"></BasicPrimaryButton>
			</div>
			<div class="d-flex justify-center">
				<BasicSecondaryButton class="w-100" content="Создать аккаунт" @click="TabService.changeTab(this ,TabService.tabProfileTypes.Register)"></BasicSecondaryButton>
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
import { TabService, UtilsService } from "@/services";
// import { AccountService,  } from "@/services";

export default {
	name: "LoginComponent",
	components: { BasicPrimaryButton, BasicInput, BasicSecondaryButton },
	props: {
		groups: [],
	},
    emits: ["changeTab"],
	data() {
		return {
            TabService,
			displayWarning: false,
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
		};
	},
	methods: {
		async login() {
			// const usernameSanitized = UtilsService.sanitize(this.username);
			// const passwordSanitized = UtilsService.sanitize(this.password);
			// const x = await AccountService.login(usernameSanitized, passwordSanitized);
			// console.log(x);
			let x = true;
			if (x) {
				
				UtilsService.highlightInputs(["Пароль"]);
				this.displayWarning = true;
			} else {
				TabService.changeTab(this, TabService.tabProfileTypes.LogedIn);
			}			
		},
		forgotPassword() {
			let notGood = false;
			if (notGood) {
				this.displayWarning = true;
			} else {
				TabService.changeTab(TabService.tabProfileTypes.RegistrationSuccess);
			}
		},
    updateUsername(value) {
      this.$emit("@update:username", value);
    },
    updatePassword(value) {
      this.$emit("@update:password", value);
    }
	}
};
</script>
