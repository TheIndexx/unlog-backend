import csv
import requests
import os
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(filename='script.log', level=logging.INFO)

# Set API Key
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Helper function to call Anthropic API
def call_anthropic_api(prompt):
    headers = {
        'anthropic-version': '2023-06-01',
        'x-api-key': ANTHROPIC_API_KEY,
        'content-type': 'application/json'
    }

    data = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 300,
        "temperature": 0.0,
        "messages": [{"role": "user", "content": prompt}]
    }

    if 1:
        response = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=data)
        result = response.json()
        print(result['content'][0]['text'])
        quit()
        return json.loads(result['content'][0]['text'])
   

# Task functions
def compute_subscription_longevity(subscription_date):
    try:
        subscription_date = datetime.strptime(subscription_date, '%Y-%m-%d')
        today = datetime.now()
        return (today - subscription_date).days // 365
    except Exception as e:
        logging.error(f"Error in computing subscription longevity: {e}")
        return 0

def analyze_contact_information(row):
    contact_points = 0
    try:
        if row['Phone1']:
            contact_points += 1
        if row['Phone2']:
            contact_points += 1
        if row['Email']:
            contact_points += 1
    except Exception as e:
        logging.error(f"Error analyzing contact info: {e}")
    return contact_points

def assess_geographic_influence(country):
    # Mockup example, as priority countries need to be pre-defined or dynamically queried
    preferred_countries = ["United States of America", "Canada", "United Kingdom"]
    return country in preferred_countries

def evaluate_company_prestige(company_name):
    prompt = f"Assess prestige for company: {company_name}"
    response = call_anthropic_api(prompt)
    if response:
        return response.get('prestige_score', 0)
    else:
        return 0

# Load data and process each entry
def main():
    results = []
    if 1:
        with open('input.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                subscription_years = compute_subscription_longevity(row['SubscriptionDate'])
                contact_info_completeness = analyze_contact_information(row)
                geographic_priority = assess_geographic_influence(row['Country'])
                company_prestige_score = evaluate_company_prestige(row['Company'])

                result = {
                    "CustomerId": row['CustomerId'],
                    "SubscriptionLongevity": subscription_years,
                    "ContactInfoCompleteness": contact_info_completeness,
                    "GeographicPriority": geographic_priority,
                    "CompanyPrestigeScore": company_prestige_score
                }
                results.append(result)

                logging.info(f"Processed CustomerId: {row['CustomerId']} with results: {result}")
    
    # Generate report
    generate_report(results)

def generate_report(results):
    try:
        with open('report.md', 'w') as report:
            report.write("# Customer Analysis Report\n\n")
            report.write("## Executive Summary\n")
            report.write("This report provides an analysis of customers based on subscription longevity, contact information completeness, geographic preference, and company prestige.\n\n")

            report.write("## Data Analysis\n")
            for result in results:
                report.write(f"- **CustomerId**: {result['CustomerId']}\n")
                report.write(f"  - Subscription Longevity: {result['SubscriptionLongevity']} years\n")
                report.write(f"  - Contact Information Completeness: {result['ContactInfoCompleteness']} methods\n")
                report.write(f"  - Geographic Priority: {'Yes' if result['GeographicPriority'] else 'No'}\n")
                report.write(f"  - Company Prestige Score: {result['CompanyPrestigeScore']}\n\n")

            report.write("## Key Findings\n")
            report.write("Top customers are those with high subscription longevity, complete contact information, geographic preference, and higher company prestige scores.\n\n")

            report.write("## Confidence Level Key\n")
            report.write("- High: Deterministic calculation (longevity, completeness)\n")
            report.write("- Medium/Low: LLM based or assumed (geographic influence, prestige)\n\n")

            report.write("## Final Analysis\n")
            report.write("The analysis indicates potential 'best' customers based on set criteria. This can guide business strategies for customer engagement.\n\n")
    except Exception as e:
        logging.error(f"Error generating report: {e}")

# Execute the script
main()