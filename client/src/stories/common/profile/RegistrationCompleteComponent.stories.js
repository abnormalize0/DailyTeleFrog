import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import ProfileComponent from "@/components/common/profile/ProfileComponent.vue";
import RegistrationCompleteComponent from "@/components/common/profile/RegistrationCompleteComponent.vue";

export default {
  components: {RegistrationCompleteComponent, BasicPrimaryButton, ProfileComponent},
  title: 'RegistrationCompleteComponent',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

const Template = (args) => ({
  components: {RegistrationCompleteComponent, BasicPrimaryButton, ProfileComponent},
  setup() {
    return args;
  },
  template: '<RegistrationCompleteComponent />',
})

export const Default = Template.bind({});