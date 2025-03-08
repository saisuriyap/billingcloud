import requests
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# IBM Cloud API Key and Account ID
IBM_CLOUD_API_KEY = "qBheXSx2n3NrLv5w2SmyhVk6QOUjKd4k0H7cSPfEfpS-"
ACCOUNT_ID = "6a9b18b8d05a4b6392a8c9ef9a064505"

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"  # Change for different providers
SMTP_PORT = 587
EMAIL_SENDER = "pavankumar.ambuga@gmail.com"
EMAIL_PASSWORD = ""
EMAIL_RECEIVER = "pavan.govindraj@ibm.com"

# IBM Cloud API Endpoints
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
# COST_API_URL = f"https://billing.cloud.ibm.com/v4/accounts/{ACCOUNT_ID}/resource_instances/usage_reports"
COST_API_SUMMARY_URL = f"https://billing.cloud.ibm.com//v4/accounts/{ACCOUNT_ID}/summary/2025-02"
COST_API_USAGE_URL = f"https://billing.cloud.ibm.com//v4/accounts/{ACCOUNT_ID}/usage/2025-02"
COST_API_RESOURCE_INSTANCR_USAGE_URL = f"https://billing.cloud.ibm.com//v4/accounts/{ACCOUNT_ID}/resource_instances/usage/2025-02"

