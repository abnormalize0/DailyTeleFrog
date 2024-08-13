import { axiosClient } from "../axios";

export const login = (username, password) => {
    return axiosClient.post('/user/login', {
        username: username,
        password: password
    });
}