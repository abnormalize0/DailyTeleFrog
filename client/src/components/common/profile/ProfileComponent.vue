<template>
	<!--Логин-->
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu" 
	v-if="tabType == tabProfileTypes.Login">
		<div class="h2 text-color">Войти</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput label="Логин" :modelValue="username" @update:modelValue="$event => (username = $event)" />
			<BasicInput label="Пароль" :modelValue="password" @update:modelValue="$event => (password = $event)" />
			<div class="d-flex reset-password text-color p2" @click="changeTab(tabProfileTypes.ForgotPassword)">
				Забыли пароль?
			</div>
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Войти" @click="login()"></BasicPrimaryButton>
			</div>
			<div class="d-flex justify-center">
				<BasicSecondaryButton class="w-100" content="Создать аккаунт" @click="changeTab(tabProfileTypes.Register)"></BasicSecondaryButton>
			</div>
		</div>
	</div>
	<!--Вид залогиненного пользователя-->
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu" 
    v-if="tabType == tabProfileTypes.LogedIn">
		<div class="d-flex profile-wrap text-color">
			<div class="d-flex">
				<img src="../../../assets/Avatar.png">
				<div class="name-tag-wrap">
					{{ avatarBlock.profileName }}
					<div>
						{{ avatarBlock.profileTag }}
					</div>
				</div>
			</div>
			<div class="d-flex">
				<i class="settings-icon" style="margin-right: 8px" />
				<i class="exit-icon" />
			</div>
		</div>
		<div class="d-flex flex-column w-100 counters">
			<div v-for="i in 3" class="text-color" :key="i">
				{{ getDisplayString(i) }}
			</div>
		</div>
		<BasicPrimaryButton class="w-100" content="Опубликовать пост"></BasicPrimaryButton>
	</div>
	<!--Регистрация-->
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu" 
	v-if="tabType == tabProfileTypes.Register">
		<div class="h2 text-color">Регистрация</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput label="Email" :modelValue="email" @update:modelValue="$event => (email = $event)" />
			<BasicInput label="Логин" :modelValue="username" @update:modelValue="$event => (username = $event)" />
			<BasicInput label="Пароль" :modelValue="password" @update:modelValue="$event => (password = $event)" />
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Создать аккаунт" @click="login()"></BasicPrimaryButton>
			</div>
			<div class="d-flex justify-center">
				<BasicSecondaryButton class="w-100" content="Назад" @click="changeTab(tabProfileTypes.Login)"></BasicSecondaryButton>
			</div>
		</div>
	</div>
	<!--Забыли пароль-->
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu" 
	v-if="tabType == tabProfileTypes.ForgotPassword">
		<div class="h2 text-color">Забыли пароль?</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput label="Email" :modelValue="email" @update:modelValue="$event => (email = $event)" />
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Восстановить пароль" @click="login()"></BasicPrimaryButton>
			</div>
			<div class="d-flex justify-center">
				<BasicSecondaryButton class="w-100" content="Назад" @click="changeTab(tabProfileTypes.Login)"></BasicSecondaryButton>
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

.profile-wrap {
	width: 100%;
	justify-content: space-between;
	align-items: center;
}

.counters {
	margin: 24px 0 32px;
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
import { AccountService } from "@/services";

export default {
	name: "ProfileComponent",
	components: { BasicPrimaryButton, BasicInput, BasicSecondaryButton },
	props: {
		groups: [],
	},
	data() {
		return {
			logedIn: false,
			tabType: 0,
			tabProfileTypes: {
				LogedIn: 3,
				Login: 0,
				Register: 1,
				ForgotPassword: 2,
			},	
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
			const usernameSanitized = this.sanitize(this.username);
			const passwordSanitized = this.sanitize(this.password);
			const x = await AccountService.login(usernameSanitized, passwordSanitized);
			console.log(x);
			this.logedIn = true;
			
		},
		changeTab(tabNumber) {
			this.clearData();
			this.tabType = tabNumber;
		},
		register() {
			this.registering = true;
		},
		getDisplayString(type) {
			switch (type) {
				case 1: return this.avatarBlock.subscribers + " подписчиков";
				case 2: return "+ " + this.avatarBlock.rating + " рейтинга";
				case 3: return this.avatarBlock.patrons + " патронов";
				default: return;
			}
		},
		clearData() {
			this.username = "";
			this.password = "";
			this.email = "";			
		},
		sanitize(data) {
			return data.replace(/[!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]/g, "").replace(/\s/g, "");
		}
	}
};
</script>
