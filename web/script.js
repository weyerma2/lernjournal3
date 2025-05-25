function checkFiles(files) {
    console.log(files);

    if (files.length != 1) {
        alert("Bitte genau eine Datei hochladen.");
        return;
    }

    const fileSize = files[0].size / 1024 / 1024; // in MiB
    if (fileSize > 10) {
        alert("Datei zu gross (max. 10 MB)");
        return;
    }

    answerPart.style.visibility = "visible";
    const file = files[0];

    // Preview
    if (file) {
        preview.src = URL.createObjectURL(file);
    }

    // Upload
    const formData = new FormData();
    formData.append("0", file);

    fetch('/analyze', {
        method: 'POST',
        body: formData
    }).then(response => response.json()
    ).then(data => {
        console.log(data);
        let resultHtml = "";

        for (const [modelName, predictions] of Object.entries(data)) {
            resultHtml += `<h5>${modelName}</h5>`;
            resultHtml += "<table class='table table-sm table-bordered'><thead><tr><th>Class</th><th>Value</th></tr></thead><tbody>";

            predictions.forEach(item => {
                resultHtml += `<tr><td>${item.class}</td><td>${(item.value * 100).toFixed(2)}%</td></tr>`;
            });

            resultHtml += "</tbody></table><br>";
        }

        answer.innerHTML = resultHtml;
    }).catch(error => console.log(error));
}
