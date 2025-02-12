import Letter from "@/components/add-post/text-frame/Letter.vue";
import { ParagraphState } from "@/enum/ParagraphState";

export default {
  component: Letter,
  title: 'Letter',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

export const Bold = {
  args: {
    type: ParagraphState.BOLD
  }
}

export const Italic = {
  args: {
    type: ParagraphState.ITALIC
  }
}

export const Underline = {
  args: {
    type: ParagraphState.UNDERLINE
  }
}

export const StrikeThrough = {
  args: {
    type: ParagraphState.STRIKETHROUGH
  }
}

export const Censor = {
  args: {
    type: ParagraphState.SPOILER
  }
}