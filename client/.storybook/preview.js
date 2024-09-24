/** @type { import('@storybook/vue3').Preview } */
import '../public/css/styles.css';
import { setup } from '@storybook/vue3';
import vuetify from '../src/plugins/vuetify';
import 'vuetify/styles';
import { VApp, VBtn, VChip, VContainer, VRow, VCol } from 'vuetify/components';

setup((app) => {
  app.use(vuetify);
  app.component('VApp', VApp);
  app.component('VBtn', VBtn);
  app.component('VChip', VChip);
  app.component('VContainer', VContainer);
  app.component('VRow', VRow);
  app.component('VCol', VCol);
});

const preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
  decorators: [
    (story) => ({
      components: { story, VApp },
      template: `<v-app><story/></v-app>`,
    })  
  ]
};

export default preview;
