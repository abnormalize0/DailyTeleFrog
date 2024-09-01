import { UserApi } from "@/api";

export const login = async (username, password) => {
    const { data } = await UserApi.login(username, password);
    return data;
}

export const register = async (username, password, email) => {
    const { data } = await UserApi.register(username, password, email);
    return data;
}

export const forgotPassword = async (email) => {
    const { status } = await UserApi.forgotPassword(email);
    return status;
}