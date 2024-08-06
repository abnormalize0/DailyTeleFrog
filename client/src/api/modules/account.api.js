import { axiosClient } from "../axios";

export const login = (username, password) => {
    return axiosClient.post('/login', {
        
    })
}