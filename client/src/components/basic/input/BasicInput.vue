<template>
  <div class="d-flex flex-column input-error-gap">
    <div class="d-flex input-field primary-rounded" :class="errorVisible ? 'error-border' : 'primary-border'">
      <input class="input-text-box" 
        :class="errorVisible ? 'text-mistake-color' : 'text-secondary-color'" 
        v-model="modelValue" @input="updateModelValue($event.target.value)"
        :type="computedType" placeholder=" " @blur="validate" @keydown.enter="validate"/>
      <label class="floating-label p2" :class="errorVisible ? 'text-mistake-color' : 'text-secondary-color'">{{ label }}</label>
      <span v-if="type === 'password'" @click="togglePasswordVisibility" class="password-icon">
        <i v-if="!errorVisible" :class="passwordVisible ? 'eye-off' : 'eye'"></i>
        <i v-if="errorVisible" :class="passwordVisible ? 'eye-error-off' : 'eye-error'"></i>
      </span>
    </div>
    <div v-if="errorVisible" class="error-text p4 error-message">
      {{ errorMessage }}
    </div>
  </div>
</template>

<style scoped>
.input-error-gap {
  gap: 5px;
}

.input-field {
  display: flex;
  height: 50px !important;
  width: 100% !important;
  padding: 10px 15px;
  background-color: transparent;
  caret-color: var(--text-secondary-color) !important;
  transition: 600ms;
  position: relative;
  justify-content: center;
  align-items: center;
}

.input-field:hover,
.input-field:focus-within,
.input-field:active {
  background-color: var(--background-secondary-color);
}

.input-field .floating-label {
  position: absolute;
  left: 15px;
  pointer-events: none;
}

.input-field:focus-within .floating-label,
.input-field:active .floating-label {
  position: absolute;
  font-size: 10px !important;
  line-height: 11.6px !important;
  margin-bottom: 2px;
  top: 10px;
}

.input-text-box:not(:focus):not(:placeholder-shown)+.floating-label {
  display: none;
}

.input-text-box {
  width: 100%;
  outline: 0;
}

.input-field .input-text-box:focus {
  padding-top: 14px;
}

.input-field .input-text-box,
.input-field .floating-label {
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
  -webkit-transition: all 0.3s;
  transition: all 0.3s;
  -webkit-transition-timing-function: cubic-bezier(0.25, 0.1, 0.25, 1);
  transition-timing-function: cubic-bezier(0.25, 0.1, 0.25, 1);
}

.password-icon {
  position: absolute;
  align-self: center;
  right: 15px;
}

.error-message {
  margin-left: 1px;
}
</style>

<script>
export default {
  name: "BasicInput",
  props: {
    validators: {
      type: Array,
      default: () => [],
    },
    label: {
      type: String,
      default: "",
    },
    type: {
      type: String,
      default: "text"
    }
  },
  data() {
    return {
      modelValue: "",
      passwordVisible: false,
      errorVisible: false,
      errorMessage: "",
    }
  },
  computed: {
    computedType() {
      return this.passwordVisible && this.type === 'password' ? 'text' : this.type;
    }
  },
  emits: ['update:modelValue', 'error'],
  methods: {
    validate() {
      const validatorsResult = this.validators.map(val => val(this.modelValue)).filter(val => val.result === false);
      if (validatorsResult.length === 0) {
        this.errorVisible = false;
        this.errorMessage = "";
        this.$emit("error", false);
        return;
      }
      this.errorMessage = validatorsResult[0].message;
      this.errorVisible = true;
      this.$emit("error", true);
    },
    updateModelValue(value) {
      this.$emit("update:modelValue", value);
    },
    togglePasswordVisibility() {
      this.passwordVisible = !this.passwordVisible;
    }
  }
}
</script>
