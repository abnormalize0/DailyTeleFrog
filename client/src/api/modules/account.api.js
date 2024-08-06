import { axiosClient } from "../axios";

export const login = (username, password) => {
    return axiosClient.post('/login', {
        username: username,
        password: password
    }).then((res) => {
        console.log(res);
    })
}