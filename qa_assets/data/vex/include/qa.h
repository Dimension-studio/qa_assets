// This function is used by check nodes in Houdini,
// it is used for an uniform reporting of results
void report_qa_result(const string status, message) {
    string status_lower = tolower(status);

    dict result = set("status", status_lower, "message", message);

    // Check for valid statuses and set it to error if it isn't
    if (
        status_lower != "pass" &&
        status_lower != "warn" &&
        status_lower != "fail"
    )
        result["status"] = "error";

    // Serialize result dict into a string and set it as node's
    // warning, which will be read by the rest of the tooling
    string result_str = json_dumps(result, 2);

    warning(result_str);
}
