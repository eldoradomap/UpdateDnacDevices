import json
from dnacentersdk import DNACenterAPI
import time
import os
import tkinter as tk
from tkinter import messagebox, simpledialog
import sys

with open("creds.json", "r") as config_file:
    config = json.load(config_file)

# Replace these variables with your Cisco DNA Center details 
DNAC_USERNAME=config["DNAC_USERNAME"]
DNAC_PASSWORD=config["DNAC_PASSWORD"]
DNAC_URL=config["DNAC_URL"]
VERSION=config["VERSION"]
# VERIFY=config["VERIFY"]

# Initialize the DNACenterAPI object
api = DNACenterAPI(
    username=DNAC_USERNAME,
    password=DNAC_PASSWORD,
    base_url=DNAC_URL,
    version=VERSION,  # Replace with your DNAC version
    verify=False
    # verify=VERIFY
)

persistent_storage = "main/persistent.json"

def save(name, value):
    variables = {}
    if os.path.exists(persistent_storage):
        with open(persistent_storage, "r") as f:
            try:
                variables = json.load(f)
            except json.JSONDecodeError:
                variables = {}

    variables[name] = value
    with open(persistent_storage, "w") as f:
        json.dump(variables, f)

def load(filename=persistent_storage):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

#/--------------------/
# Create Proj Function
#/--------------------/

def create_project_function():
    project_name = simpledialog.askstring("Input", "Enter the name of the project: ")
    description = simpledialog.askstring("Input", "Enter a description for the project: ")
    
    # advanced_config = input("Enter y/n to enter advanced configuration mode: ")
    
    # if advanced_config == 'y' or advanced_config == 'Y':
    #     print()
        #Put the rest of the possible method vars with input vars

    api.configuration_templates.create_project(
        name=project_name,
        description=description
    )

    time.sleep(5)

    proj_id = api.configuration_templates.get_projects(project_name)[0]['id']
    save("proj_id", proj_id)
    return proj_id

#/--------------------/
# Create Template Function
#/--------------------/

def create_template_function(proj_id):
    template_name = simpledialog.askstring("Input", "Enter the name of the template: ")
    description = simpledialog.askstring("Input", "Enter a description for the template: ")
    template_Content = open("main/configs.txt", "r").read()


    # advanced_config = input("Enter y/n to enter advanced configuration mode: ")

    # if advanced_config == 'y' or advanced_config == 'Y':
    #     print()
        #Put the rest of the possible method vars with input vars

    resp = api.configuration_templates.create_template(
        author=DNAC_USERNAME,
        name=template_name,
        description=description,
        project_id=proj_id,
        language="JINJA",
        deviceTypes=[{"productFamily": "Switches and Hubs"}],
        softwareType="IOS-XE",
        templateContent=template_Content,
    )

    time.sleep(5)

    templateId = api.configuration_templates.get_projects_details(id=proj_id)["response"][0]["templates"][0]["id"]

    ver_resp = api.configuration_templates.version_template(
        templateId=templateId,
        comments="Init"
    )
    save("template_name", template_name)
    save("templateId", templateId)
    return templateId

#/--------------------/
# Update Template Function
#/--------------------/

def update_template_function(template_name, templateId, proj_id):

    resp = api.configuration_templates.update_template(
        name=template_name,
        deviceTypes=[{"productFamily": "Switches and Hubs"}],
        id=templateId,
        language="JINJA",
        projectId=proj_id,
        softwareType="IOS-XE",
        templateContent=open("main/configs.txt", "r").read(),
    )

    comments = simpledialog.askstring("Input", "OPTIONAL. Enter comments for the template: ")
    time.sleep(5)
    templateId = api.configuration_templates.get_projects_details(id=proj_id)["response"][0]["templates"][0]["id"]

    ver_resp = api.configuration_templates.version_template(
        templateId=templateId,
        comments=comments
    )

    return templateId

#/--------------------/
# Deploy Function
#/--------------------/

def deploy_to_all_function(templateId):
    
    device_ids = []
    devices = api.devices.get_device_list()['response']

    for device in devices:
        device_ids.append(device['id'])
    
    target_Info = [{"id": device_id, "type": "MANAGED_DEVICE_UUID"} for device_id in device_ids]

    resp = api.configuration_templates.deploy_template(
        templateId=templateId,
        targetInfo=target_Info
    )

    print(resp)
    print("AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
    print(target_Info)
    messagebox.showinfo(title="Success!", message=templateId)
    sys.exit()

#/--------------------/
# Search Project Function
#/--------------------/

def search_select_projects():
    
    project_dict = {}
    project_id_dict = {}
    count = 0

    projects = api.configuration_templates.get_projects()

    for project in projects:
        count+=1
        project_dict[count] = project['name']
        project_id_dict[project['name']] = project['id']

    user_input = simpledialog.askinteger("Input", "Make your selection using a number: \n"+"\n".join([str(key)+" : "+value for key, value in project_dict.items()]))

    while True:
        if user_input in project_dict.keys():
            confirm = messagebox.askyesno("Input", "You selected the " + project_dict[user_input] + " project is that correct?")
            if confirm == True:
                messagebox.showinfo(title="ALERT", message="Proceeding with process.")
                proj_id = project_id_dict[project_dict[user_input]]
                save("proj_id", proj_id)
                return proj_id
            else:
                messagebox.showinfo(title="ALERT", message="Cancelling operation.")
        else:
            messagebox.showinfo(title="ALERT", message="Enter a valid selection.")

#/--------------------/
# Deciscion Tree Function
#/--------------------/

def decision_tree():
    
    create_project_question = messagebox.askyesno("Input", "Do you want to create a new project?")

    if create_project_question == True:
            create_template_question = messagebox.askyesno("Input", "Do you want to create a new template?")

            if create_template_question == True:
                data = load()
                deploy_to_all_function(create_template_function(data.get("proj_id")))

            else: 
                data = load()
                deploy_to_all_function(update_template_function(data.get("template_name"), data.get('templateId'), data.get('proj_id')))

    else:
        create_template_question = messagebox.askyesno("Input", "Do you want to create a new template?")
        if create_template_question == True:
            deploy_to_all_function(create_template_function(proj_id=search_select_projects()))
        else:
            #DOES NOT WORK YET
            deploy_to_all_function(update_template_function(search_select_projects()))


#/--------------------/
# Main Function
#/--------------------/

def main():
    root = tk.Tk()
    root.withdraw()
    decision_tree()


if __name__ == "__main__":
    main()