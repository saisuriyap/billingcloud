import requests
import json
from datetime import datetime, timezone
import dateutil.parser
from dotenv import load_dotenv
import os
# Get current month and year in YYYY-MM format
current_month = datetime.now().strftime("%Y-%m")
current_time = datetime.now(timezone.utc)
load_dotenv("./auth.env")
# IBM Cloud API Endpoints
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
RESOURCE_GROUPS_URL = f"https://resource-controller.cloud.ibm.com/v2/resource_groups"
RESOURCE_INSTANCES_URL = f"https://resource-controller.cloud.ibm.com/v2/resource_instances"

IBM_CLOUD_API_KEY=os.getenv("IBM_CLOUD_API_KEY")
ACCOUNT_ID=os.getenv("ACCOUNT_ID")

def get_iam_token():
    print("=====Entering Token generation phase=======")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={IBM_CLOUD_API_KEY}"
    
    response = requests.post(IAM_TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        print("=====PASS: Exiting Token generation phase=======")
        return response.json()["access_token"]
    else:
        print(f"Error fetching IAM token: {response.status_code}")
        print(response.text)
        print("=====FAIL: Exiting Token generation phase=======")
        return None

def get_resource_groups():
    print("=====Entering Resource Groups Fetch Phase=======")
    token = get_iam_token()
    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(RESOURCE_GROUPS_URL, headers=headers)
    
    if response.status_code == 200:
        with open('resource_groups.json', 'w') as f:
            json.dump(response.json(), f)
        print("=====PASS: Exiting Resource Groups Fetch Phase=======")
        return response.json().get("resources", [])
    else:
        print(f"Error fetching resource groups: {response.status_code}")
        print(response.text)
        print("=====FAIL: Exiting Resource Groups Fetch Phase=======")
        return None

def get_resource_group_usage(resource_group_id):
    print(f"=====Entering Resource Group Usage Fetch Phase for {resource_group_id}=======")
    token = get_iam_token()
    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    resource_group_usage_url = f"https://billing.cloud.ibm.com/v4/accounts/{ACCOUNT_ID}/resource_groups/{resource_group_id}/usage/{current_month}"
    response = requests.get(resource_group_usage_url, headers=headers)
    
    if response.status_code == 200:
        with open(f'usage_{resource_group_id}.json', 'w') as f:
            json.dump(response.json(), f)
        print(f"=====PASS: Exiting Resource Group Usage Fetch Phase for {resource_group_id}=======")
        return response.json()
    else:
        print(f"Error fetching resource group usage: {response.status_code}")
        print(response.text)
        print(f"=====FAIL: Exiting Resource Group Usage Fetch Phase for {resource_group_id}=======")
        return None

def calculate_uptime(created_at):
    created_datetime = dateutil.parser.isoparse(created_at)
    uptime = current_time - created_datetime
    
    years, remainder = divmod(uptime.days, 365)
    months, days = divmod(remainder, 30)
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_parts = []
    if years > 0:
        uptime_parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months > 0:
        uptime_parts.append(f"{months} month{'s' if months > 1 else ''}")
    if days > 0:
        uptime_parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        uptime_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        uptime_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds > 0:
        uptime_parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")    
    
    return {
        'total_days': uptime.days,
        'uptime_string': ', '.join(uptime_parts) if uptime_parts else 'Less than a minute',
        'created_at': created_datetime.strftime("%Y-%m-%d %H:%M:%S UTC")
    }

def get_resource_instances():
    print("=====Entering Resource Instances Fetch Phase=======")
    token = get_iam_token()
    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    all_instances = []
    next_url = RESOURCE_INSTANCES_URL

    while next_url:
        response = requests.get(next_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            all_instances.extend(data.get("resources", []))
            
            next_url = data.get("next_url")
            if next_url and not next_url.startswith("http"):
                next_url = f"https://resource-controller.cloud.ibm.com{next_url}"
        else:
            print(f"Error fetching resource instances: {response.status_code}")
            print(response.text)
            break

    with open('resource_instances.json', 'w') as f:
        json.dump(all_instances, f)
    print(f"=====PASS: Fetched {len(all_instances)} Resource Instances=======")
    return all_instances

def generate_resource_group_report():
    resource_groups = get_resource_groups()
    if not resource_groups:
        print(" Failed to retrieve resource groups.")
        return

    resource_instances = get_resource_instances()
    if not resource_instances:
        print("Failed to retrieve resource instances.")

    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; color: #333; }
            h1 { color: #007BFF; }
            h2 { color: #34eb49; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #007BFF; color: white; }
            .resource-group { border-left: 5px solid #007BFF; padding-left: 15px; margin-top: 30px; }
            .highlight-red { background-color: #ffcccc; }
        </style>
    </head>
    <body>
        <h1>IBM Cloud Resource Instance Uptime Report - """ + current_month + """</h1>
    """

    for group in resource_groups:
        resource_group_id = group.get("id")
        resource_group_name = group.get("name", "Unnamed Group")
        usage_data = get_resource_group_usage(resource_group_id)

        html_content += f"""
        <div class="resource-group">
            <h2>Resource Group: {resource_group_name}</h2>
            <p><strong>Resource Group ID:</strong> {resource_group_id}</p>
            <table>
                <tr>
                    <th>Resource Name</th>
                    <th>Type</th>
                    <th>State</th>
                    <th>Created At</th>
                    <th>Uptime</th>
                    <th>Total Days</th>
                </tr>
        """

        for instance in resource_instances:
            if instance.get('resource_group_id') != resource_group_id:
                continue
                
            name = instance.get('name', 'Unnamed Instance')
            created_at = instance.get('created_at')
            
            if not created_at:
                continue
            
            uptime_details = calculate_uptime(created_at)
            total_days = uptime_details['total_days']
            style = "class='highlight-red'" if total_days > 28 else ""

            html_content += f"""
                <tr>
                    <td>{name}</td>
                    <td>{instance.get('type', 'N/A')}</td>
                    <td>{instance.get('state', 'N/A')}</td>
                    <td>{uptime_details['created_at']}</td>
                    <td>{uptime_details['uptime_string']}</td>
                    <td {style}>{total_days} days</td>
                </tr>
            """

        html_content += """
            </table>
        </div>
        """

    html_content += """
        <p>Regards,</p>
        <p><b>IBM Cloud Resource Monitoring System</b></p>
    </body>
    </html>
    """

    with open("time_summary.html", "w") as output_file:
        output_file.write(html_content)

generate_resource_group_report()