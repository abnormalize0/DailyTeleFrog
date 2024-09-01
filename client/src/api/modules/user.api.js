import { axiosClient } from "../axios";

export const login = (username, password) => {
    return axiosClient.post('/user/login', {
        username: username,
        password: password
    }).catch((error) => {
        console.error(error.toJSON());
        return {};
    });
}

export const register = (username, password, email) => {
    return axiosClient.post('/user/register', {
        username: username,
        password: password,
        email: email
    }).catch((error) => {
        console.error(error.toJSON());
        return {};
    });
}

export const forgotPassword = (email) => {
    return axiosClient.post('/user/forgot/password', {
        email: email,
    }).catch((error) => {
        console.error(error.toJSON());
        return {};
    });
}