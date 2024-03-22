"use strict";

// Function for setting drag & drop
// https://stackoverflow.com/a/30100596
function dropJSON(targetEl, callback) {
    // Disable the default drag & drop functionality
    targetEl.addEventListener("dragenter", function (e) {
        // Make the box border dashed
        targetEl.classList.add("border-dashed", "border-2")

        e.preventDefault();
    });

    // Prevent file from being opened by the browser
    targetEl.addEventListener("dragover", function (e) { e.preventDefault(); });

    targetEl.addEventListener("drop", function (e) {
        let files = e.dataTransfer.files;

        // Iterate over all files
        for (let i = 0; i < files.length; i++) {
            // Create a new FileReader object with the onloadend handling
            let reader = new FileReader();

            reader.onloadend = function () {
                let data = JSON.parse(this.result);
                // Call our passed JSON-processing function
                // Pass also file name
                callback({
                    name: files[i].name,
                    data: data
                });
            };

            // Read the current file
            reader.readAsText(files[i]);
        }

        // Revert the dashed box border
        targetEl.classList.remove("border-dashed", "border-2");

        e.preventDefault();
    });
}

// Set up drag & drop on our element
dropJSON(document.querySelector("#drop-target"), JSONReport);

// JSON-processing function
function JSONReport(data) {
    let reportsEl = document.querySelector("#reports");
    let name = data.name;
    let report = data.data;

    let overall_status = "success";

    let reportLIs = "";

    report.reports.forEach(el => {
        let msg = "";
        if (el.message.length > 0)
            msg = `<details><summary class="text-muted small">Details</summary><p>${el.message}</p></details>`;

        let status;
        if (el.status === "pass") status = "success";
        else if (el.status === "warn") status = "warning";
        else if (el.status === "fail") status = "danger";
        else if (el.status === "error") status = "danger";

        // Update the overall status
        if (status === "warning" && overall_status === "success") overall_status = "warning";
        else if (status === "danger" && (overall_status === "success" || overall_status === "warning")) overall_status = "danger";

        reportLIs += `
        <li class="list-group-item">
            <span class="badge text-bg-${status}">${el.status.toUpperCase()}</span> ${el.node_name}<br>
            <code>${el.node_type}</code>
            ${msg}
        </li>
        `
    });

    let reportHTML = `
    <div class="col">
        <div class="card border-${overall_status}">
            <div class="card-body">
                <h5 class="card-title">${name}</h5>
                <code>
                    ${report.asset_path}
                </code>
                <p class="card-subtitle mt-1 mb-2 text-muted small">
                    Cooked: ${report.cook_success}, ${report.user}@${report.node}, ${report.time}
                </p>
                <ul class="list-group">
                    ${reportLIs}
                </ul>
            </div>
        </div>
    </div>
    `

    reportsEl.innerHTML += reportHTML;
};
