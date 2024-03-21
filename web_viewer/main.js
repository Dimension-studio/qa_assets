"use strict";

// Function for setting drag & drop
// https://stackoverflow.com/a/30100596
function dropJSON(targetEl, callback) {
    // disable default drag & drop functionality
    targetEl.addEventListener("dragenter", function (e) {
        // Make the box border dashed
        targetEl.classList.add("border-dashed", "border-2")

        e.preventDefault();
    });

    targetEl.addEventListener("dragover", function (e) { e.preventDefault(); });

    targetEl.addEventListener("drop", function (event) {

        let reader = new FileReader();
        reader.onloadend = function () {
            let data = JSON.parse(this.result);

            // Call our passed JSON-processing function
            callback(data);
        };

        reader.readAsText(event.dataTransfer.files[0]);

        // Revert the dashed box border
        targetEl.classList.remove("border-dashed", "border-2")

        event.preventDefault();
    });
}

// Set up drag & drop on our element
dropJSON(document.querySelector("#drop-target"), JSONReport);

// JSON-processing function
function JSONReport(data) {
    console.log(data);
};
