<template>
	<ProfileComponent />
</template>

<style scoped>

</style>

<script>
import ProfileComponent from './profile/ProfileComponent.vue';
import { AccountService } from "@/services";

export default {
	name: "RightMenuComponent",
	components: { ProfileComponent },
	props: {
	},
	data() {
		return {
			logedIn: false,
			username: "",
			password: "",
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
      
			const usernameSanitized = this.username.replace(/[!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]/g, "");
			const passwordSanitized = this.password.replace(/[!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]/g, "");
      AccountService.loginPost(usernameSanitized, passwordSanitized);
			
		},
		getDisplayString(type) {
			switch (type) {
				case 1: return this.avatarBlock.subscribers + " подписчиков";
				case 2: return "+ " + this.avatarBlock.rating + " рейтинга";
				case 3: return this.avatarBlock.patrons + " патронов";
				default: return;
			}
		}
	}
};
</script>
