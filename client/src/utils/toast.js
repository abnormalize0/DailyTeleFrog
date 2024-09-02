import { toast } from 'vue3-toastify';
import "vue3-toastify/dist/index.css";

export const showToast = (message, options = {}) => {
  toast(message, {
    autoClose: options.autoClose || 3000,
    type: options.type || 'default',
    ...options
  });
};