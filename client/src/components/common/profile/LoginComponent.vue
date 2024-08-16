<template>
	<!--Логин-->
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Войти</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput class="form-input" name="Логин" label="Логин" v-model="username" @update:modelValue="$event => (username = $event)" />
			<BasicInput class="form-input" name="Пароль" label="Пароль" type="password" v-model="password" @update:modelValue="$event => (password = $event)" />
			<div class="d-flex text-mistake-color p2" v-if="displayWarning">
				Неправильный пароль. Попробуйте снова, пожалуйста. 
			</div>
			<div class="d-flex reset-password text-color p2" @click="TabService.changeTab(this, TabService.tabProfileTypes.ForgotPassword)">
				Забыли пароль?
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
.wrap-menu {
	width: 267px;
	height: auto;
	padding: 20px;
	gap: 11px;
}

.login-form {
	gap: 15px;
}

.name-tag-wrap {
	margin-left: 12px;
}

.reset-password {
	text-decoration: underline;
}

.reset-password:hover {
	cursor: pointer;
}
</style>

<script>
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import BasicSecondaryButton from "@/components/basic/buttons/BasicSecondaryButton.vue";
import BasicInput from "@/components/basic/input/BasicInput.vue";
import { TabService } from "@/services";
//import { AccountService } from "@/services";

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
//			const usernameSanitized = this.sanitize(this.username);
//			const passwordSanitized = this.sanitize(this.password);
			//const x = await AccountService.login(usernameSanitized, passwordSanitized);
			//console.log(x);
			let x = true;
			if (x) {
				let inputs = document.getElementsByClassName("form-input");
				this.highlightInputs(inputs, ["Пароль"]);
				this.displayWarning = true;
			} else {
				TabService.changeTab(this, TabService.tabProfileTypes.LogedIn);
			}			
		},
		sanitize(data) {
			return data.replace(/[!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]/g, "").replace(/\s/g, "");
		},
		highlightInputs(inputsArray, namesToHighlight) {
			for (let i = 0; i < inputsArray.length; i++) {
					if (namesToHighlight.indexOf(inputsArray[i].attributes["name"].value) != -1) {
						inputsArray[i].style.border = "1px solid #C90C00"; // в идеале сделать классом и пушить/попать
					}
				}
		},
		forgotPassword() {
			let notGood = false;
			if (notGood) {
				this.displayWarning = true;
			} else {
				TabService.changeTab(TabService.tabProfileTypes.RegistrationSuccess);
			}
		}
	}
};
</script>
