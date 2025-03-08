import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
# Get current month and year in YYYY-MM format
current_month = datetime.now().strftime("%Y-%m")
load_dotenv("./auth.env")
# IBM Cloud API Endpoints
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
RESOURCE_GROUPS_URL = f"https://resource-controller.cloud.ibm.com/v2/resource_groups"

IBM_CLOUD_API_KEY=os.getenv("IBM_CLOUD_API_KEY")
ACCOUNT_ID=os.getenv("ACCOUNT_ID")

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
        print(f"Error fetching IAM token: {response.status_code}")
        print(response.text)
        print("=====FAIL: Exiting Token generation phase=======")
        return None

# Function to get resource groups
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
        print("=====PASS: Exiting Resource Groups Fetch Phase=======")
        return response.json().get("resources", [])
    else:
        print(f"Error fetching resource groups: {response.status_code}")
        print(response.text)
        print("=====FAIL: Exiting Resource Groups Fetch Phase=======")
        return None

# Function to get resource group usage
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
        print(f"=====PASS: Exiting Resource Group Usage Fetch Phase for {resource_group_id}=======")
        return response.json()
    else:
        print(f"Error fetching resource group usage: {response.status_code}")
        print(response.text)
        print(f"=====FAIL: Exiting Resource Group Usage Fetch Phase for {resource_group_id}=======")
        return None


