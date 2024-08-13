<template>
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Забыли пароль?</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput class="form-input" name="Email" label="Email" :modelValue="email" @update:modelValue="$event => (email = $event)" />
			<div class="d-flex text-mistake-color p2" v-if="displayWarning">
				Такой Email не зарегистрирован.
			</div>
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Восстановить пароль" @click="forgotPassword()"></BasicPrimaryButton>
			</div>
			<div class="d-flex justify-center">
				<BasicSecondaryButton class="w-100" content="Назад" @click="TabService.changeTab(this, TabService.tabProfileTypes.Login)"></BasicSecondaryButton>
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
</style>

<script>
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import BasicSecondaryButton from "@/components/basic/buttons/BasicSecondaryButton.vue";
import BasicInput from "@/components/basic/input/BasicInput.vue";
import { TabService } from "@/services";

export default {
	name: "ProfileComponent",
	components: { BasicPrimaryButton, BasicInput, BasicSecondaryButton, },
	props: {
		groups: [],
	},
	data() {
		return {
			TabService,
			displayWarning: false,
			email: "",
		};
	},
	methods: {
		forgotPassword() {
			let notGood = true;
			if (notGood) {let inputs = document.getElementsByClassName("form-input");
            this.highlightInputs(inputs, ["Email"]);
				this.displayWarning = true;
			} else {
				TabService.changeTab(this, TabService.tabProfileTypes.RegistrationSuccess);
			}
		},
        highlightInputs(inputsArray, namesToHighlight) {
			for (let i = 0; i < inputsArray.length; i++) {
					if (namesToHighlight.indexOf(inputsArray[i].attributes["name"].value) != -1) {
						inputsArray[i].style.border = "1px solid #C90C00"; // в идеале сделать классом и пушить/попать
					}
				}
		},
	}
};
</script>
