ChatAI_key = "OnGCTtBUL4T2TrL6osaPi6hFInUhGzMAE3BmAp7loukbAiHE"
prompt_message_template = (
                "#Input"
                "{task_details_data}"
                "{skill_set_data}"
 
                "#INSTRUCTIONS"
                "As a project manager, Organize and Generate a Work Breakdown Structure (WBS) for the project. The input are the task details and the skill set of the team members."
                "The output should include all members for each task. The output should be in the excel format:"
 
                "#Output Template"
                "Role: {Role of member based on the input data of the task}"
                "Task No."
                "Task Description: {Task Description}"
                "Assigned To: {Assigned to based on the input data of the task}"
                "Progress: {Task completion based on the input data of the task}"
                "Expected duration: {hours/days considered necessary to perform the task}"
                "Plan Start: {Plan start date for the task: Date format}"
                "Plan End: {Plan end date for the task: Date format}"
                "Actual Start: {Actual Start date based on the input data of the task}"
                "Actual End: {Actual End date based on the input data of the task}"
            )
error_message = {
    "FileNotFoundError": "The file was not found. Please check the file path and try again.",
    "EmptyDataError": "The file is empty. Please provide a valid Excel file with data.",
    "ParserError": "There was a problem parsing the file. Please ensure the file is a valid Excel file.",
    "APIKeyError": "The API Key file was not found. Please check the file path and try again.",
    "FailReadError": "Failed to read Excel file: {error_message}",
    "GeneralError": "An error occurred: {error_message}"
}