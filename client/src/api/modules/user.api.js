import { axiosClient } from "../axios";

export const login = (username, password) => {
    return axiosClient.post('/user/login', {
        username: username,
        password: password
    });
}

export const register = (username, password, email) => {
    return axiosClient.post('/user/register', {
        username: username,
        password: password,
        email: email
    });
}

export const forgotPassword = (email) => {
    return axiosClient.post('/forgot/password', {
        email: email,
    });
}