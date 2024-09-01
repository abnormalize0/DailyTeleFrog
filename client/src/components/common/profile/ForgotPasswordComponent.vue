<template>
	<div class="d-flex flex-column primary-rounded background-secondary-color align-center wrap-menu">
		<div class="h2 text-color">Забыли пароль?</div>
		<div class="d-flex flex-column w-100 login-form">
			<BasicInput 
        class="form-input" 
        name="Email" 
        label="Email" 
        v-model="email"
        :validators="this.emailValidators"
        @error="validateForm"
      />
			<div class="d-flex justify-center">
				<BasicPrimaryButton class="w-100" content="Восстановить пароль" :disabled="!forgotPasswordFormValid" @click="forgotPassword()"></BasicPrimaryButton>
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
import { required, sanitizeEmail } from "@/utils/validators";
import { TabProfileTypes } from "@/components/common/profile/profile-tab";
import { UserService } from "@/services";

export default {
	name: "ProfileComponent",
	components: { BasicPrimaryButton, BasicInput, BasicSecondaryButton, },
	props: {
		groups: [],
	},
	data() {
		return {
			TabProfileTypes,
			email: "",
      forgotPasswordFormValid: true,
		};
	},
  computed: {
    emailValidators() {
      return [required, sanitizeEmail];
    }
  },
	methods: {
		async forgotPassword() {
			if (this.forgotPasswordFormValid && this.email) {
        const result = await UserService.forgotPassword(this.email);
        if (result === 200) {
          this.$emit("changeTab", TabProfileTypes.Login);
        }
			}
		},
    validateForm(value) {
      this.forgotPasswordFormValid = !value;
    }
	}
};
</script>
