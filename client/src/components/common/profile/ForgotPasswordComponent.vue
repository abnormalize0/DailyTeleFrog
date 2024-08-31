<template>
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Забыли пароль?</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput 
        class="form-input" 
        name="Email" 
        label="Email" 
        v-model="email"
        @input="updateEmail($event.target.value)"
        :validators="this.emailValidators"
      />
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Восстановить пароль" @click="forgotPassword()"></BasicPrimaryButton>
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
import { required, sanitizeEmail } from "@/utils/validators";

export default {
	name: "ProfileComponent",
	components: { BasicPrimaryButton, BasicInput, BasicSecondaryButton, },
	props: {
		groups: [],
	},
	data() {
		return {
			TabService,
			email: "",
		};
	},
	emits: ["update:email"],
  computed: {
    emailValidators() {
      return [required, sanitizeEmail];
    }
  },
	methods: {
		forgotPassword() {
			let notGood = true;
			if (!notGood) {
				TabService.changeTab(this, TabService.tabProfileTypes.RegistrationSuccess);
			}
		},
    updateEmail(value) {
      this.$emit("update:email", value);
    }
	}
};
</script>
