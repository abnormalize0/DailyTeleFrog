import { AccountApi } from "@/api";

export const login = async (username, password) => {
    const { data } = await AccountApi.login(username, password);
    return data;
}