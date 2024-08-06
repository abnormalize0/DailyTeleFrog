import { AccountApi } from "@/api";

export const loginPost = async (username, password) => {
    AccountApi.login(username, password);

}