import { UserApi } from "@/api";

export const login = async (username, password) => {
    const { data } = await UserApi.login(username, password);
    return data;
}