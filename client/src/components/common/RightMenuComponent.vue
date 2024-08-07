<template>
	<ProfileComponent />
</template>

<style scoped>

</style>

<script>
import ProfileComponent from './profile/ProfileComponent.vue';

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

  }
};
</script>
