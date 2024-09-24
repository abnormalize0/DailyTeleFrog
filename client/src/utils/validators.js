// ВСЕ ВАЛИДАТОРЫ ВОЗВРАЩАЮТ ТРУ ЕСЛИ ВСЕ ОК

const validator = require('email-validator');

function required(data) {
    return {
        result: !(typeof(data) === typeof(null)
        || typeof(data) === typeof(undefined)
        || data.length === 0),
        message: "Это поле обязательно"
    } 
}

function minLength(data, length) {
    return {
        result: data.length >= length,
        message: "Содержимое поля слишком короткое"
    };
}

function maxLength (data, length) {
    return {
        result: data.length <= length,
        message: "Содержимое поля слишком длинное"
    };
}

function sanitizeLogin(data) {
    return {
        result: /^[a-zA-Z0-9_-]{6,32}$/.test(data),
        message: "Логин не соответствует правилам",
    };
}

function sanitizePassword(data) {
    return {
        result: /^[a-zA-Z0-9!@#$%^&*+=<>?~`|,.]{8,24}$/.test(data),
        message: "Пароль не соответствует правилам"
    };
}

function sanitizeEmail(data) {
    return {
        result: validator.validate(data),
        message: "Email не соответвует формату"
    };
}

export { sanitizeEmail, sanitizeLogin, sanitizePassword, maxLength, minLength, required };