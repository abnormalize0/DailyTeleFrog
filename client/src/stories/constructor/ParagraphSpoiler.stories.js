import ParagraphSpoiler from "@/components/constructor/ParagraphSpoiler.vue";
import { userEvent, within } from "@storybook/test";

export default {
  component: ParagraphSpoiler,
  title: 'ParagraphSpoiler',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

const content = 'Текст параграфа';

export const Default = {
  args: {
    content: content,
  }
}

// Function to emulate pausing between interactions
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

Default.play = async ({canvasElement}) => {
  await sleep(2000);
  const canvas = within(canvasElement);
  const hide = canvas.getByTestId("hide");
  console.log(hide);
  await userEvent.click(hide);
  await sleep(2000);
  await userEvent.click(hide);
  await sleep(2000);
}