# Main execution
def generate_resource_group_report():
    # Get all resource groups
    resource_groups = get_resource_groups()
    if not resource_groups:
        print("❌ Failed to retrieve resource groups.")
        return

    # Start HTML content
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; color: #333; }
            h1 { color: #007BFF; }
            h2 { color: #34eb49; }
            h3 { color: #007BFF; margin-top: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #007BFF; color: white; }
            .summary { background-color: #f2f2f2; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .resource-group { border-left: 5px solid #007BFF; padding-left: 15px; margin-top: 30px; }
            .total-row { font-weight: bold; background-color: #e6f2ff; }
        </style>
    </head>
    <body>
        <h1>IBM Cloud Resource Group Usage Report - """ + current_month + """</h1>
    """

    # Track totals across all resource groups
    total_billable_cost = 0
    total_non_billable_cost = 0
    resource_groups_with_data = 0
    
    # Process each resource group
    for group in resource_groups:
        resource_group_id = group.get("id")
        resource_group_name = group.get("name", "Unnamed Group")
        
        # Get usage data for this resource group
        usage_data = get_resource_group_usage(resource_group_id)
        if not usage_data or "resources" not in usage_data:
            print(f"No usage data available for resource group: {resource_group_name}")
            continue
            
        resource_groups_with_data += 1
        
        # Add resource group section
        html_content += f"""
        <div class="resource-group">
            <h2>Resource Group: {resource_group_name}</h2>
            <p><strong>Resource Group ID:</strong> {resource_group_id}</p>
            <p><strong>Pricing Country:</strong> {usage_data.get('pricing_country', 'N/A')}</p>
            <p><strong>Currency:</strong> {usage_data.get('currency_code', 'USD')}</p>
        """
        
        # Resource section
        html_content += """
            <h3>Resources Cost Breakdown</h3>
            <table>
                <tr>
                    <th>Resource ID</th>
                    <th>Resource Name</th>
                    <th>Billable Cost</th>
                    <th>Billable Rated Cost</th>
                    <th>Non-Billable Cost</th>
                    <th>Non-Billable Rated Cost</th>
                </tr>
        """
        
        # Process each resource
        group_billable_cost = 0
        group_non_billable_cost = 0
        group_billable_rated_cost = 0
        group_non_billable_rated_cost = 0
        
        for resource in usage_data.get("resources", []):
            resource_id = resource.get("resource_id", "N/A")
            resource_name = resource.get("resource_name", resource_id)
            billable_cost = resource.get("billable_cost", 0)
            billable_rated_cost = resource.get("billable_rated_cost", 0)
            non_billable_cost = resource.get("non_billable_cost", 0)
            non_billable_rated_cost = resource.get("non_billable_rated_cost", 0)
            
            # Update totals
            group_billable_cost += billable_cost
            group_non_billable_cost += non_billable_cost
            group_billable_rated_cost +=billable_rated_cost
            group_non_billable_rated_cost += non_billable_rated_cost
            
            html_content += f"""
                <tr>
                    <td>{resource_id}</td>
                    <td>{resource_name}</td>
                    <td>${billable_cost:.2f}</td>
                    <td>${billable_rated_cost:.2f}</td>
                    <td>${non_billable_cost:.2f}</td>
                    <td>${non_billable_rated_cost:.2f}</td>
                </tr>
            """
        
        # Add group total
        html_content += f"""
                <tr class="total-row">
                    <td colspan="2">Group Total</td>
                    <td>${group_billable_cost:.2f}</td>
                    <td>${group_billable_rated_cost: .2f}</td>
                    <td>${group_non_billable_cost:.2f}</td>
                    <td>${group_non_billable_rated_cost}</td>
                </tr>
            </table>
        """
        
        # Update global totals
        total_billable_cost += group_billable_cost
        total_non_billable_cost += group_non_billable_cost
        
        # Plan section for the most important resources
        html_content += """
            <h3>Plan Details</h3>
            <table>
                <tr>
                    <th>Resource</th>
                    <th>Plan ID</th>
                    <th>Plan Name</th>
                    <th>Cost</th>
                    <th>Rated Cost</th>
                    <th>Billable</th>
                </tr>
        """
        
        for resource in usage_data.get("resources", []):
            resource_id = resource.get("resource_id", "N/A")
            resource_name = resource.get("resource_name", resource_id)
            
            for plan in resource.get("plans", []):
                plan_id = plan.get("plan_id", "N/A")
                plan_name = plan.get("plan_name", plan_id)
                cost = plan.get("cost", 0)
                rated_cost = plan.get("rated_cost", 0)
                billable = "Yes" if plan.get("billable", False) else "No"
                
                html_content += f"""
                    <tr>
                        <td>{resource_name}</td>
                        <td>{plan_id}</td>
                        <td>{plan_name}</td>
                        <td>${cost:.2f}</td>
                        <td>${rated_cost:.2f}</td>
                        <td>{billable}</td>
                    </tr>
                """
        
        html_content += """
            </table>
        """
        
        # Usage metrics for the most significant plans
        html_content += """
            <h3>Usage Metrics</h3>
            <table>
                <tr>
                    <th>Resource</th>
                    <th>Plan</th>
                    <th>Metric</th>
                    <th>Metric Name</th>
                    <th>Quantity</th>
                    <th>Unit</th>
                    <th>Cost</th>
                </tr>
        """
        
        for resource in usage_data.get("resources", []):
            resource_name = resource.get("resource_name", resource.get("resource_id", "N/A"))
            
            for plan in resource.get("plans", []):
                plan_name = plan.get("plan_name", plan.get("plan_id", "N/A"))
                
                for usage in plan.get("usage", []):
                    metric = usage.get("metric", "N/A")
                    metric_name = usage.get("metric_name", metric)
                    quantity = usage.get("quantity", 0)
                    unit = usage.get("unit", "N/A")
                    cost = usage.get("cost", 0)
                    
                    html_content += f"""
                        <tr>
                            <td>{resource_name}</td>
                            <td>{plan_name}</td>
                            <td>{metric}</td>
                            <td>{metric_name}</td>
                            <td>{quantity:.4f}</td>
                            <td>{unit}</td>
                            <td>${cost:.2f}</td>
                        </tr>
                    """
        
        html_content += """
            </table>
        """
        
        # Discounts section if applicable
        all_discounts = []
        for resource in usage_data.get("resources", []):
            all_discounts.extend(resource.get("discounts", []))
            
            for plan in resource.get("plans", []):
                all_discounts.extend(plan.get("discounts", []))
                
                for usage in plan.get("usage", []):
                    all_discounts.extend(usage.get("discounts", []))
        
        if all_discounts:
            html_content += """
                <h3>Applied Discounts</h3>
                <table>
                    <tr>
                        <th>Discount Name</th>
                        <th>Discount Reference</th>
                        <th>Discount Percentage</th>
                    </tr>
            """
            
            # Use a set to track unique discounts by reference
            processed_discounts = set()
            
            for discount in all_discounts:
                ref = discount.get("ref", "N/A")
                
                # Skip if we've already processed this discount
                if ref in processed_discounts:
                    continue
                    
                processed_discounts.add(ref)
                
                name = discount.get("display_name", discount.get("name", "Unknown Discount"))
                percentage = discount.get("discount", 0)
                
                html_content += f"""
                    <tr>
                        <td>{name}</td>
                        <td>{ref}</td>
                        <td>{percentage}%</td>
                    </tr>
                """
            
            html_content += """
                </table>
            """
            
        html_content += """
        </div>
        """
    
    # Add summary section at the top
    summary_html = f"""
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Reporting Period:</strong> {current_month}</p>
            <p><strong>Total Resource Groups with Usage:</strong> {resource_groups_with_data}</p>
            <p><strong>Total Billable Cost:</strong> ${total_billable_cost:.2f}</p>
            <p><strong>Total Non-Billable Cost:</strong> ${total_non_billable_cost:.2f}</p>
            <p><strong>Total Cost:</strong> ${(total_billable_cost + total_non_billable_cost):.2f}</p>
        </div>
    """
    
    html_content = html_content.replace("<h1>", summary_html + "<h1>")
    
    # Close HTML
    html_content += """
        <p>Regards,</p>
        <p><b>IBM Cloud Resource Group Cost Monitoring System</b></p>
    </body>
    </html>
    """
    
    # Save HTML file
    with open("cost_report.html", "w") as output_file:
        output_file.write(html_content)

generate_resource_group_report()
