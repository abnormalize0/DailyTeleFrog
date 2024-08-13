const tabProfileTypes = {
    LogedIn: 3,
    Login: 0,
    Register: 1,
    ForgotPassword: 2,
    RegistrationSuccess: 4,
}
function changeTab (element, tabNumber) {
    element.$emit("changeTab", tabNumber);
}

export {tabProfileTypes, changeTab};