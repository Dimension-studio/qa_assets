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
        targetEl.classList.remove("border-dashed", "border-2")

        e.preventDefault();
    });
}

// Set up drag & drop on our element
dropJSON(document.querySelector("#drop-target"), JSONReport);

// JSON-processing function
function JSONReport(data) {
    console.log(data);
};
