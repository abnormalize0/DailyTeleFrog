import { axiosClient } from "../axios";
import { showToast } from "@/utils/toast";

export const login = (username, password) => {
    return axiosClient.post('/user/login', {
        username: username,
        password: password
    }).catch((error) => {
        showToast(error.message, { type: 'error', autoClose: 5000 });
        return {};
    });
}

export const register = (username, password, email) => {
    return axiosClient.post('/user/register', {
        username: username,
        password: password,
        email: email
    }).catch((error) => {
        showToast(error.message, { type: 'error', autoClose: 5000 });
        return {};
    });
}

export const forgotPassword = (email) => {
    return axiosClient.post('/user/forgot/password', {
        email: email,
    }).catch((error) => {
        showToast(error.message, { type: 'error', autoClose: 5000 });
        return {};
    });
}