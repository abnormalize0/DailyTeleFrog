<template>
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
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
</template>

<style scoped>
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
</style>

<script>
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";

export default {
	name: "LogedInComponent",
	components: { BasicPrimaryButton, },
	props: {
		groups: [],
	},
    data() {
		return {
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
        getDisplayString(type) {
			switch (type) {
				case 1: return this.avatarBlock.subscribers + " подписчиков";
				case 2: return "+ " + this.avatarBlock.rating + " рейтинга";
				case 3: return this.avatarBlock.patrons + " патронов";
				default: return;
			}
		},
	},
}
</script>
