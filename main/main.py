import json
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import requests  # Import pandas
import pandas as pd  # Import pandas
import config   # Import the config file
import webbrowser
from tkcalendar import DateEntry

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid()
        self.skillset_file = None  # Initialize skillset_file
        self.task_details_file = None  # Initialize task_file (Mira change the name to self.task_details_file - 5/11)
        self.create_widgets()
        self.skill_set_data = None  # Initialize skill_set_data

    def create_widgets(self):
        labels = ["Members skill set", "Task details"]
        descriptions = [
            ("Download template here: Members_skillset.xlsx", "https://fujitsu.sharepoint.com/:x:/r/teams/Asia-42f6e454-ChatAIContestAPG/Shared%20Documents/ChatAI%20Contest%20APG/Deliverable/Sprint%201/MEMBERS_SKILLSET.xlsx?d=w3087fb3ba54e43bab309789ad185a9a7&csf=1&web=1&e=5ekEi5"),
            ("Download template here: Task_details.xlsx", "https://fujitsu.sharepoint.com/:x:/r/teams/Asia-42f6e454-ChatAIContestAPG/Shared%20Documents/ChatAI%20Contest%20APG/Deliverable/Sprint%201/Task%20Details%20Sample.xlsx?d=we84ab6e37355440c9f70aa90c9f85bdc&csf=1&web=1&e=FtsjuW")
        ]
        self.entries = []
        for i, (label, (description, url)) in enumerate(zip(labels, descriptions)):
            tk.Label(self, text=label).grid(row=i*2, column=0, padx=10, pady=5, sticky='w')
            entry = tk.Entry(self, width=40)
            entry.grid(row=i*2, column=1, padx=10, pady=5)
            self.entries.append(entry)
            tk.Button(self, text="Browse", command=lambda e=entry, l=label: self.browse_file(e, l), width=10).grid(row=i*2, column=2, padx=10, pady=5)
            
            text_widget = tk.Text(self, height=1, width=40, font=("Helvetica", 8), bd=0, bg=self.cget("bg"))
            text_widget.grid(row=i*2+1, column=1, padx=10, sticky='w')
            text_widget.insert(tk.END, description)
            
            if "Members_skillset.xlsx" in description:
                text_widget.tag_add("link", "1.23", "1.end")
                text_widget.tag_config("link", foreground="blue", underline=True)
                text_widget.tag_bind("link", "<Button-1>", lambda e, url=url: self.open_url(url))
            else:
                text_widget.tag_add("link", "1.23", "1.end")
                text_widget.tag_config("link", foreground="blue", underline=True)
                text_widget.tag_bind("link", "<Button-1>", lambda e, url=url: self.open_url(url))
            
            text_widget.config(state=tk.DISABLED)

            tk.Button(self, text="Start", command=self.main, width=10).grid(row=8, column=1, padx=10, pady=10, sticky='e')
            tk.Button(self, text="Cancel", command=self.master.destroy, width=10).grid(row=8, column=2, padx=10, pady=10, sticky='w')
        
            # Status label to show process completion
            self.status_label = tk.Label(self, text="")
            self.status_label.grid(row=9, column=0, columnspan=3, padx=10, pady=10) 
        
    
    def browse_file(self, entry, label):
        file_types = [("Excel files", "*.xlsx *.xls")]
        file_path = filedialog.askopenfilename(filetypes=file_types)
        
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)
            
            if label == "Members skill set":
                self.skillset_file = file_path
                print(self.skillset_file)
            else:
                self.task_details_file = file_path
                print(self.task_details_file)
        else:
            messagebox.showerror("Error", "No file selected")

    def open_url(self, url):
        webbrowser.open_new(url)
    
    def main(self):
        # Call read file function
        self.skill_set_data = self.read_file(self.skillset_file, 3, None)
        self.task_details_data = self.read_file(self.task_details_file, 1, "B:E")
        self.send_data_to_chatai()


        #Test print from config file
        print(f"Test chatAI Key : {config.ChatAI_key}")

        # Use the prompt_message_template from config and format it with the data
        prompt_message = config.prompt_message_template.format(
            task_details_data=self.task_details_data.to_json(),
            skill_set_data=self.skill_set_data.to_json()
        )

        self.read_api_key()

    # rangecol=None mean will read all columns that has data
    def read_file(self, file, rowskip=0, rangecol=None):
        # print(file, rowskip, rangecol)
        try:
            file_data = pd.read_excel(file, skiprows=rowskip, usecols=rangecol)  # Read Excel file using pandas
            
            # Data cleaning steps
            file_data.dropna(axis=1, how='all', inplace=True)  # Remove columns with all missing values
            file_data.fillna(0, inplace=True)  # Replace NaN values with 0
            
            print(file_data)  # Print the task details data for debugging
            return(file_data)
        except FileNotFoundError:
            messagebox.showerror("Error", config.error_message["FileNotFoundError"])
        except pd.errors.EmptyDataError:
            messagebox.showerror("Error", config.error_message["EmptyDataError"])
        except pd.errors.ParserError:
            messagebox.showerror("Error", config.error_message["ParserError"])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel file: {e}")

    #Send data to ChatAI for analysis
    def send_data_to_chatai(self):
        try:
            self.status_label.config(text="Processing, please wait...")
            self.status_label.update_idletasks()  # Force the GUI to update

            #To extract only the start date and end date of the project 
            start_date = self.task_details_data.iloc[1,2]
            end_date = self.task_details_data.iloc[2,2]

            #Convert the date data into string to pass for prompt
            start_date_str = str(start_date)
            end_date_str = str(end_date)

            #Debug - print string start date and end date
            print(start_date_str)
            print(end_date_str)
            print(start_date)
            print(end_date)
            

            # Define the API endpoint and hardcoded prompt
            api_endpoint = "https://ai-foundation-api.app/ai-foundation/chat-ai/gpt4"
            prompt = (
                "#Input"
                f"{self.task_details_data.to_json()} "
                f"{self.skill_set_data.to_json()}"

                "#INSTRUCTIONS"
                "As a project manager, create a WBS for the project. The input are the task details and the skill set of the team members."
                "Please give in table format where each of the title should be the header"
                "For high task priority assign first to senior developer then to middle developer"
                "For medium task priority assign first to middle developer then junior developer" 
                "For low task priority first assign to junior developer then middle developer"
                "Please also consider the skills needed for each task with the member with high level skills for that particular need"
                "The output should include all members for each task and one task for one person only"
                "Please estimate the duration of each task without including it in the result. Then, set the start date and end date based on the duration."
                f"Please use the date range from the input data for start date = {start_date_str} and end date = {end_date_str} for each of the task."
                f"Please fully utilize the date but do not exceed the project's end date at {end_date_str}"
                "It should consists of:"
                
                "| Item No. {n} | Task Description: {Task Description} | Assigned to: {Assigned to based on the input data of the task} | Progress: {Progress of the task either To do/In progress/Waiting for Review/Done, default is To do} | Plan Start date: {Start date based on the input data of the task} | Plan End date: {End date based on the input data of the task} |\n"
            )

            headers = {
                "Content-type": "application/json",
                "api-key": "OnGCTtBUL4T2TrL6osaPi6hFInUhGzMAE3BmAp7loukbAiHE"
            }

            payload = {
                "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
                ]
            }
            
            # Send the POST request
            response = requests.post(api_endpoint, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Check the response
            try:
                analysis_result = response.json()
                #print("Analysis Result:", analysis_result)

                # Extract the content (only the wbs result)
                content = analysis_result['choices'][0]['message']['content']
                print(content)

            except json.JSONDecodeError:
                print("Error: The response is not in JSON format.")
                print("Response content:", response.text)

        except requests.exceptions.RequestException as e:
            print("Failed to get a response from ChatAI. Status code:", response.status_code)
            print("Response content:", response.text)
            messagebox.showerror("Error", f"Failed to send data to ChatAI: {e}")

        except ValueError as ve:
            print(ve)
            messagebox.showerror("Error", str(ve))
        finally:
            self.status_label.config(text="Process completed")

    def read_api_key(self):
        try:
            with open("API_Key.txt",'r') as file:
                content = file.read()
                print(content)
        except FileNotFoundError:
            messagebox.showerror("Error", config.error_message["APIKeyError"])
        except Exception as e:
            error_message = config.error_message["FailReadError"].format(error_message=str(e))
            messagebox.showerror("Error", error_message)

root = tk.Tk()
root.title("WBS Enhancement")
app = Application(master=root)
app.mainloop()