# Function to get IBM IAM Token
def get_iam_token():
    print("=====Entering Token generation phase=======")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={IBM_CLOUD_API_KEY}"
    
    response = requests.post(IAM_TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        print("=====PASS: Exiting Token generation phase=======")
        return response.json()["access_token"]
    else:
        print("Error fetching IAM token:", response.json())
        print("=====FAIL: Exiting Token generation phase=======")
        return None

# Function to get IBM Cloud costs summary
def get_ibm_cloud_costs_summary():
    print("=====Entering Account Cost Summary Generation Phase=======")
    token = get_iam_token()
    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(COST_API_SUMMARY_URL, headers=headers)
    
    if response.status_code == 200:
        print("=====PASS: Exiting Account Cost Summary Generation Phase=======")
        return response.json()
    else:
        print("Error fetching cost data:", response.json())
        print("=====FAIL: Exiting Account Cost Summary Generation Phase=======")
        return None
    
# Function to get IBM Cloud costs usage
def get_ibm_cloud_costs_usage():
    print("=====Entering Account Cost Usage Generation Phase=======")
    token = get_iam_token()
    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(COST_API_USAGE_URL, headers=headers)
    
    if response.status_code == 200:
        print("=====PASS: Exiting Account Cost Usage Generation Phase=======")
        # return json.dumps(response.json(), indent=4)
        return response.json()
    else:
        print("Error fetching cost data:", response.json())
        print("=====FAIL: Exiting Account Cost Usage Generation Phase=======")
        return None
    
# Function to get IBM Cloud resource instance usage
def get_ibm_cloud_resource_instance_usage():
    print("=====Entering Resource Instance Usage Generation Phase=======")
    token = get_iam_token()
    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(COST_API_RESOURCE_INSTANCR_USAGE_URL, headers=headers)
    
    if response.status_code == 200:
        print("=====PASS: Exiting Resource Instance Usage Generation Phase=======")
        # return json.dumps(response.json(), indent=4)
        return response.json()
    else:
        print("Error fetching cost data:", response.json())
        print("=====FAIL: Exiting Resource Instance Usage Generation Phase=======")
        return None

# Function to send email report
def send_email_report(cost_data):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "IBM Cloud Daily Cost Report"

    # Format cost data for email
    cost_summary = json.dumps(cost_data, indent=4)
    email_body = f"Here is your IBM Cloud cost report for today:\n\n{cost_summary}"
    
    msg.attach(MIMEText(email_body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

SENDGRID_API_KEY = ""
EMAIL_SENDER = "pavankumar.ag@gmail.com"
EMAIL_RECEIVER = "pavan.govindraj@ibm.com"

def send_email_via_sendgrid(subject, body):
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [{"to": [{"email": EMAIL_RECEIVER}]}],
        "from": {"email": EMAIL_SENDER},
        "subject": subject,
        "content": [{"type": "text/html", "value": body}]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 202:
        print("✅ Email sent successfully via SendGrid!")
    else:
        print(f"❌ Failed to send email: {response.json()}")


# Main Execution
cost_summary_data = get_ibm_cloud_costs_summary()
if cost_summary_data:
    print("==Success: Got cost summary data======")
    # print(cost_summary_data)
else:
    print("Failed to retrieve IBM Cloud summary cost data.")

cost_usage_data = get_ibm_cloud_costs_usage()
if cost_usage_data:
    print("==Success: Got cost usage data======")
    # print(cost_usage_data)
else:
    print("Failed to retrieve IBM Cloud cost usage data.")

cost_resource_instances_usage_data = get_ibm_cloud_resource_instance_usage()
if cost_resource_instances_usage_data:
    print("==Success: Got resource instance usage data======")
    # print(cost_resource_instances_usage_data)
else:
    print("Failed to retrieve IBM Cloud cost resource usage data.")



# (1)  Generate HTML data for account summary

account_id = cost_summary_data.get("account_id", "N/A")
month = cost_summary_data.get("month", "N/A")
billable_cost = cost_summary_data["resources"].get("billable_cost", 0)
non_billable_cost = cost_summary_data["resources"].get("non_billable_cost", 0)
currency = cost_summary_data.get("billing_currency_code", "N/A")
resources = cost_summary_data.get("account_resources", [])


html_content = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; color: #333; }}
        h1 {{ color: #007BFF; }}
        h2 {{ colot: #34eb49; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #007BFF; color: white; }}
    </style>
</head>
<body>
    <h1>IBM Cloud Cost Report - {month}</h1>
    <h2>1. Account Summary Breakup - {month}</h2>
    <p><strong>Account ID:</strong> {account_id}</p>
    <p><strong>Total Billable Cost:</strong> ${billable_cost:.2f} {currency}</p>
    <p><strong>Non-Billable Cost:</strong> ${non_billable_cost:.2f} {currency}</p>
    
    <h3>Resource Cost Breakdown</h3>
    <table>
        <tr>
            <th>Resource Name</th>
            <th>Billable Cost ({currency})</th>
            <th>Discounts Applied</th>
        </tr>
"""

# Loop through resources and add table rows
for resource in resources:
    resource_name = resource.get("resource_name", "Unknown")
    cost = resource.get("billable_cost", 0)
    

    discounts = ""
    for discount in resource.get("discounts", []):
        discounts += discount.get("name", "Unknown Discount") + "->" + str(discount.get("discount", 0)) + "%" + "<br>"
    if not discounts:
        discounts = "None"

    html_content += f"""
        <tr>
            <td>{resource_name}</td>
            <td>${cost:.2f}</td>
            <td>{discounts}</td>
        </tr>
    """

html_content += """
    </table> <br>"""


# (2) generate HTML data for account usage data

billing_country = cost_usage_data.get("billing_country", "N/A")
currency = cost_usage_data.get("currency_code", "N/A")
month = cost_usage_data.get("month", "N/A")
usage_resources = cost_usage_data.get("resources", [])

html_content += f"""<h2>2. Account Usage Breakup - {month}</h2>
    <p><strong>Billing Country:</strong> {billing_country}</p>
    <p><strong>Currency:</strong> {currency}</p>

    <h3>Resource Cost Breakdown</h3>
    <table>
        <tr>
            <th>Resource Name</th>
            <th>Billable Cost ({currency})</th>
            <th>Billable Rated Cost ({currency})</th>
            <th>Non Billable Cost ({currency})</th>
            <th>Non Billable Rated Cost ({currency})</th>
            <th>Usage Details</th>
        </tr>
"""

# Process each resource
for resource in usage_resources:
    resource_name = resource.get("resource_id", "Unknown Resource")
    billable_cost = resource.get("billable_cost", 0)
    billable_rated_cost = resource.get("billable_rated_cost", 0)
    non_billable_cost = resource.get("non_billable_cost", 0)
    non_billable_rated_cost = resource.get("non_billable_rated_cost", 0)
    
    # Extract usage details
    usage_details = []
    for plan in resource.get("plans", []):
        for usage in plan.get("usage", []):
            metric = usage.get("metric", "Unknown Metric")
            quantity = usage.get("quantity", 0)
            unit = usage.get("unit", "")
            usage_details.append(f"{quantity:.2f} {unit} ({metric})")
    
    usage_text = "<br>".join(usage_details) if usage_details else "No Usage Data"

    html_content += f"""
        <tr>
            <td>{resource_name}</td>
            <td>${billable_cost:.2f}</td>
            <td>${billable_rated_cost:.2f}</td>
            <td>${non_billable_cost:.2f}</td>
            <td>${non_billable_rated_cost:.2f}</td>
            <td>{usage_text}</td>
        </tr>
    """

html_content += """
    </table><br>"""

# (3) generate HTML data for resource instance usage data
month = cost_resource_instances_usage_data.get("resources", [])[0].get("month", "N/A")
currency = cost_resource_instances_usage_data.get("resources", [])[0].get("currency_code", "USD")

html_content += f"""
<h2>3. Resource Usage Report Breakup- {month}</h2>
    <p><strong>Currency:</strong> {currency}</p>

    <h3>Resource Cost Breakdown</h3>
    <table>
        <tr>
            <th>Resource Name</th>
            <th>Usage Metric</th>
            <th>Quantity</th>
            <th>Billable Cost ({currency})</th>
            <th>Discounts Applied</th>
        </tr>
"""

# Process each resource
for resource in cost_resource_instances_usage_data.get("resources", []):
    resource_name = resource.get("resource_id", "Unknown Resource")
    for usage in resource.get("usage", []):
        metric = usage.get("metric", "N/A")
        unit = usage.get("unit", "N/A")
        quantity = usage.get("quantity", 0)
        cost = usage.get("cost", 0)

        discounts = ""
        for discount in usage.get("discounts", []):
            discounts += discount.get("name", "Unknown Discount") + "->" + str(discount.get("discount", 0)) + "%" + "<br>"
        if not discounts:
            discounts = "None"

        html_content += f"""
        <tr>
            <td>{resource_name}</td>
            <td>{metric} ({unit})</td>
            <td>{quantity:.2f}</td>
            <td>${cost:.2f}</td>
            <td>{discounts}</td>
        </tr>
        """

html_content += """
    </table><br>"""


html_content += """
    <p>Regards,</p>
    <p><b>IBM Cloud Cost Monitoring System</b></p>
</body>
</html>
"""

# Save HTML file
with open("consolidated_report.html", "w") as output_file:
    output_file.write(html_content)

print("✅ HTML report generated successfully!")
send_email_via_sendgrid(f"IBM Cloud Cost Report - {month}", html_content)
