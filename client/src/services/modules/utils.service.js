function sanitize(data) {
    return data.replace(/[!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]/g, "").replace(/\s/g, "");
}

function highlightInputs(namesToHighlight) {
    const inputsArray = document.getElementsByClassName("form-input");
    for (let i = 0; i < inputsArray.length; i++) {
            if (namesToHighlight.indexOf(inputsArray[i].attributes["name"].value) != -1) {
                inputsArray[i].classList.add("not-good-input"); // в идеале сделать классом и пушить/попать
            }
        }
}

export { sanitize, highlightInputs };