import ForgotPasswordComponent from "@/components/common/profile/ForgotPasswordComponent.vue";
import LoggedInComponent from "@/components/common/profile/LoggedInComponent.vue";
import LoginComponent from "@/components/common/profile/LoginComponent.vue";
import ProfileComponent from "@/components/common/profile/ProfileComponent.vue";
import RegistrationCompleteComponent from "@/components/common/profile/RegistrationCompleteComponent.vue";
import RegistrationComponent from "@/components/common/profile/RegistrationComponent.vue";
import { within, userEvent, expect, waitFor } from '@storybook/test';

export default {
  components: {ProfileComponent, LoginComponent, LoggedInComponent, RegistrationComponent, ForgotPasswordComponent, RegistrationCompleteComponent},
  title: 'ProfileComponent',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}
const Template = (args) => ({
  components: {ProfileComponent, LoginComponent, LoggedInComponent, RegistrationComponent, ForgotPasswordComponent, RegistrationCompleteComponent},
  setup() {
    return args;
  },
  template: '<ProfileComponent />',
})

export const Default = Template.bind({})

Default.play = async ({canvasElement}) => {
  const canvas = within(canvasElement);
  const buttons = canvas.queryAllByText('Войти');
  await userEvent.click(buttons[1]);
  await waitFor(() => {
    const toastContainer = document.querySelector('.Toastify__toast-container');
    if (!toastContainer) throw new Error('Toast container not found');

    const toast = toastContainer.querySelector('.Toastify__toast');
    if (!toast) throw new Error('Toast not found');

    expect(toast).toBeInTheDocument();
  });

  const forgotPassword = canvas.queryAllByText('Забыли пароль?')[0];
  await userEvent.click(forgotPassword);

  const restorePassword = canvas.queryAllByAltText('Восстановить пароль')[0];
  await userEvent.click(restorePassword);
  await waitFor(() => {
    const toastContainer = document.querySelector('.Toastify__toast-container');
    if (!toastContainer) throw new Error('Toast container not found');

    const toast = toastContainer.querySelector('.Toastify__toast');
    if (!toast) throw new Error('Toast not found');

    expect(toast).toBeInTheDocument();
  });

  const backToLogin = canvas.queryAllByText('Назад')[0];
  await userEvent.click(backToLogin);

  const createAccount = canvas.queryAllByText('Создать аккаунт')[0];
  await userEvent.click(createAccount);

  const createAccount2 = canvas.queryAllByText('Создать аккаунт')[0];
  await userEvent.click(createAccount2);
  await waitFor(() => {
    const toastContainer = document.querySelector('.Toastify__toast-container');
    if (!toastContainer) throw new Error('Toast container not found');

    const toast = toastContainer.querySelector('.Toastify__toast');
    if (!toast) throw new Error('Toast not found');

    expect(toast).toBeInTheDocument();
  });

  const backToLogin2 = canvas.queryAllByText('Назад')[0];
  await userEvent.click(backToLogin2);
}