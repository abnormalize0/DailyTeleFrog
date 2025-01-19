import Paragraph from "@/components/constructor/Paragraph.vue";
import { ParagraphState } from "@/enum/ParagraphState";

export default {
  component: Paragraph,
  title: 'Paragraph',
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

export const Italic = {
  args: {
    content: content,
    states: [ParagraphState.ITALIC]
  }
}

export const Bold = {
  args: {
    content: content,
    states: [ParagraphState.BOLD]
  }
}

export const BoldItalic = {
  args: {
    content: content,
    states: [ParagraphState.BOLD, ParagraphState.ITALIC]
  }
}

export const Underline = {
  args: {
    content: content,
    states: [ParagraphState.UNDERLINE]
  }
}

export const UnderlineItalic = {
  args: {
    content: content,
    states: [ParagraphState.UNDERLINE, ParagraphState.ITALIC]
  }
}

export const UnderlineBold = {
  args: {
    content: content,
    states: [ParagraphState.UNDERLINE, ParagraphState.BOLD]
  }
}

export const UnderlineBoldItalic = {
  args: {
    content: content,
    states: [ParagraphState.UNDERLINE, ParagraphState.BOLD, ParagraphState.ITALIC]
  }
}

export const Strikethrough = {
  args: {
    content: content,
    states: [ParagraphState.STRIKETHROUGH]
  }
}

export const StrikethroughBold = {
  args: {
    content: content,
    states: [ParagraphState.STRIKETHROUGH, ParagraphState.BOLD]
  }
}

export const StrikethroughItalic = {
  args: {
    content: content,
    states: [ParagraphState.STRIKETHROUGH, ParagraphState.ITALIC]
  }
}

export const StrikethroughBoldItalic = {
  args: {
    content: content,
    states: [ParagraphState.STRIKETHROUGH, ParagraphState.BOLD, ParagraphState.ITALIC]
  }
}
